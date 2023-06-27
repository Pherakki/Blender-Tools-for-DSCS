import bpy
from ..IOHelpersLib.Objects import find_bpy_objects
from ..Utils.ModelComponents import get_child_materials


class OBJECT_PT_DSCSAnimationPanel(bpy.types.Panel):
    bl_label       = "DSCS Animations"
    bl_idname      = "OBJECT_PT_DSCSAnimationPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.armature is not None

    def draw(self, context):
        armature = context.armature
        layout = self.layout
        
        armature_anims = {t.name: t for t in armature.animation_data.nla_tracks} if armature.animation_data is not None else {}
        materials = get_child_materials(armature)
        material_anims = {material.name: {t.name: t for t in material.animation_data.nla_tracks} for material in materials if material.animation_data is not None}
        # material anims are material.animation_data.nla_tracks
        # then need to do cameras
        # then need to do lights


        # Way to do this... probably to make a collection with a 'get' property..?
        # Might finally be time to look at StackExchange.
        # Need to end up with:
        # - Dict of anim name: anim collection pairs
        # - Each anim collection consists of:
        #     - A skeletal animation
        #     - A list of animated materials
        #     - A list of animated cameras
        #     - A list of animated lights
