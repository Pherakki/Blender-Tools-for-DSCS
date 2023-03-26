import array
import math

import bpy
from mathutils import Vector, Quaternion

from ...Core.FileFormats.Geom.GeomBinary.MeshBinary.Base import PrimitiveTypes
from ...Core.FileFormats.Geom.Constants import AttributeTypes
from ..IOHelpersLib.Meshes import merge_vertices, import_loop_normals, create_uv_map
from ..IOHelpersLib.Context import safe_active_object_switch, set_active_obj, set_mode


@safe_active_object_switch
def import_meshes(model_name, ni, gi, armature, material_list, try_merge_vertices):
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
        new_verts, new_tris, new_facevert_to_old_facevert_map = merge_vertices(mesh.vertices, faces, try_merge_vertices)
        vert_positions = [Vector(v.position[:3]) for v in new_verts]

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
        
        set_active_obj(bpy_mesh_object)
        
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
                create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type][0], (l[uv_type][1]*-1) + 1) for l in loop_data))

        # Assign vertex colours
        if mesh.vertices[0][AttributeTypes.COLOR] is not None:
            colour_map = bpy_mesh.vertex_colors.new(name="Map", do_init=True)
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
        bpy_mesh_object.data.DSCS_MeshProperties.name_hash = hex(mesh.name_hash)

        # Set armature constraint
        bpy_mesh_object.parent = armature
        modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = armature

        # Assign normals
        # Do this LAST because it can remove some loops
        if mesh.vertices[0][AttributeTypes.NORMAL] is not None:
            import_loop_normals(bpy_mesh, (l.normal for l in loop_data))

        # Tell Blender what we've done
        bpy_mesh.validate(verbose=True, clean_customdata=False)
        bpy_mesh.update()
        bpy_mesh.update()

        # Convert meshes Y up -> Z up
        bpy_mesh.transform(Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4())

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
