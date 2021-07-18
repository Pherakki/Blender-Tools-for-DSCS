import copy
import numpy as np

from .AnimationReposingHelperFunctions import try_replace_rest_pose_elements
from .Interpolation import lerp, slerp, produce_interpolation_method_dict
from .Matrices import apply_transform_to_keyframe, generate_transform_matrix

quat_nm = "rotation_quaternion"
loc_nm = "location"
scale_nm = "scale"


def shift_initial_base_animation_data(filename, model_data):
    pose_delta = generate_composite_pose_delta(filename, model_data)
    animation = model_data.animations[filename]
    print("### INPUT ANIM ###""")
    print(animation)
    animation_dict = package_animation_into_dict(animation)
    print("### BEFORE SHIFT ###""")
    print(animation_dict)
    print("### POSE DELTA ###")
    print(pose_delta)
    animation_dict = shift_animation_by_transforms(pose_delta, animation_dict)
    print("### AFTER SHIFT ###""")
    print(animation_dict)
    unpack_dict_to_animation(animation, animation_dict)


def package_animation_into_dict(IF_animation):
    retval = {}
    for dataset in [IF_animation.rotations, IF_animation.locations, IF_animation.scales]:
        for bone_idx in dataset:
            retval[bone_idx] = {quat_nm: {},
                                loc_nm: {},
                                scale_nm: {}}
    for bone_idx, fcurve in IF_animation.rotations.items():
        retval[bone_idx][quat_nm] = {frame_idx: value for frame_idx, value in zip(fcurve.frames, fcurve.values)}
    for bone_idx, fcurve in IF_animation.locations.items():
        retval[bone_idx][loc_nm] = {frame_idx: value for frame_idx, value in zip(fcurve.frames, fcurve.values)}
    for bone_idx, fcurve in IF_animation.scales.items():
        retval[bone_idx][scale_nm] = {frame_idx: value for frame_idx, value in zip(fcurve.frames, fcurve.values)}
    return retval


def unpack_dict_to_animation(IF_animation, animation_dict):
    IF_animation.rotations = {}
    IF_animation.locations = {}
    IF_animation.scale = {}
    for bone_idx in animation_dict:
        for curve_type, factory in zip([quat_nm, loc_nm, scale_nm],
                                       [IF_animation.add_rotation_fcurve, IF_animation.add_location_fcurve, IF_animation.add_scale_fcurve]):
            fcurve_data = animation_dict[bone_idx][curve_type]
            if len(fcurve_data):
                factory(bone_idx, list(fcurve_data.keys()), list(fcurve_data.values()))
    print(IF_animation.rotations)
    print(IF_animation.locations)
    print(IF_animation.scale)


def generate_composite_pose_delta(filename, model_data):
    """
    Combines the base animation and rest pose of a model into the shift from the bind pose
    used to make the animations work.
    """
    rest_pose = [copy.deepcopy(item) for item in model_data.skeleton.rest_pose_delta]
    base_animation = model_data.animations[filename]
    for bone_idx, fcurve in base_animation.rotations.items():
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 0, fcurve, rotation=True)
    for bone_idx, fcurve in base_animation.locations.items():
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 1, fcurve, location=True)
    for bone_idx, fcurve in base_animation.scales.items():
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 2, fcurve)

    return {bone_idx: generate_transform_matrix(*pose_data, WXYZ=True) for bone_idx, pose_data in enumerate(rest_pose)}


def shift_animation_by_transforms(transforms, animation_data):
    """
    Applies the input transforms to each keyframe in the animation data.
    """
    retval = {}
    for bone_name, transform in transforms.items():
        rotation_data = animation_data.get(bone_name, {}).get('rotation_quaternion', {})
        location_data = animation_data.get(bone_name, {}).get('location', {})
        scale_data = animation_data.get(bone_name, {}).get('scale', {})

        retval[bone_name] = {'rotation_quaternion': {},
                             'location': {},
                             'scale': {}}

        rotation_interpolator = produce_interpolation_method_dict(rotation_data,
                                                             np.array([1., 0., 0., 0.]), slerp)
        location_interpolator = produce_interpolation_method_dict(location_data,
                                                             np.array([0., 0., 0.]), lerp)
        scale_interpolator = produce_interpolation_method_dict(scale_data,
                                                          np.array([1., 1., 1.]), lerp)

        all_frames = set()
        all_frames.update(set(rotation_data.keys()))
        all_frames.update(set(location_data.keys()))
        all_frames.update(set(scale_data.keys()))
        all_frames = sorted(list(all_frames))

        for frame in all_frames:
            t, r, s = apply_transform_to_keyframe(transform,
                                                  frame, rotation_data, rotation_interpolator,
                                                  location_data, location_interpolator, scale_data, scale_interpolator)

            if frame in rotation_data:
                rotation_data[frame] = r
            if frame in location_data:
                location_data[frame] = t
            if frame in scale_data:
                scale_data[frame] = s

        retval[bone_name]['rotation_quaternion'] = rotation_data
        retval[bone_name]['location'] = location_data
        retval[bone_name]['scale'] = scale_data
    return retval
