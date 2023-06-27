import bpy
import math
from mathutils import Vector, Matrix
import struct

from ..IOHelpersLib.Animations import transform_bone_matrix
from ..IOHelpersLib.Bones      import construct_bone, resize_bones
from ..IOHelpersLib.Context    import safe_active_object_switch
from ..Utils.BoneUtils         import MODEL_TRANSFORMS


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
        bpy_bone = construct_bone(bone_name, armature_obj, transform_bone_matrix(bpms[bone_idx], MODEL_TRANSFORMS), 1)
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
    
    hashes = {}
    for i, m in enumerate(gi.materials):
        hashes[m.name_hash] = ni.material_names[i]
    for i, b in enumerate(si.bones):
        hashes[b.name_hash] = ni.bone_names[i]
    
    # Now get the float channels in
    for fc in si.float_channels:
        bpy_fc = armature.DSCS_ModelProperties.float_channels.add()
        bpy_fc.obj_hash  = struct.unpack('i', struct.pack('I', fc.name_hash))[0]
        bpy_fc.obj_name  = hashes.get(fc.name_hash, "???")
        
        bpy_fc.flags     = fc.flags
        bpy_fc.channel   = fc.array_index >> 4
        bpy_fc.array_idx = fc.array_index & 0x0000000F
    
    return armature_obj, dscs_to_bpy_bone_map
