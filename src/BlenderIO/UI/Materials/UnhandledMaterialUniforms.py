import bpy

from ...IOHelpersLib.UI import UIListBase


class OBJECT_UL_DSCSMaterialUniformUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.split(factor=0.05)
        split.prop(item, "enabled", text="")
        split = split.split(factor=0.25)
        split.enabled = item.enabled
        
        split.prop(item, "index")
        split.prop(item, "dtype")
        if item.dtype == "FLOAT32":
            split.prop(item, "float32_data")
        elif item.dtype == "FLOAT32VEC3":
            split.prop(item, "float32vec3_data")
        elif item.dtype == "FLOAT32VEC2":
            split.prop(item, "float32vec2_data")
        elif item.dtype == "FLOAT32VEC4":
            split.prop(item, "float32vec4_data")
        elif item.dtype == "TEXTURE":
            col = split.column()
            col.prop(item.texture_data, "image", text="")
            col.prop(item.texture_data, "data", text="")


_base_class = UIListBase(
    "import_dscs", 
    "UnhandledUniforms", 
    OBJECT_UL_DSCSMaterialUniformUIList, 
    "unhandled_uniforms", 
    "active_unhandled_uniform_idx", 
    lambda x: x.material.DSCS_MaterialProperties
)


class OBJECT_PT_DSCSMaterialUnhandledUniformsPanel(_base_class):
    bl_label       = ""
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "material"

    @classmethod
    def poll(self, context):
        return context.material is not None
    
    def draw_header(self, context):
        props = context.material.DSCS_MaterialProperties
        layout = self.layout
        
        layout.label(text=f"Extra Uniforms [{len(props.unhandled_uniforms)}]")
