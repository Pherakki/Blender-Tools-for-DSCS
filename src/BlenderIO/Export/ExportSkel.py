import bpy
from mathutils import Matrix
import struct

from ...Core.FileFormats.Skel.SkelInterface import SkelInterface
from ...Utilities.Hash import dscs_hash_string


def create_bpy_to_dscs_bone_map(armature_obj):
    return {bone.name: bidx for bidx, bone in enumerate(armature_obj.data.bones)}


def extract_skel(armature_obj, base_anim, errorlog, bpy_to_dscs_bone_map):
    armature = armature_obj.data
    props = armature.DSCS_ModelProperties
    si = SkelInterface()
    
    bone_indices = {bone.name: i for i, bone in enumerate(armature.bones)}
    for bidx, bone in enumerate(armature.bones):
        parent = bone.parent
        parent_idx = -1 if parent is None else bone_indices.get(parent.name, -1)
        
        pos   = list(base_anim.locations[bidx].values())[0]
        quat  = list(base_anim.rotations[bidx].values())[0]
        scale = list(base_anim.scales[bidx].values())[0]
        
        si.add_bone(dscs_hash_string(bone.name), 
                    parent_idx, 
                    bone.DSCS_BoneProperties.flag,
                    [*pos, 1.], 
                    quat, 
                    [*scale, 1.])
    
    for fc in props.float_channels:
        hsh = struct.unpack('I', struct.pack('i', fc.obj_hash))[0]
        si.add_float_channel(hsh, fc.flags, (fc.channel << 4) | fc.array_idx)

    return si
