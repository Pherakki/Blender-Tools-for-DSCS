import bpy
from mathutils import Vector, Matrix
import array

import numpy as np


def set_mesh_vertex_attribute_labels(vert, mesh):
    attributes = set(list(vert.keys()))
    mesh['export_normals'] = 'Normal' in attributes
    mesh['export_tangents'] = 'Tangent' in attributes
    mesh['export_binormals'] = 'Binormal' in attributes


def import_meshes(parent_obj, filename, model_data, armature_name):
    for i, IF_mesh in enumerate(model_data.meshes):
        faces = [poly.indices for poly in IF_mesh.polygons]

        new_verts, new_tris, new_facevert_to_old_facevert_map = merge_opengl_vertices(IF_mesh.vertices, faces)
        vert_positions = [np.array(v.position) for v in new_verts]

        # Init mesh
        meshobj_name = f"{filename}_{i}"
        mesh = bpy.data.meshes.new(name=meshobj_name)
        mesh_object = bpy.data.objects.new(meshobj_name, mesh)

        mesh_object.data.from_pydata(vert_positions, [], new_tris)
        bpy.context.collection.objects.link(mesh_object)

        # Get the loop data
        n_loops = len(mesh.loops)
        map_of_loops_to_model_verts = {}
        map_of_model_verts_to_blender_verts = {}
        for new_poly_idx, poly in enumerate(mesh.polygons):
            for loop_idx in poly.loop_indices:
                assert loop_idx not in map_of_loops_to_model_verts, "Loop already exists!"
                new_vert_idx = mesh.loops[loop_idx].vertex_index
                # Take only the vert id from the old (face_id, vert_id) pair
                old_vert_idx = new_facevert_to_old_facevert_map[(new_poly_idx, new_vert_idx)][1]
                map_of_loops_to_model_verts[loop_idx] = old_vert_idx
                map_of_model_verts_to_blender_verts[old_vert_idx] = new_vert_idx

        loop_data = [IF_mesh.vertices[map_of_loops_to_model_verts[loop_idx]] for loop_idx in range(n_loops)]

        # Assign normals
        # Works thanks to this stackexchange answer https://blender.stackexchange.com/a/75957
        # which a few of these comments below are also taken from
        if 'Normal' in IF_mesh.vertices[0]:
            mesh.create_normals_split()
            for face in mesh.polygons:
                face.use_smooth = True  # loop normals have effect only if smooth shading ?

            # Set loop normals
            loop_normals = [Vector(l["Normal"]) for l in loop_data]
            mesh.loops.foreach_set("normal", [subitem for item in loop_normals for subitem in item])

            mesh.validate(clean_customdata=False)  # important to not remove loop normals here!
            mesh.update()

            clnors = array.array('f', [0.0] * (len(mesh.loops) * 3))
            mesh.loops.foreach_get("normal", clnors)

            mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
            mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
            # mesh.normals_split_custom_set(loop_normals)
            mesh.use_auto_smooth = True

        # Assign materials
        material_name = model_data.materials[IF_mesh.material_id].name
        active_material = bpy.data.materials[material_name]
        bpy.data.objects[meshobj_name].active_material = active_material

        # Assign UVs
        for uv_type in ['UV', 'UV2', 'UV3']:
            if uv_type in IF_mesh.vertices[0]:
                uv_layer = mesh.uv_layers.new(name=f"{uv_type}Map", do_init=True)
                for loop_idx, loop in enumerate(mesh.loops):
                    uv_layer.data[loop_idx].uv = loop_data[loop_idx][uv_type]

        # Assign vertex colours
        if 'Colour' in IF_mesh.vertices[0]:
            colour_map = mesh.vertex_colors.new(name=f"Map", do_init=True)
            for loop_idx, loop in enumerate(mesh.loops):
                colour_map.data[loop_idx].color = loop_data[loop_idx]['Colour']

        # Rig the vertices
        vertex_groups = make_vertex_groups(new_verts, [vg.bone_idx for vg in IF_mesh.vertex_groups])
        for bone_idx, vg in vertex_groups.items():
            vertex_group = mesh_object.vertex_groups.new(name=model_data.skeleton.bone_names[bone_idx])
            for vert_idx, vert_weight in vg:
                vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        # Add unknown data
        mesh_object['name_hash'] = IF_mesh.name_hash

        mesh_object.parent = bpy.data.objects[armature_name]
        modifier = mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = bpy.data.objects[armature_name]

        mesh.validate(verbose=True, clean_customdata=False)
        set_mesh_vertex_attribute_labels(IF_mesh.vertices[0], mesh_object)
        mesh.update()

    # Top-level unknown data
    parent_obj['unknown_footer_data'] = model_data.unknown_data['unknown_footer_data']


class LoopCandidate:
    def __init__(self, vertex_id, face_id, face_normal, face_centre, data):
        self.vert_id = vertex_id
        self.face_id = face_id
        self.face_normal = face_normal
        self.face_centre = face_centre
        self.data = data


class BlenderVertexInfo:
    def __init__(self, position, indices, weights):
        self.position = position
        self.indices = indices
        self.weights = weights


def merge_opengl_vertices(vertices, triangles):
    """
    Given a list of input vertices and polygons, merge vertices with the same position attribute with face normals
    within 90 degrees of the normal of the best-fitting plane of the centres of all faces associated with that position.
    This process will cause any loose vertices in the input collection to be lost on output.
    Outputs:
    a list of objects containing positions, bone indices, and bone weights to be turned into Blender vertices,
    a list of triangles mapped to the new vertices,
    a map of (new_face_idx, new_vert_idx) to (old_face_idx, old_vert_idx)
    """
    # First get all vertex-face pairs
    # We plan to merge some of these into Blender vertices (i.e. collections of OpenGL vertices with the same position)
    # However, we need to ensure that e.g. vertices making up faces with opposite normals don't get merged unless they
    # form a boundary of the polygon
    # So in this process, we'll also calculate the face normals and centres
    # NOTE: THIS WILL DROP ANY LOOSE VERTICES!!!
    loop_candidates = []
    for triangle_idx, triangle in enumerate(triangles):
        vert_positions = [vertices[vert_idx]['Position'] for vert_idx in triangle]
        edge_1 = vert_positions[1] - vert_positions[0]
        edge_2 = vert_positions[2] - vert_positions[1]
        face_normal = np.cross(edge_1, edge_2)
        face_centre = np.mean(vert_positions, axis=0)
        for vert_idx in triangle:
            loop_candidates.append(LoopCandidate(vert_idx, triangle_idx, face_normal, face_centre, vertices[vert_idx]))
    # Now, loop over the loop candidates and collect them by position
    # We'll split these collections by face normals after the collections have been populated
    # Can this list be 'consumed' element-by-element by popping elements off the front to waste less memory?
    grouped_loop_candidates = {}
    for loop_candidate in loop_candidates:
        pos = tuple(loop_candidate.data['Position'])
        if pos not in grouped_loop_candidates:
            grouped_loop_candidates[pos] = []
        grouped_loop_candidates[pos].append(loop_candidate)

    # Now build the final list of unique loops going into each vertex - these will form the basis of the Blender loops
    new_vertices = []
    old_facevert_to_new_vert = {}
    for position, candidate_group in grouped_loop_candidates.items():
        start_idx = len(new_vertices)
        group_1 = []
        group_2 = []
        all_centres = np.array([candidate_loop.face_centre for candidate_loop in candidate_group])
        # Now find the plane closest to all the face centres
        # We'll store this as the associated covector; i.e. the plane normal
        plane_basis = np.linalg.svd((all_centres - np.mean(all_centres, axis=0)).T)[0]
        covector = plane_basis[:, -1]
        # This covector defines a plane of separation we can use to split the candidate loops into two groups: aligned
        # with and anti-aligned with the plane of separation normal
        # Basically, if we have two surfaces directly on top of each other but with opposite normals,
        # this technique will allow us to separate which loop candidates should go into the "upper" surface and which
        # should go into the "lower" surface
        for old_facevertex in candidate_group:
            test_normal = old_facevertex.face_normal
            (group_1 if np.dot(covector, test_normal) >= 0 else group_2).append(old_facevertex)

        # Ensure that group 1 will always have at least one element in it
        if len(group_2) > len(group_1):
            group_1, group_2 = group_2, group_1
        # Assume that all loops are weighted the same - no support for non-manifold data yet
        new_vertices.append(BlenderVertexInfo(position, group_1[0].data["WeightedBoneID"], group_1[0].data["BoneWeight"]))
        for old_facevert in group_1:
            old_facevert_to_new_vert[(old_facevert.face_id, old_facevert.vert_id)] = start_idx
        if len(group_2):
            new_vertices.append(BlenderVertexInfo(position, group_2[0].data["WeightedBoneID"], group_2[0].data["BoneWeight"]))
            for old_facevert in group_2:
                old_facevert_to_new_vert[(old_facevert.face_id, old_facevert.vert_id)] = start_idx + 1

    # Now we can generate some new triangles based on our merged vertices
    new_triangles = []
    new_facevert_to_old_facevert_map = {}
    for face_id, triangle in enumerate(triangles):
        new_triangle = []
        for vert_id in triangle:
            new_vert_id = old_facevert_to_new_vert[(face_id, vert_id)]
            new_triangle.append(new_vert_id)
            new_facevert_to_old_facevert_map[(face_id, new_vert_id)] = (face_id, vert_id)
        new_triangles.append(new_triangle)

    return new_vertices, new_triangles, new_facevert_to_old_facevert_map


def make_vertex_groups(blender_vert_infos, local_idx_to_bone_idx_map):
    groups = {}
    for vert_idx, vert in enumerate(blender_vert_infos):
        for group_idx, weight in zip(vert.indices, vert.weights):
            bone_idx = local_idx_to_bone_idx_map[group_idx]
            if weight == 0.:
                continue
            elif bone_idx not in groups:
                groups[bone_idx] = []
            groups[bone_idx].append((vert_idx, weight))
    return groups