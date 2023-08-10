from .AdvancedMaterial import rebuild_advanced_tree
from .ColliderMaterial import rebuild_collider_tree


def rebuild_tree(bpy_material, used_images):
    props    = bpy_material.DSCS_MaterialProperties
    if props.shader_name == "00000000_00000000_00000000_00000000":
        rebuild_collider_tree(bpy_material)
        return
    
    rebuild_advanced_tree(bpy_material, used_images)
