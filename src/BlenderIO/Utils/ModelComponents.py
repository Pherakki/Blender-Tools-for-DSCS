def get_child_meshes(bpy_armature_obj):
    return [obj for obj in bpy_armature_obj.children if obj.type == "MESH"]


def get_used_materials(bpy_meshes):
    material_names = []
    for bpy_mesh_obj in bpy_meshes:
        if bpy_mesh_obj.active_material is not None:
            mat_name = bpy_mesh_obj.active_material.name
            if mat_name not in material_names:
                material_names.append(mat_name)
    return material_names


def get_child_materials(bpy_armature_obj):
    return get_used_materials(get_child_meshes(bpy_armature_obj))
