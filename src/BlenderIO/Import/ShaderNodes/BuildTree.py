from .AdvancedMaterial import rebuild_advanced_tree


def rebuild_tree(bpy_material, used_images):
    props    = bpy_material.DSCS_MaterialProperties
    
    rebuild_advanced_tree(bpy_material, used_images)
