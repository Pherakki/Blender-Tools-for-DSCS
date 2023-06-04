import array
import numpy as np

#############
# INTERFACE #
#############

def bpy_mesh_to_VAO_IBO(bpy_mesh, get_vertex_data, loop_data, make_vertex):
    # Get vertex -> loop and loop -> face maps
    vidx_to_lidx_map = generate_vertex_to_loops_map(bpy_mesh)
    lidx_to_fidx_map = generate_loop_to_face_map(bpy_mesh)
    
    # Make loop -> unique value lookup maps
    # This should just be a splat of all vertex attributes
    # normals, UVs, colours, tangents, binormals
    loop_idx_to_key        = [key for key in (zip(*loop_data))]
    unique_val_map         = {key: i for i, key in enumerate(list(set(loop_idx_to_key)))}
    loop_idx_to_unique_key = {i: unique_val_map[key] for i, key in enumerate(loop_idx_to_key)}
    
    exported_vertices = []
    faces = [{l: bpy_mesh.loops[l].vertex_index for l in f.loop_indices} for f in bpy_mesh.polygons]
    vao_vert_to_bpy_vert = {}
    for vert_idx, linked_loops in vidx_to_lidx_map.items():
        vertex = bpy_mesh.vertices[vert_idx]
        unique_ids = {i: [] for i in list(set(loop_idx_to_unique_key[ll] for ll in linked_loops))}
        for ll in linked_loops:
            unique_ids[loop_idx_to_unique_key[ll]].append(ll)
        unique_values = [(loop_idx_to_key[lids[0]], lids) for id_, lids in unique_ids.items()]
        
        vertex_data = get_vertex_data(vert_idx, vertex)
        
        # Now split the verts by their loop data
        for unique_value, loops_with_this_value in unique_values:
            # Create the VAO entry
            vb = make_vertex(vertex_data, unique_value)

            # Update the vao -> bpy map
            n_verts = len(exported_vertices)
            vao_vert_to_bpy_vert[len(exported_vertices)] = vert_idx
            exported_vertices.append(vb)

            # Update the polygon map
            for l in loops_with_this_value:
                face_idx = lidx_to_fidx_map[l]
                faces[face_idx][l] = n_verts

    # Create IBO from faces
    faces = [list(face_verts.values()) for face_verts in faces]

    return exported_vertices, faces, vao_vert_to_bpy_vert


def get_normals(bpy_mesh_obj, use_normals, sigfigs, transform=lambda x, l: x):
    mesh = bpy_mesh_obj.data
    nloops = len(mesh.loops)
    if use_normals:
        data  = fetch_data(mesh.loops, "normal", sigfigs)
        loops = mesh.loops
        return [transform(d, l) for d, l in zip(data, loops)]
    else:
        return empty_attr(nloops)


def get_tangents(bpy_mesh_obj, use_tangents, sigfigs, transform=lambda x, l: x):
    mesh = bpy_mesh_obj.data
    nloops = len(mesh.loops)
    if use_tangents:
        data  = fetch_data(mesh.loops, "tangent", sigfigs)
        loops = mesh.loops
        return [transform(d, l) for d, l in zip(data, loops)]
    else:
        return empty_attr(nloops)


def get_binormals(bpy_mesh_obj, use_binormals, sigfigs, transform=lambda x, l: x):
    mesh = bpy_mesh_obj.data
    nloops = len(mesh.loops)
    if use_binormals:
        data  = [(round_to_sigfigs(l.bitangent_sign * np.cross(l.normal, l.tangent), sigfigs)) for l in mesh.loops]
        loops = mesh.loops
        return [transform(d, l) for d, l in zip(data, loops)]
    else:
        return empty_attr(nloops)


def get_uvs(bpy_mesh_obj, use_uv, map_name, sigfigs, errorlog=None, transform=lambda x, l: x):
    mesh = bpy_mesh_obj.data
    nloops = len(mesh.loops)
    if use_uv:
        if map_name in mesh.uv_layers:
            data  = fetch_data(mesh.uv_layers[map_name].data, "uv", sigfigs)
            loops = mesh.loops
            return [transform(d, l) for d, l in zip(data, loops)]
        else:
            if errorlog is not None:
                errorlog.log_warning_message(f"Unable to locate UV Map '{map_name}' on mesh '{bpy_mesh_obj.name}'; exporting a fallback blank map")
            return make_blank(nloops, 2)
    else:
        return empty_attr(nloops)


def get_colors(bpy_mesh_obj, use_colors, map_name, data_format, errorlog=None, transform=lambda x: x):
    nloops = len(bpy_mesh_obj.data.loops)
    if data_format not in ("BYTE", "FLOAT"):
        raise NotImplementedError("Invalid data format provided to 'get_colors'. Options are 'BYTE' or 'FLOAT'.")
    if use_colors:
        ################
        # EXTRACT DATA #
        ################
        dtype = "BYTE_COLOR"
        # Blender 3.2+ 
        # vertex_colors is equivalent to color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER").
        if hasattr(bpy_mesh_obj, "color_attributes"):
            if map_name not in bpy_mesh_obj.color_attributes:
                if errorlog is not None:
                    errorlog.log_warning_message(f"Unable to locate color map '{map_name}' on mesh '{bpy_mesh_obj.name}'; exporting a fallback blank map")
                data = make_blank_color(nloops) 
            else:
                ca = bpy_mesh_obj.color_attributes[map_name]
                dtype = ca.data_type
                if ca.domain == "CORNER":
                    data = (c.color for c in ca.data)
                elif ca.domain == "POINT":
                    # Copy vertex data to loop data
                    data = (ca.data[loop.vertex_index].color for loop in bpy_mesh_obj.data.loops)
                else:
                    if errorlog is not None:
                        errorlog.log_warning_message(f"Unable to extract data from unknown color map domain '{ca.domain}'; exporting a fallback blank map")
                    data = make_blank_color(nloops)
        # Blender 2.81-3.2
        else:
            if map_name not in bpy_mesh_obj.vertex_colors:
                if errorlog is not None:
                    errorlog.log_warning_message(f"Unable to locate color map '{map_name}' on mesh '{bpy_mesh_obj.name}' - exporting a fallback blank map")
                data = make_blank_color(nloops)
            else:
                vc = bpy_mesh_obj.vertex_colors[map_name]
                data = (l.color for l in vc.data)
                
        #############################################
        # Convert to the requested output data type #
        #############################################
        if dtype == "BYTE_COLOR" and data_format == "BYTE":
            return [transform(d) for d in data]
        elif dtype == "BYTE_COLOR" and data_format == "FLOAT":
            return [transform([e/255. for e in d]) for d in data]
        elif dtype == "FLOAT_COLOR" and data_format == "BYTE":
            return [transform([min(1, max(0, int(e*255))) for e in d]) for d in data]
        elif dtype == "FLOAT_COLOR" and data_format == "FLOAT":
            return [transform(d) for d in data]
        else:
            raise NotImplementedError("Unhandled data type combination '{dtype}' and '{data_format}'")
        
    else:
        return empty_attr(nloops)

##################
# IMPLEMENTATION #
##################

def generate_vertex_to_loops_map(mesh):
    vidx_to_lidxs = {}
    for loop in mesh.loops:
        if loop.vertex_index not in vidx_to_lidxs:
            vidx_to_lidxs[loop.vertex_index] = []
        vidx_to_lidxs[loop.vertex_index].append(loop.index)
    return vidx_to_lidxs


def generate_loop_to_face_map(mesh):
    lidx_to_fidx = {}
    for face in mesh.polygons:
        for loop_idx in face.loop_indices:
            lidx_to_fidx[loop_idx] = face.index
    return lidx_to_fidx


def fetch_data(obj, element, sigfigs):
    dsize = len(getattr(obj[0], element))
    data = array.array('f', [0.0] * (len(obj) * dsize))
    obj.foreach_get(element, data)
    return [tuple(round_to_sigfigs(datum, sigfigs)) for datum in zip(*(iter(data),) * dsize)]


def empty_attr(size):
    return (None for _ in range(size))


def make_blank(count, shape):
    elem = tuple([0.0 for _ in range(shape)])
    return [elem for _ in range(count)]


def make_blank_color(count):
    elem = tuple([1.0, 1.0, 1.0, 1.0])
    return [elem for _ in range(count)]


def round_to_sigfigs(x, p):
    """
    Credit to Scott Gigante
    Taken from https://stackoverflow.com/a/59888924
    Rounds a float x to p significant figures
    """
    x = np.asarray(x)
    x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10**(p-1))
    mags = 10 ** (p - 1 - np.floor(np.log10(x_positive)))
    return np.round(x * mags) / mags
