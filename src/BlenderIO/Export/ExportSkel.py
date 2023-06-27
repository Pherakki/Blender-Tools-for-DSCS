import bpy
from mathutils import Matrix
import struct

from ...Core.FileFormats.Skel.SkelInterface import SkelInterface
from ...Utilities.Hash import dscs_hash_string

AUTO_FLAG_BANK = {
    0x00: 0,  # Light
    0x01: 8,  # Light
    0x02: 16, # Light
    0x03: 0,  # Light
    0x07: 0,  # Camera
}

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


def create_missing_float_channels(skel, handled_channels, unhandled_channels, errorlog):
    # Figure out what channels already exist
    float_channel_defs = {}
    for idx, fc in enumerate(skel.float_channels):
        float_channel_defs[(fc.name_hash, fc.array_index)] = idx
    
    
    float_channels = {}
    # Add unhandled
    for channel_idx, channel_data in unhandled_channels.items():
        if channel_idx >= len(skel.float_channels):
            # TODO: LOG ERROR
            raise ValueError("WRUVHKLMELRE KML EMK")
        else:
            float_channels[channel_idx] = channel_data
    
    # Create new channels
    for hsh, anim_data in handled_channels.items():
        for array_idx, channel_data in anim_data.items():
            key = (hsh, array_idx)
            
            
            if key in float_channel_defs:
                channel_idx = float_channel_defs[key]
            else:
                flags = AUTO_FLAG_BANK.get(array_idx, 8)
                channel_idx = len(skel.float_channels)
                skel.add_float_channel(hsh, flags, array_idx)
            
            # TODO: FIX ME
            if channel_idx in float_channels:
                errorlog.log_warning_message("fijpgrjigrjipvjpi")
            float_channels[channel_idx] = channel_data
    
    return float_channels
    