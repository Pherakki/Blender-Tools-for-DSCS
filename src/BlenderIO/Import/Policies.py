import bpy

from ....external.blunger.interface import ArgGroup


def ImportPoliciesTemplate(is_preferences):
    class ImportPoliciesImpl(ArgGroup):
        merge_vertices: bpy.props.BoolProperty(
            name="Merge Vertices",
            description="Default setting for 'Merge Vertices' on import"
            if is_preferences else
            "Merge the OpenGL vertices (which look like duplicates in Blender) to Blender vertices",
            default=True
        )
    
        import_anims: bpy.props.BoolProperty(
            name="Import Animations",
            description="Default setting for 'Import Animations' on import"
            if is_preferences else
            "Whether to import animations or not"
        )
    return ImportPoliciesImpl


ImportPoliciesPrefs = ImportPoliciesTemplate(True)
ImportPoliciesOp    = ImportPoliciesTemplate(False)
ImportPoliciesArgs  = ImportPoliciesOp.AnnotationGroup() 
ImportPoliciesGroup = ImportPoliciesOp.PropGroup()
