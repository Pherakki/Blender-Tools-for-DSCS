import array

import bpy
from mathutils import Vector

from ..Core.FileFormats.Geom.GeomBinary.MeshBinary.Base import PrimitiveTypes
from ..Core.FileFormats.Geom.Constants import AttributeTypes
from .VertexMerging import merge_opengl_vertices


def import_meshes(model_name, ni, gi, armature, material_list, merge_vertices):
    meshes = []
    for i, mesh in enumerate(gi.meshes):
        #################
        # PURE GEOMETRY #
        #################
        # First get the primitives
        if mesh.indices.primitive_type == PrimitiveTypes.TRIANGLES:
            faces = mesh.indices.unpack()
        elif mesh.indices.primitive_type == PrimitiveTypes.TRIANGLE_STRIP:
            faces = mesh.indices.to_triangles().unpack()
        else:
            raise Exception(f"Primitive Type '{mesh.indices.primitive_type}' not supported")

        # Now merge OpenGL vertices into Blender vertices
        new_verts, new_tris, new_facevert_to_old_facevert_map = merge_opengl_vertices(mesh.vertices, faces, merge_vertices)
        vert_positions = [Vector(v.position) for v in new_verts]

        ###############
        # CREATE MESH #
        ###############
        # Init mesh
        meshobj_name = f"{model_name}_{i}"
        bpy_mesh = bpy.data.meshes.new(name=meshobj_name)
        bpy_mesh_object = bpy.data.objects.new(meshobj_name, bpy_mesh)

        bpy_mesh_object.data.from_pydata(vert_positions, [], new_tris)
        bpy.context.collection.objects.link(bpy_mesh_object)

        # Assign materials
        active_material = material_list[mesh.material_id]
        bpy.data.objects[meshobj_name].active_material = active_material

        #################
        # ADD LOOP DATA #
        #################
        # Get the loop data
        n_loops = len(bpy_mesh.loops)
        map_of_loops_to_model_verts = {}
        for new_poly_idx, poly in enumerate(bpy_mesh.polygons):
            for loop_idx in poly.loop_indices:
                assert loop_idx not in map_of_loops_to_model_verts, "Loop already exists!"
                new_vert_idx = bpy_mesh.loops[loop_idx].vertex_index
                # Take only the vert id from the old (face_id, vert_id) pair
                old_vert_idx = new_facevert_to_old_facevert_map[(new_poly_idx, new_vert_idx)][1]
                map_of_loops_to_model_verts[loop_idx] = old_vert_idx

        loop_data = [mesh.vertices[map_of_loops_to_model_verts[loop_idx]] for loop_idx in range(n_loops)]

        # Assign UVs
        for uv_idx, uv_type in enumerate([AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3]):
            if mesh.vertices[0][uv_type] is not None:
                uv_layer = bpy_mesh.uv_layers.new(name=f"UVMap{uv_idx + 1}", do_init=True)
                for loop_idx, loop in enumerate(bpy_mesh.loops):
                    u, v = loop_data[loop_idx][uv_type]
                    uv_layer.data[loop_idx].uv = (u, (v*-1) + 1)

        # Assign vertex colours
        if mesh.vertices[0][AttributeTypes.COLOR] is not None:
            colour_map = bpy_mesh.vertex_colors.new(name=f"Map", do_init=True)
            for loop_idx, loop in enumerate(bpy_mesh.loops):
                colour_map.data[loop_idx].color = loop_data[loop_idx].color

        # Rig the vertices
        vertex_groups = make_vertex_groups(new_verts)
        for bone_idx, vg in vertex_groups.items():
            vertex_group = bpy_mesh_object.vertex_groups.new(name=ni.bone_names[bone_idx])
            for vert_idx, vert_weight in vg:
                vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        #################
        # ADD MISC DATA #
        #################
        # Load the hashed mesh name
        bpy_mesh_object['name_hash'] = hex(mesh.name_hash)

        # Set armature constraint
        bpy_mesh_object.parent = armature
        modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = armature

        # Assign normals
        # Works thanks to this stackexchange answer https://blender.stackexchange.com/a/75957
        # which a few of these comments below are also taken from
        # Do this LAST because it can remove some loops
        if mesh.vertices[0][AttributeTypes.NORMAL] is not None:
            bpy_mesh.create_normals_split()
            for face in bpy_mesh.polygons:
                face.use_smooth = True  # loop normals have effect only if smooth shading ?

            # Set loop normals
            loop_normals = [Vector(list(l.normal))for l in loop_data]
            bpy_mesh.loops.foreach_set("normal", [subitem for item in loop_normals for subitem in item])

            bpy_mesh.validate(clean_customdata=False)  # important to not remove loop normals here!
            bpy_mesh.update()

            clnors = array.array('f', [0.0] * (len(bpy_mesh.loops) * 3))
            bpy_mesh.loops.foreach_get("normal", clnors)

            bpy_mesh.polygons.foreach_set("use_smooth", [True] * len(bpy_mesh.polygons))
            # This line is pretty smart (came from the stackoverflow answer)
            # 1. Creates three copies of the same iterator over clnors
            # 2. Splats those three copies into a zip
            # 3. Each iteration of the zip now calls the iterator three times, meaning that three consecutive elements
            #    are popped off
            # 4. Turn that triplet into a tuple
            # In this way, a flat list is iterated over in triplets without wasting memory by copying the whole list
            bpy_mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))

            bpy_mesh.use_auto_smooth = True

        # Tell Blender what we've done
        bpy_mesh.validate(verbose=True, clean_customdata=False)
        bpy_mesh.update()

        meshes.append(bpy_mesh)


def make_vertex_groups(blender_vert_infos):
    groups = {}
    for vert_idx, vert in enumerate(blender_vert_infos):
        for bone_idx, weight in zip(vert.indices, vert.weights):
            if weight == 0.:
                continue
            elif bone_idx not in groups:
                groups[bone_idx] = []
            groups[bone_idx].append((vert_idx, weight))
    return groups
