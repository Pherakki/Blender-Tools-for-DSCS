import bpy
from mathutils import Matrix
import struct

from .....external.blunger.interface.object import preserve_initial_active_object
from .....external.blunger.interface.object import set_active_obj, set_mode
from .....external.blunger.interface.object import TempSwapActiveObjectMode
from .....external.blunger.interface.armature import construct_bone
from .....external.blunger.interface.armature import resize_bone_lengths
#from .....external.blunger.dataproc.text import logged_decode

from ...Globals import MODEL_TRANSFORMS


@preserve_initial_active_object
def import_skeleton(collection, armature_name, bone_names, material_names, si, gi, model_dims, errorlog):
    bpy_armature_object = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    collection.objects.link(bpy_armature_object)
    bpy_armature = bpy_armature_object.data
    
    set_active_obj(bpy_armature_object)
    set_mode("OBJECT")
    with TempSwapActiveObjectMode('EDIT'):
        # Get IBPMs
        list_of_bones = {}
        dscs_to_bpy_bone_map = {}
        bpms = [Matrix([m[0:4],
                        m[4:8],
                        m[8:12],
                        [0., 0., 0., 1.]]).inverted() for m in gi.ibpms]
        
        for bone_idx, bone in enumerate(si.bones):
            # Throw warning if there is a hash collision
            dscs_to_bpy_bone_map[bone.name_hash] = len(list_of_bones)
            
            bone_name = bone_names[bone_idx]
            bpy_bone = construct_bone(bone_name, bpy_armature_object, MODEL_TRANSFORMS.transform_bone_matrix4x4(bpms[bone_idx]), 1)
            list_of_bones[bone_idx] = bpy_bone
            
            if bone.parent != -1:
                bpy_bone.parent = list_of_bones[bone.parent]

    # Edit bone lengths
    if all(e < 0.0001 for e in model_dims):
        model_dims = [10., 10., 10.]
    resize_bone_lengths(bpy_armature_object, default_size=[.1*d for d in model_dims], min_bone_length=0.01)
    
    # Import custom props
    for bone_idx, bone in zip(list_of_bones.keys(), bpy_armature.bones):
        bone.DSCS_BoneProperties.flag = si.bones[bone_idx].flag
    
    hashes = {}
    for i, m in enumerate(gi.materials):
        hashes[m.name_hash] = material_names[i]
    for i, b in enumerate(si.bones):
        hashes[b.name_hash] = bone_names[i]
    
    # Now get the float channels in
    for fc in si.float_channels:
        bpy_fc = bpy_armature.DSCS_ModelProperties.float_channels.add()
        bpy_fc.obj_hash  = struct.unpack('i', struct.pack('I', fc.name_hash))[0]
        bpy_fc.obj_name  = hashes.get(fc.name_hash, "???")
        
        bpy_fc.flag_0    = (fc.flags >> 0) & 1
        bpy_fc.flag_1    = (fc.flags >> 1) & 1
        bpy_fc.flag_2    = (fc.flags >> 2) & 1
        bpy_fc.flag_3    = (fc.flags >> 3) & 1
        bpy_fc.flag_4    = (fc.flags >> 4) & 1
        bpy_fc.flag_5    = (fc.flags >> 5) & 1
        bpy_fc.flag_6    = (fc.flags >> 6) & 1
        bpy_fc.flag_7    = (fc.flags >> 7) & 1
        bpy_fc.channel   = fc.array_index >> 4
        bpy_fc.array_idx = fc.array_index & 0x0000000F
    
    return bpy_armature_object, dscs_to_bpy_bone_map
