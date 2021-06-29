import copy
import numpy as np

from .AnimationReposingHelperFunctions import try_replace_rest_pose_elements
from .Interpolation import lerp, slerp, produce_interpolation_method
from .Matrices import apply_transform_to_keyframe, generate_transform_matrix


def shift_animation_data(filename, model_data):
    pose_delta = generate_composite_pose_delta(filename, model_data)
    for animation_name in model_data.animations:
        animation = model_data.animations[animation_name]
        animation_dict = package_animation_into_dict(animation)
        animation_dict = shift_animation_by_transforms(pose_delta, animation_dict)
        unpack_dict_to_animation(animation, animation_dict)


def package_animation_into_dict(IF_animation):
    return {"rotation_quaternion": repackage_fcurves(IF_animation.rotations),
            "location": repackage_fcurves(IF_animation.locations),
            "scale": repackage_fcurves(IF_animation.scales)}


def repackage_fcurves(dict_of_fcurves):
    retval = {}
    for bone_idx, fcurve in dict_of_fcurves.items():
        retval[bone_idx] = {frame_idx: value for frame_idx, value in zip(fcurve.frames, fcurve.values)}
    return retval


def unpack_dict_to_animation(IF_animation, animation_dict):
    IF_animation.rotations = {}
    for bone_idx, fcurve_data in animation_dict["rotation_quaternion"].items():
        IF_animation.add_rotation_fcurve(bone_idx, list(fcurve_data.keys()), list(fcurve_data.values()))
    IF_animation.locations = {}
    for bone_idx, fcurve_data in animation_dict["location"].items():
        IF_animation.add_location_fcurve(bone_idx, list(fcurve_data.keys()), list(fcurve_data.values()))
    IF_animation.scale = {}
    for bone_idx, fcurve_data in animation_dict["scale"].items():
        IF_animation.add_scale_fcurve(bone_idx, list(fcurve_data.keys()), list(fcurve_data.values()))


def generate_composite_pose_delta(filename, model_data):
    """
    Combines the base animation and rest pose of a model into the shift from the bind pose
    used to make the animations work.
    """
    rest_pose = [copy.deepcopy(item) for item in model_data.skeleton.rest_pose_delta]
    base_animation = model_data.animations[filename]
    for bone_idx, fcurve in base_animation.rotations.items():
        print(">>>", bone_idx, rest_pose[bone_idx])
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 0, fcurve, rotation=True)
    for bone_idx, fcurve in base_animation.locations.items():
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 1, fcurve, location=True)
    for bone_idx, fcurve in base_animation.scales.items():
        rest_pose[bone_idx] = try_replace_rest_pose_elements(rest_pose[bone_idx], 2, fcurve)

    return rest_pose


def shift_animation_by_transforms(transforms, animation_data):
    """
    Applies the input transforms to each keyframe in the animation data.
    """
    rotations = animation_data['rotation_quaternion']
    locations = animation_data['location']
    scales = animation_data['scale']

    retval = {'rotation_quaternion': {},
              'location': {},
              'scale': {}}
    for bone_idx, transform in enumerate(transforms):
        rotation_data = rotations.get(bone_idx, {})
        location_data = locations.get(bone_idx, {})
        scale_data = scales.get(bone_idx, {})

        rotation_interpolator = produce_interpolation_method(list(rotation_data.keys()), list(rotation_data.values()),
                                                             np.array([0., 0., 0., 1.]), slerp)
        location_interpolator = produce_interpolation_method(list(location_data.keys()), list(location_data.values()),
                                                             np.array([0., 0., 0.]), lerp)
        scale_interpolator = produce_interpolation_method(list(scale_data.keys()), list(scale_data.values()),
                                                          np.array([1., 1., 1.]), lerp)

        all_frames = set()
        all_frames.update(set(rotation_data.keys()))
        all_frames.update(set(location_data.keys()))
        all_frames.update(set(scale_data.keys()))
        all_frames = sorted(list(all_frames))

        for frame in all_frames:
            t, r, s = apply_transform_to_keyframe(generate_transform_matrix(*transform), frame, rotation_data, rotation_interpolator,
                                                  location_data, location_interpolator, scale_data, scale_interpolator)
            if frame in rotation_data:
                rotation_data[frame] = r
            if frame in location_data:
                location_data[frame] = t
            if frame in scale_data:
                scale_data[frame] = s

        retval['rotation_quaternion'][bone_idx] = rotation_data
        retval['location'][bone_idx] = location_data
        retval['scale'][bone_idx] = scale_data
    return retval
