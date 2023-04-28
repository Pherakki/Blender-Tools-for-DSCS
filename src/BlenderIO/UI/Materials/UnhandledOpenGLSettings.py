import bpy

from ...IOHelpersLib.UI import UIListBase

class OBJECT_UL_DSCSOpenGLUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.split(factor=0.05)
        split.separator()
        split.prop(item, "index", min=0, max=255)
        split.prop(item, "data")


_base_class = UIListBase(
    "import_dscs", 
    "UnhandledSettings", 
    OBJECT_UL_DSCSOpenGLUIList, 
    "unhandled_settings", 
    "active_unhandled_setting_idx", 
    lambda x: x.material.DSCS_MaterialProperties
)


class OBJECT_PT_DSCSMaterialUnhandledSettingsPanel(_base_class):
    bl_label       = ""
    bl_parent_id   = "OBJECT_PT_DSCSMaterialPanel"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "material"

    @classmethod
    def poll(self, context):
        return context.material is not None
    
    def draw_header(self, context):
        props = context.material.DSCS_MaterialProperties
        layout = self.layout
        
        layout.label(text=f"Extra Settings [{len(props.unhandled_settings)}]")
