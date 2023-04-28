import numpy as np
import bpy
from mathutils import Matrix, Quaternion

from ...Core.FileFormats.Anim.AnimInterface import AnimInterface
from ..IOHelpersLib.Animations import group_fcurves_by_bone_and_type, extract_clean_animation_data
from ..IOHelpersLib.Animations import bind_relative_to_parent_relative
from ..IOHelpersLib.Animations import bind_relative_to_parent_relative_preblend
from ..Utils.BoneUtils import upY_to_upZ_matrix


def extract_base_anim(bpy_armature_obj, errorlog, bpy_to_dscs_bone_map):
    if bpy_armature_obj.animation_data is None:
        errorlog.log_warning_message("No animation data present for '{bpy_armature_obj.name}': using bind pose as base animation")
        ai = AnimInterface()
    elif "base" not in bpy_armature_obj.animation_data.nla_tracks:
        errorlog.log_warning_message("No NLA track called 'base' found for '{bpy_armature_obj.name}': using bind pose as base animation")
        ai = AnimInterface()
    else:
        base_anim_track = bpy_armature_obj.animation_data.nla_tracks["base"]
        ai = extract_anim(bpy_armature_obj, base_anim_track, errorlog, bpy_to_dscs_bone_map, is_base=True)
    
    # Load up data for any missing indices from the armature
    for bone in bpy_armature_obj.data.bones:
        bone_idx = bpy_to_dscs_bone_map[bone.name]
        
        has_pos = bone_idx in ai.locations
        has_rot = bone_idx in ai.rotations
        has_scl = bone_idx in ai.scales
        # Skip bone if it's fully accounted for
        if all((has_pos, has_rot, has_scl)):
            continue
        
        # Else, get the bind pose transform and use that...
        # since that's what Blender falls back to.
        # Although here we will of course be transforming to parent-relative
        # coordinates.
        parent = bone.parent
        if parent is None:
            parent_matrix = Matrix.Identity(4)
        else:
            parent_matrix = parent.matrix_local
            
        # Need to shove the axis permutation matrices in here to make this
        # fully general.
        # Should really cook up a "transformer" class that can be used to do
        # this stuff instead of randomly passing matrices around?!!
        pos, quat, scale = (parent_matrix.inverted() @ bone.matrix_local).decompose()
        
        if not has_pos: ai.locations[bone_idx] = {0: [pos.x, pos.y, pos.z]}
        if not has_rot: ai.rotations[bone_idx] = {0: [quat.x, quat.y, quat.z, quat.w]}
        if not has_scl: ai.scales   [bone_idx] = {0: [scale.x, scale.y, scale.z]}
        
    return ai

def extract_anims(armature, errorlog, bpy_to_dscs_bone_map):
    ais = {}
    if armature.animation_data is None:
        return ais
    
    for track in armature.animation_data.nla_tracks:
        if track.name == "base":
            continue
        ai = extract_anim(armature, track, errorlog, bpy_to_dscs_bone_map, is_base=False)
        if ai is not None:
            ais[track.name] = ai
    
    return ais

def optimise_base_anim(ai):
    """
    Optimise the base animation by dropping any animation channels with less
    than two frames, since these are already loaded into constant skeleton data.
    """
    ai.locations      = {idx: data for idx, data in ai.locations     .items() if len(data) > 1}
    ai.rotations      = {idx: data for idx, data in ai.rotations     .items() if len(data) > 1}
    ai.scales         = {idx: data for idx, data in ai.scales        .items() if len(data) > 1}
    ai.float_channels = {idx: data for idx, data in ai.float_channels.items() if len(data) > 1}

def extract_anim(bpy_armature_obj, nla_track, errorlog, bpy_to_dscs_bone_map, is_base):
    if is_base:
        transform = bind_relative_to_parent_relative
    else:
        transform = bind_relative_to_parent_relative_preblend
    
    strip_count = len(nla_track.strips)
    if strip_count == 0:
        errorlog.log_warning_message()
        return None
    elif strip_count > 1:
        errorlog.log_warning_message(f"NLA Track '{nla_track.name}' has {strip_count} NLA Strips - only the first will be exported")
    
    ai = AnimInterface()
    strip = nla_track.strips[0]
    action = strip.action
    node_transforms = get_action_data(action, bpy_armature_obj, 
                                      transform,
                                      upY_to_upZ_matrix,
                                      Matrix.Identity(4))
    
    # Clean up extracted animation data
    t = {}
    r = {}
    s = {}
    missing_bones = []
    for (bpy_bidx, bname, pos, rot, scl) in node_transforms:
        if bname not in bpy_to_dscs_bone_map:
            missing_bones.append(bname)
            continue
        dscs_bidx = bpy_to_dscs_bone_map[bname]
        t[dscs_bidx] = pos
        r[dscs_bidx] = rot
        s[dscs_bidx] = scl
    if len(missing_bones):
        errorlog.log_warning_message(f"Animation track '{nla_track.name}' has animations for {len(missing_bones)} bone{'s' if len(missing_bones) > 1 else ''} that are not in the armature '{bpy_armature_obj.name}' - these have not been exported")
    
    # HANDLE FLOAT CHANNELS SMARTER WHEN THEY ARE EDITABLE!!!!
    # NEED TO FIND OUT EVERYTHING THAT *CAN* BE EDITED ON CAMS AND LAMPS!!!
    float_channels = {}
    props = action.DSCS_AnimationProperties
    for bpy_fc in props.float_channels:
        keyframes = {}
        for bpy_kf in bpy_fc:
            keyframes[bpy_kf.frame] = bpy_kf.value
        float_channels[bpy_fc.channel_idx] = keyframes
    
    # Need to integerise the frames!!
    # -> Need to bin each frame.
    # -> The width of the bin has a hard minimum, and is determined by the distance
    #    between frames.
    #    So take all inverse frame distances, and take the smallest between the largest
    #    distance and (say) 128 as the max inverse bin width.
    # -> Multiply each frame by the inverse bin width.
    # -> Set the animation speed accordingly.
    # -> If any bin has more than 1 entry, throw errors.
    t = {bidx: {int(frame): v                    for frame, v in bone_data.items()} for bidx, bone_data in t.items()}
    r = {bidx: {int(frame): [q.x, q.y, q.z, q.w] for frame, q in bone_data.items()} for bidx, bone_data in r.items()}
    s = {bidx: {int(frame): v                    for frame, v in bone_data.items()} for bidx, bone_data in s.items()}

    ai.playback_rate  = 24 / strip.scale
    ai.bone_count     = len(bpy_armature_obj.data.bones)
    ai.locations      = t
    ai.rotations      = r
    ai.scales         = s
    ai.float_channels = float_channels

    return ai


def get_action_data(action, bpy_armature_obj, transform, inverse_world_axis_rotation, bone_axis_permutation):
    curve_defaults = {'location': [0., 0., 0.],
                      'rotation_quaternion': [1., 0., 0., 0.],
                      'scale': [1., 1., 1.],
                      'rotation_euler': [0, 0, 0]}
    
    bone_names = [b.name for b in bpy_armature_obj.data.bones]
    out = []
    animation_data = {}
    fcurve_groups, obj_transforms = group_fcurves_by_bone_and_type(action)
    for bone_name, group in fcurve_groups.items():
        if bone_name not in bpy_armature_obj.pose.bones:
            continue
        animation_data[bone_name] = {'rotation_quaternion': {},
                                     'location': {},
                                     'scale': {},
                                     'rotation_euler': {}}
        
        bpy_bone = bpy_armature_obj.data.bones[bone_name]
        extract_clean_animation_data(group, curve_defaults, animation_data[bone_name], bpy_armature_obj.pose.bones[bone_name])
        ad = animation_data[bone_name]
        t, r, s = transform(bpy_bone, 
                            ad["location"].values(),
                            [Quaternion(q) for q in ad["rotation_quaternion"].values()],
                            ad["scale"].values(),
                            inverse_world_axis_rotation,
                            bone_axis_permutation)
        
        out.append([bone_names.index(bone_name), bone_name, 
                    {(k-1) : v for k, v in zip(ad["location"].keys(), t)}, 
                    {(k-1) : v for k, v in zip(ad["rotation_quaternion"], r)}, 
                    {(k-1) : v for k, v in zip(ad["scale"], s)}])

    return out
