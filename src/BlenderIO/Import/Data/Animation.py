import bpy
from mathutils import Quaternion

from .....external.blunger.interface.object import preserve_initial_active_object
from .....external.blunger.interface.object import set_active_obj
from .....external.blunger.interface.object import TempSwapActiveObjectMode
from .....external.blunger.interface.animation import create_fcurves
from .....external.blunger.dataproc.text import logged_decode
from .....external.blunger.dataproc.transform import BoneTransform
from .....external.blunger.dataproc.transform import parentspace_to_bindspace
from .....external.blunger.dataproc.transform import parentspace_to_bindspace_stdblend
from ...Globals import MODEL_TRANSFORMS


@preserve_initial_active_object
def import_base_animation(name_prefix, bpy_armature_obj, bone_names, base_anim, errorlog):
    bpy_armature_obj.animation_data_create()
    set_active_obj(bpy_armature_obj)
    
    with TempSwapActiveObjectMode("POSE"):
        rotations = convert_to_mathutils_quats(base_anim)
        construct_nla_action("base", name_prefix, bpy_armature_obj, errorlog, 
                             build_base_fcurves,
                             base_anim.positions, rotations, base_anim.scales,
                             base_anim.float_channels,
                             bone_names, base_anim.playback_rate, "REPLACE")
        

@preserve_initial_active_object
def import_animations(name_prefix, bpy_armature_obj, bone_names, ais, errorlog):
    # Need to remove dependence on NameInterface for separate anim import
    bpy_armature_obj.animation_data_create()
    set_active_obj(bpy_armature_obj)
    
    with TempSwapActiveObjectMode("POSE"): 
        for animation_name, animation_data in list(ais.items()):
            track_name = animation_name[len(name_prefix)+1:]  # +1 to also remove the underscore
            rotations = convert_to_mathutils_quats(animation_data)
            construct_nla_action(track_name, animation_name, bpy_armature_obj, errorlog, 
                                 build_blend_fcurves,
                                 animation_data.positions, rotations, animation_data.scales,
                                 animation_data.float_channels,
                                 bone_names, animation_data.playback_rate, "COMBINE")



##########################
# Helpers implementation #
##########################
def convert_to_mathutils_quats(anim):
    return {k: {k2: Quaternion([r[3], r[0], r[1], r[2]])  for k2, r in rdata.items()} for k, rdata in anim.rotations.items()}


def construct_nla_action(track_name, action_name, armature, errorlog, method, positions, rotations, scales, float_channels, bone_names, playback_rate, blend_type):
    action = bpy.data.actions.new(action_name)

    for positions, rotations, scales, bone_name in zip(positions.values(),
                                                       rotations.values(),
                                                       scales.values(),
                                                       bone_names):
        method(action, armature, bone_name, 1, positions, rotations, scales, errorlog)

    armature.animation_data.action = action
    track = armature.animation_data.nla_tracks.new()
    track.name = track_name
    track.mute = True
    nla_strip = track.strips.new(action.name, int(action.frame_range[0]), action)
    nla_strip.scale = 24 / playback_rate
    nla_strip.blend_type = blend_type
    armature.animation_data.action = None


def build_base_fcurves(action, armature, bone_name_bytes, fps, positions, rotations, scales, errorlog):
    # Set up action data
    bone_name = logged_decode(bone_name_bytes, "Bone name", errorlog)
    actiongroup = action.groups.new(bone_name)
    
    bpy_bone = armature.data.bones[bone_name]
    btrans = BoneTransform(bpy_bone, MODEL_TRANSFORMS)
    b_positions = parentspace_to_bindspace.t.vector(positions.values(), btrans)
    b_rotations = parentspace_to_bindspace.r.quat(rotations.values(), btrans)
    b_scales    = parentspace_to_bindspace.s.vector(scales.values(), btrans)


    rotation_frames = [float(fps*frame + 1) for frame in rotations.keys()]
    position_frames = [float(fps*frame + 1) for frame in positions.keys()]
    scale_frames    = [float(fps*frame + 1) for frame in scales   .keys()]

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", rotation_frames, b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", position_frames, b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", scale_frames,    b_scales,    [0, 1, 2]   )


def build_blend_fcurves(action, armature, bone_name, fps, positions, rotations, scales, errorlog):
    # Set up action data
    actiongroup = action.groups.new(bone_name)

    # Get the matrices required to convert animations from DSCS -> Blender
    bpy_bone = armature.data.bones[bone_name]
    btrans = BoneTransform(bpy_bone, MODEL_TRANSFORMS)
    b_positions = parentspace_to_bindspace_stdblend.t.vector(positions.values(), btrans)
    b_rotations = parentspace_to_bindspace_stdblend.r.quat(rotations.values(), btrans)
    b_scales    = parentspace_to_bindspace_stdblend.s.vector(scales.values(), btrans)


    # Create animations
    
    rotation_frames = [float(fps*frame + 1) for frame in rotations.keys()]
    position_frames = [float(fps*frame + 1) for frame in positions.keys()]
    scale_frames    = [float(fps*frame + 1) for frame in scales   .keys()]

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", rotation_frames, b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", position_frames, b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", scale_frames,    b_scales,    [0, 1, 2]   )
