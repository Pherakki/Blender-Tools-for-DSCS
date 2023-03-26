import bpy

from ..IOHelpersLib.Animations import create_fcurves
from ..IOHelpersLib.Animations import parent_relative_to_bind_relative
from ..IOHelpersLib.Animations import parent_relative_to_bind_relative_preblend
from ..IOHelpersLib.Context    import safe_active_object_switch, set_active_obj
from ..Utils.BoneUtils import boneY_to_boneX_matrix, upY_to_upZ_matrix

from mathutils import Matrix


@safe_active_object_switch
def import_base_animation(directory, name_prefix, armature, ni, base_anim):
    armature.animation_data_create()
    set_active_obj(armature)
    
    bpy.ops.object.mode_set(mode="POSE")
    construct_nla_action("base", name_prefix, armature, build_base_fcurves, 
                         base_anim.locations, base_anim.rotations, base_anim.scales, 
                         ni.bone_names, base_anim.playback_rate, "REPLACE")
    bpy.ops.object.mode_set(mode="OBJECT")


@safe_active_object_switch
def import_animations(directory, name_prefix, armature, ni, ais):
    # Need to remove dependence on NameInterface for separate anim import
    armature.animation_data_create()
    set_active_obj(armature)
    
    bpy.ops.object.mode_set(mode="POSE")    
    for animation_name, animation_data in list(ais.items()):
        track_name = animation_name[len(name_prefix)+1:]  # +1 to also remove the underscore
        construct_nla_action(track_name, animation_name, armature, build_blend_fcurves,
                             animation_data.locations, animation_data.rotations, animation_data.scales, 
                             ni.bone_names, animation_data.playback_rate, "COMBINE")
    bpy.ops.object.mode_set(mode="OBJECT")

#########
# UTILS #
#########

def construct_nla_action(track_name, action_name, armature, method, positions, rotations, scales, bone_names, playback_rate, blend_type):
    action = bpy.data.actions.new(action_name)

    for positions, rotations, scales, bone_name in zip(positions.values(),
                                                       rotations.values(),
                                                       scales.values(),
                                                       bone_names):
        method(action, armature, bone_name, 1, positions, rotations, scales)

    armature.animation_data.action = action
    track = armature.animation_data.nla_tracks.new()
    track.name = track_name
    track.mute = True
    nla_strip = track.strips.new(action.name, int(action.frame_range[0]), action)
    nla_strip.scale = 24 / playback_rate
    nla_strip.blend_type = blend_type
    armature.animation_data.action = None


def build_base_fcurves(action, armature, bone_name, fps, positions, rotations, scales):
    # Set up action data
    actiongroup = action.groups.new(bone_name)
    
    bpy_bone = armature.data.bones[bone_name]
    b_positions, \
    b_rotations, \
    b_scales = parent_relative_to_bind_relative(bpy_bone, 
                                                positions.values(), 
                                                ([q[3], q[0], q[1], q[2]] for q in rotations.values()), 
                                                scales.values(),
                                                upY_to_upZ_matrix.inverted(),
                                                Matrix.Identity(4))

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", fps, rotations.keys(), b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", fps, positions.keys(), b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", fps, scales   .keys(), b_scales,    [0, 1, 2]   )


def build_blend_fcurves(action, armature, bone_name, fps, positions, rotations, scales):
    # Set up action data
    actiongroup = action.groups.new(bone_name)

    # Get the matrices required to convert animations from DSCS -> Blender
    bpy_bone = armature.data.bones[bone_name]
    b_positions, \
    b_rotations, \
    b_scales = parent_relative_to_bind_relative_preblend(bpy_bone, 
                                                          positions.values(), 
                                                          ([q[3], q[0], q[1], q[2]] for q in rotations.values()), 
                                                          scales.values(),
                                                          upY_to_upZ_matrix.inverted(),
                                                          Matrix.Identity(4))

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", fps, rotations.keys(), b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", fps, positions.keys(), b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", fps, scales   .keys(), b_scales,    [0, 1, 2]   )
