import bpy


class OBJECT_PT_DSCSLightPanel(bpy.types.Panel):
    bl_label       = "DSCS Light"
    bl_idname      = "OBJECT_PT_DSCSLightPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.light is not None

    def draw(self, context):
        light = context.light
        layout = self.layout
        props = light.DSCS_LightProperties
        
        if context.active_object.parent_bone == "":
            layout.prop(props, "bone_hash")
        
        layout.prop(props, "mode")
        layout.prop(props, "light_id")
        layout.prop(props, "intensity")
        layout.prop(props, "fog_height")
        layout.prop(props, "alpha")
        layout.prop(props, "unknown_0x20")
        layout.prop(props, "unknown_0x24")
        layout.prop(props, "unknown_0x28")
        layout.prop(props, "unknown_0x2C")
