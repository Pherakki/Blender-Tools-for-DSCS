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
    resize_bones(armature, default_size=[.1*d for d in model_dims], min_bone_length=0.01)
    
    return armature_obj, dscs_to_bpy_bone_map
