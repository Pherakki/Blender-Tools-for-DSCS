import bpy
from mathutils import Vector, Matrix


def import_meshes(parent_obj, filename, model_data, armature_name):
    for i, IF_mesh in enumerate(model_data.meshes):
        # This function should be the best way to remove duplicate vertices (?) but doesn't pick up overlapping polygons with opposite normals
        # verts, faces, map_of_loops_to_model_vertices, map_of_model_verts_to_verts = self.build_loops_and_verts(IF_mesh.vertices, IF_mesh.polygons)
        # verts = [Vector(vert) for vert in verts]
        edges = []

        # Init mesh
        meshobj_name = f"{filename}_{i}"
        mesh = bpy.data.meshes.new(name=meshobj_name)
        mesh_object = bpy.data.objects.new(meshobj_name, mesh)

        verts = [Vector(v['Position']) for v in IF_mesh.vertices]
        faces = [poly.indices for poly in IF_mesh.polygons]
        mesh_object.data.from_pydata(verts, edges, faces)
        bpy.context.collection.objects.link(mesh_object)

        # Get the loop data
        # map_of_blenderloops_to_modelloops = {}
        # for poly_idx, poly in enumerate(mesh.polygons):
        #     for loop_idx in poly.loop_indices:
        #         vert_idx = mesh.loops[loop_idx].vertex_index
        #         model_vertex = map_of_loops_to_model_vertices[(poly_idx, vert_idx)]
        #         map_of_blenderloops_to_modelloops[loop_idx] = IF_mesh.vertices[model_vertex]

        # Assign normals
        # if 'Normal' in map_of_blenderloops_to_modelloops[0]:
        if 'Normal' in IF_mesh.vertices[0]:
            # loop_normals = [Vector(loop_data['Normal']) for loop_data in map_of_blenderloops_to_modelloops.values()]
            # loop_normals = [Vector(IF_mesh.vertices[loop.vertex_index]['Normal']) for loop in mesh_object.data.loops]
            # mesh_object.data.normals_split_custom_set([(0, 0, 0) for _ in mesh_object.data.loops])
            # mesh_object.data.normals_split_custom_set(loop_normals)
            mesh_object.data.normals_split_custom_set_from_vertices([Vector(v['Normal']) for v in IF_mesh.vertices])

        mesh.use_auto_smooth = True

        # Assign materials
        material_name = model_data.materials[IF_mesh.material_id].name
        active_material = bpy.data.materials[material_name]
        bpy.data.objects[meshobj_name].active_material = active_material

        # Assign UVs
        for uv_type in ['UV', 'UV2', 'UV3']:
            # if uv_type in map_of_blenderloops_to_modelloops[0]:
            if uv_type in IF_mesh.vertices[0]:
                uv_layer = mesh.uv_layers.new(name=f"{uv_type}Map", do_init=True)
                for loop_idx, loop in enumerate(mesh.loops):
                    # uv_layer.data[loop_idx].uv = map_of_blenderloops_to_modelloops[loop_idx][uv_type]
                    uv_layer.data[loop_idx].uv = IF_mesh.vertices[loop.vertex_index][uv_type]

        # Assign vertex colours
        if 'Colour' in IF_mesh.vertices[0]:
            colour_map = mesh.vertex_colors.new(name=f"Map", do_init=True)
            for loop_idx, loop in enumerate(mesh.loops):
                colour_map.data[loop_idx].color = IF_mesh.vertices[loop.vertex_index]['Colour']

        # Rig the vertices
        for IF_vertex_group in IF_mesh.vertex_groups:
            vertex_group = mesh_object.vertex_groups.new(name=model_data.skeleton.bone_names[IF_vertex_group.bone_idx])
            for vert_idx, vert_weight in zip(IF_vertex_group.vertex_indices, IF_vertex_group.weights):
                # vertex_group.add([map_of_model_verts_to_verts[vert_idx]], vert_weight, 'REPLACE')
                vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        # Add unknown data
        mesh_object['unknown_0x31'] = IF_mesh.unknown_data['unknown_0x31']
        mesh_object['name_hash'] = IF_mesh.name_hash

        bpy.data.objects[meshobj_name].select_set(True)
        bpy.data.objects[armature_name].select_set(True)
        # I would prefer to do this by directly calling object methods if possible
        # mesh_object.parent_set()...
        bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
        bpy.ops.object.parent_set(type='ARMATURE')

        mesh.validate(verbose=True)
        mesh.update()

        bpy.data.objects[meshobj_name].select_set(False)
        bpy.data.objects[armature_name].select_set(False)

    # Top-level unknown data
    parent_obj['unknown_footer_data'] = model_data.unknown_data['unknown_footer_data']
