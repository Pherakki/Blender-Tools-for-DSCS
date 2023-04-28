import math
import bpy
from mathutils import Matrix

from ..IOHelpersLib.Collection import init_collection
from ..IOHelpersLib.Objects import lock_obj_transforms
from ..IOHelpersLib.UI import UIListBase


class OBJECT_UL_DSCSFloatChannelUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.split(factor=0.2)
        split.prop(item, "obj_name", emboss=False)
        # obj hash?
        split.prop(item, "flags")
        split.prop(item, "channel")
        split.prop(item, "array_idx")

_base_class = UIListBase(
    "import_dscs",
    "FloatChannels", 
    OBJECT_UL_DSCSFloatChannelUIList, 
    "float_channels", 
    "active_float_channel_idx", 
    lambda x: x.armature.DSCS_ModelProperties
)

class OBJECT_OT_AddCamera(bpy.types.Operator):
    bl_label  = "Add Camera"
    bl_idname =  "import_dscs.OBJECT_OT_AddCamera".lower()
    
    def execute(self, context):
        bpy_armature_obj = context.active_object
        bpy_armature     = context.armature
        props            = bpy_armature.DSCS_ModelProperties
        
        armature_collection = bpy_armature_obj.users_collection[0]
        collection_name = f"{armature_collection.name} Cameras"
        if collection_name not in armature_collection.children:
            init_collection(collection_name, armature_collection)
        collection = armature_collection.children[collection_name]
        
        # Need to put this into the "Cameras" collection inside the model's collection
        cam_name = f"{bpy_armature.name} New Camera"
        camera = bpy.data.cameras.new(cam_name)
        bpy_camera_obj = bpy.data.objects.new(cam_name, camera)
        collection.objects.link(bpy_camera_obj)
        
        
        constraint = bpy_camera_obj.constraints.new("CHILD_OF")
        constraint.target = context.active_object
        constraint.subtarget = props.new_cam_parent_bone
        constraint.inverse_matrix = Matrix.Identity(4)
        
        bpy_camera_obj.location = [0., 0., 0.]
        bpy_camera_obj.rotation_euler[0] = 90 * (math.pi/180)
        bpy_camera_obj.scale = [1., 1., 1.]
        lock_obj_transforms(bpy_camera_obj)
        
        return {'FINISHED'}

class OBJECT_OT_AddLight(bpy.types.Operator):
    bl_label  = "Add Light"
    bl_idname = "import_dscs.OBJECT_OT_AddLight".lower()
    
    def execute(self, context):
        bpy_armature_obj = context.active_object
        bpy_armature     = context.armature
        props            = bpy_armature.DSCS_ModelProperties
        
        armature_collection = bpy_armature_obj.users_collection[0]
        collection_name = f"{armature_collection.name} Lights"
        if collection_name not in armature_collection.children:
            init_collection(collection_name, armature_collection)
        collection = armature_collection.children[collection_name]
        
        # Need to put this into the "Lights" collection inside the model's collection
        lgt_name = f"{bpy_armature.name} New Light"
        bpy_light = bpy.data.lights.new(lgt_name, "POINT")
        bpy_light_obj = bpy.data.objects.new(lgt_name, bpy_light)
        collection.objects.link(bpy_light_obj)
        
        
        constraint = bpy_light_obj.constraints.new("CHILD_OF")
        constraint.target = context.active_object
        constraint.subtarget = props.new_lgt_parent_bone
        constraint.inverse_matrix = Matrix.Identity(4)

        bpy_light_obj.location = [0., 0., 0.]
        bpy_light_obj.rotation_euler[0] = 90 * (math.pi/180)
        bpy_light_obj.scale = [1., 1., 1.]
        lock_obj_transforms(bpy_light_obj)
        
        return {'FINISHED'}


class OBJECT_PT_DSCSModelPanel(_base_class):
    bl_label       = "DSCS Model"
    bl_idname      = "OBJECT_PT_DSCSModelPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.armature is not None

    def draw(self, context):
        layout = self.layout
        bpy_armature = context.armature
        props = bpy_armature.DSCS_ModelProperties
            
        row = layout.row()
        c1 = row.column()
        c1.operator(OBJECT_OT_AddCamera.bl_idname)
        c2 = row.column()
        c2.prop_search(props, "new_cam_parent_bone", bpy_armature, "bones")
        c1.active = props.new_cam_parent_bone != ""
        
        row = layout.row()
        row.operator(OBJECT_OT_AddLight.bl_idname)
        row.prop_search(props, "new_lgt_parent_bone", bpy_armature, "bones")
        
        _base_class.draw_collection(self, context)

    @classmethod
    def register(cls):
        bpy.utils.register_class(OBJECT_UL_DSCSFloatChannelUIList)
        bpy.utils.register_class(OBJECT_OT_AddCamera)
        bpy.utils.register_class(OBJECT_OT_AddLight)
        _base_class.register()
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(OBJECT_UL_DSCSFloatChannelUIList)
        bpy.utils.unregister_class(OBJECT_OT_AddCamera)
        bpy.utils.unregister_class(OBJECT_OT_AddLight)
        _base_class.unregister()
