import math
import bpy
from mathutils import Matrix

from ..IOHelpersLib.Collection import init_collection
from ..IOHelpersLib.Objects import lock_obj_transforms
from ..IOHelpersLib.UI import UIListBase


class OBJECT_UL_DSCSFloatChannelUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.row()
        split.prop(item, "obj_name", text="", emboss=False)
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
    bl_options = {"UNDO"}
    
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
    bl_options = {"UNDO"}
    
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


class OBJECT_OT_ToggleNonRenderedMeshes(bpy.types.Operator):
    bl_label = "Toggle Non-Rendered Colliders"
    bl_idname = "import_dscs.OBJECT_OT_ToggleNonRenderedMeshes".lower()
    bl_options = {"UNDO"}
    
    def execute(self, context):
        bpy_armature = context.armature
        props = bpy_armature.DSCS_ModelProperties
        
        nonrendered_meshes = props.get_nonrendered_meshes(context.object)
        props.nonrendered_mesh_toggle_is_show = not props.are_all_visible(nonrendered_meshes)
        if props.nonrendered_mesh_toggle_is_show:
            for m in nonrendered_meshes:
                m.hide_set(False)
        else:
            for m in nonrendered_meshes:
                m.hide_set(True)
        props.nonrendered_mesh_toggle_is_show = not props.nonrendered_mesh_toggle_is_show
        
        return {'FINISHED'}


class OBJECT_OT_ToggleSolidColliders(bpy.types.Operator):
    bl_label = "Toggle Solid Colliders"
    bl_idname = "import_dscs.OBJECT_OT_ToggleSolidColliders".lower()
    bl_options = {"UNDO"}
    
    def execute(self, context):
        bpy_armature = context.armature
        props = bpy_armature.DSCS_ModelProperties
        
        colliders = props.get_solid_colliders(context.object)
        props.solidcollider_toggle_is_show = not props.are_all_visible(colliders)
        if props.solidcollider_toggle_is_show:
            for m in colliders:
                m.hide_set(False)
        else:
            for m in colliders:
                m.hide_set(True)
        props.solidcollider_toggle_is_show = not props.solidcollider_toggle_is_show
        
        return {'FINISHED'}

class OBJECT_OT_ToggleNonSolidColliders(bpy.types.Operator):
    bl_label = "Toggle Non-Solid Colliders"
    bl_idname = "import_dscs.OBJECT_OT_ToggleNonSolidColliders".lower()
    bl_options = {"UNDO"}
    
    def execute(self, context):
        bpy_armature = context.armature
        props = bpy_armature.DSCS_ModelProperties
        
        
        colliders = props.get_nonsolid_colliders(context.object)
        props.nonsolidcollider_toggle_is_show = not props.are_all_visible(colliders)
        if props.nonsolidcollider_toggle_is_show:
            for m in colliders:
                m.hide_set(False)
        else:
            for m in colliders:
                m.hide_set(True)
        props.nonsolidcollider_toggle_is_show = not props.nonsolidcollider_toggle_is_show
        
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

    def handle_visiblity_toggle(self, layout, context, props, getter, op, message):
        row = layout.row()
        objs = getter(context.object)
        if len(objs):
            do_show = not props.are_all_visible(objs)
            op_verb = "Show" if do_show else "Hide"
            text = f"{op_verb} {message}"
            enabled = True
        else:
            text = f"Model has no {message}"
            enabled = False
        row.operator(op.bl_idname, text=text)
        row.enabled = enabled


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
        
        self.handle_visiblity_toggle(layout, context, props, props.get_nonrendered_meshes, OBJECT_OT_ToggleNonRenderedMeshes, "Non-Rendered Meshes")
        self.handle_visiblity_toggle(layout, context, props, props.get_solid_colliders,    OBJECT_OT_ToggleSolidColliders,    "Solid Colliders")
        self.handle_visiblity_toggle(layout, context, props, props.get_nonsolid_colliders, OBJECT_OT_ToggleNonSolidColliders, "Non-Solid Colliders")
     
        _base_class.draw_collection(self, context)

    @classmethod
    def register(cls):
        bpy.utils.register_class(OBJECT_UL_DSCSFloatChannelUIList)
        bpy.utils.register_class(OBJECT_OT_AddCamera)
        bpy.utils.register_class(OBJECT_OT_AddLight)
        bpy.utils.register_class(OBJECT_OT_ToggleNonRenderedMeshes)
        bpy.utils.register_class(OBJECT_OT_ToggleSolidColliders)
        bpy.utils.register_class(OBJECT_OT_ToggleNonSolidColliders)
        _base_class.register()
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(OBJECT_UL_DSCSFloatChannelUIList)
        bpy.utils.unregister_class(OBJECT_OT_AddCamera)
        bpy.utils.unregister_class(OBJECT_OT_AddLight)
        bpy.utils.unregister_class(OBJECT_OT_ToggleNonRenderedMeshes)
        bpy.utils.unregister_class(OBJECT_OT_ToggleSolidColliders)
        bpy.utils.unregister_class(OBJECT_OT_ToggleNonSolidColliders)
        _base_class.unregister()
