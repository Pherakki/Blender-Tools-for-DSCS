import bpy


class OBJECT_PT_DSCSCameraPanel(bpy.types.Panel):
    bl_label       = "DSCS Camera"
    bl_idname      = "OBJECT_PT_DSCSBonePanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.camera is not None

    def draw(self, context):
        bone = context.camera
        layout = self.layout
        props = bone.DSCS_CameraProperties
        
        layout.prop(props, "aspect_ratio")
