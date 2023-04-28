import bpy


class OBJECT_PT_DSCSBonePanel(bpy.types.Panel):
    bl_label       = "DSCS Bone"
    bl_idname      = "OBJECT_PT_DSCSBonePanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "bone"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.bone is not None

    def draw(self, context):
        bone = context.bone
        layout = self.layout
        props = bone.DSCS_BoneProperties
        
        layout.prop(props, "flag")
