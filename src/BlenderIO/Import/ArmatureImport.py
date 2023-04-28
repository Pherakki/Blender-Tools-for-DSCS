import bpy
import math
from mathutils import Vector, Matrix

from ..IOHelpersLib.Bones import construct_bone, resize_bones
from ..IOHelpersLib.Context import safe_active_object_switch
from ..Utils.BoneUtils import MayaBoneToBlenderBone


@safe_active_object_switch
def import_skeleton(collection, armature_name, ni, si, gi, model_dims):
    armature_obj = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    collection.objects.link(armature_obj)
    armature = armature_obj.data
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Rig
    list_of_bones = {}
    dscs_to_bpy_bone_map = {}
    bpms = [Matrix([m[0:4],
                    m[4:8],
                    m[8:12],
                    [0., 0., 0., 1.]]).inverted() for m in gi.ibpms]
    for bone_idx, bone in enumerate(si.bones):
        # Throw warning if there is a hash collision
        dscs_to_bpy_bone_map[bone.name_hash] = len(list_of_bones)
        
        bone_name = ni.bone_names[bone_idx]
        bpy_bone = construct_bone(bone_name, armature_obj, MayaBoneToBlenderBone(bpms[bone_idx]), 1)
        list_of_bones[bone_idx] = bpy_bone
        
        if bone.parent != -1:
            bpy_bone.parent = list_of_bones[bone.parent]

    # Save the bones
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Now edit their lengths
    if all([e < 0.0001 for e in model_dims]):
        model_dims = [10., 10., 10.]
    resize_bones(armature_obj, default_size=[.1*d for d in model_dims], min_bone_length=0.01)
    
    # Import custom props
    for bone_idx, bone in zip(list_of_bones.keys(), armature.bones):
        bone.DSCS_BoneProperties.flag = si.bones[bone_idx].flag
    
    # Now get the float channels in
    for fc in si.float_channels:
        bpy_fc = armature.DSCS_ModelProperties.float_channels.add()
        bpy_fc.obj_hash  = fc.name_hash
        bpy_fc.flags     = fc.flags
        bpy_fc.channel   = fc.array_idx // 16
        bpy_fc.array_idx = fc.array_idx % 16
    
    return armature_obj, dscs_to_bpy_bone_map
