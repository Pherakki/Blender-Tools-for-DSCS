import numpy as np

from .Interpolation import lerp, slerp, produce_interpolation_method
from .Matrices import apply_transform_to_keyframe, generate_transform_matrix


def generate_reference_frames(pose_matrices, animation_data):
    result = []
    for bone_idx, matrix in enumerate(pose_matrices):
        anim_rotation = animation_data['rotation_quaternion'].get(bone_idx, {}).get(0, [1., 0., 0., 0.])
        anim_location = animation_data['location'].get(bone_idx, {}).get(0, [0., 0., 0.])
        anim_scale = animation_data['scale'].get(bone_idx, {}).get(0, [1., 1., 1.])

        anim_transform = generate_transform_matrix(anim_rotation, anim_location, anim_scale, WXYZ=True)

        total_transform = np.dot(anim_transform, matrix)

        result.append(total_transform)
    return result


def get_action_data(action, curve_defaults):
    animation_data = {'location': {},
                      'rotation_quaternion': {},
                      'scale': {}}

    groups = group_fcurves(action)
    for bone_name, group in groups.items():
        # Get whether any of the locations, rotations, and scales are animated; plus the f-curves for those
        # that are
        elements_used, bone_data = get_used_animation_elements(group)
        # For each set that is animated, interpolate missing keyframes for each component of the relevant vector
        # on each keyframe where at least one element is used
        for curve_type, isUsed in elements_used.items():
            if isUsed:
                curve_data = interpolate_missing_frame_elements(bone_data[curve_type], curve_defaults[curve_type], lerp)
                zipped_data = zip_vector_elements(curve_data)
                animation_data[curve_type][bone_name] = zipped_data
    return animation_data


def group_fcurves(action):
    """
    Group f-curves by data path. Returns a dictionary with bone names as keys, and a list of f-curves as values.
    Kinda unnecessary, but the original code was written using the groups of an action rather than fcurves of an action,
    so this function emulates the group class (as a dict) so minimal changes needed to be made to the rest of the code.
    This *should* all be refactored to be f-curve-centric rather than group-centric, but no point fixing something that
    isn't broken unless it becomes a problem. The appropriate change to this function would be to ensure that each
    group only contains locations, rotations, or scales.
    """
    res = {}
    for fcurve in action.fcurves:
        if fcurve.data_path[:10] == 'pose.bones':
            bone_name = fcurve.data_path.split('[')[1].split(']')[0][1:-1]
            if bone_name not in res:
                res[bone_name] = []
            res[bone_name].append(fcurve)
        else:
            print(f"WARNING: animation path '{fcurve.data_path}' was not exported.")
    return res


def get_used_animation_elements(group):
    """
    Summary
    -------
    Takes a list of f-curves and assigns the keyframe point co-ordinates in each f-curve to the appropriate transform
    and array index of a returned dictionary.

    The animation export module should probably be refactored so that the groups that get passed into this function
    are either locations, rotations, or scales, so that all three are not handled simultaneously, but rather by three
    separate function calls.

    Parameters
    ----------
    :parameters:
    group -- A list of Blender f-curve objects.

    Returns
    -------
    :returns:
    A two-element tuple:
    - The first element is a dictionary in the shape {'location': bool, 'rotation_quaternion': bool, 'scale': bool} that
      states whether any of the input f-curves are of any of those types
    - The second element is a dictionary in the shape
                {'location': {0: {}, 1: {}, 2: {}},
                 'rotation_quaternion': {0: {}, 1: {}, 2: {}, 3: {}},
                 'scale': {0: {}, 1: {}, 2: {}}},
      where the integers are the array indices of the appropriate f-curves. Each array index is also given a dictionary
      as above, which contains the frame index and the f-curve value as key-value pairs.
    """
    elements_used = {'location': False,
                     'rotation_quaternion': False,
                     'scale': False}

    bone_data = {'location': {0: {}, 1: {}, 2: {}},
                 'rotation_quaternion': {0: {}, 1: {}, 2: {}, 3: {}},
                 'scale': {0: {}, 1: {}, 2: {}}}
    for f_curve in group:
        curve_type = f_curve.data_path.split('.')[-1]
        curve_idx = f_curve.array_index
        elements_used[curve_type] = True
        bone_data[curve_type][curve_idx] = {k-1: v for k, v in [kfp.co for kfp in f_curve.keyframe_points]}

    return elements_used, bone_data


def get_all_required_frames(curve_data):
    """
    Returns all keys in a list of dictionaries as a sorted list of rounded integers plus the rounded-up final key,
    assuming all keys are floating-point values.
    """
    res = set()
    for dct in curve_data.values():
        iter_keys = tuple(dct.keys())
        for key in iter_keys:
            res.add(int(round(key)))
        res.add(int(np.ceil(iter_keys[-1])))
    return sorted(list(res))


def interpolate_missing_frame_elements(curve_data, default_values, interpolation_function):
    """
    DSCS requires animations to be stored as whole quaternions, locations, and scales.
    This function ensures that every passed f-curve has a value at every frame referenced by all f-curves - e.g. if
    a location has values at frame 30 on its X f-curve but not on its Y and Z f-curves, the Y and Z values at frame 30
    will be interpolated from the nearest frames on the Y and Z f-curves respectively and stored in the result.
    """
    # First get every frame required by the vector and which will be passed on to DSCS
    # The returned frames are integers, even if the input frames are floats, because DSCS only likes integer frames
    all_frame_idxs = get_all_required_frames(curve_data)
    for (component_idx, framedata), default_value in zip(curve_data.items(), default_values):
        # Get all the frames at which the curve has data
        component_frame_idxs = list(framedata.keys())
        # Produce a function that will return the value for the frame, based on how many frames are available
        interp_method = produce_interpolation_method(component_frame_idxs, framedata, default_value, interpolation_function)
        new_framedata = {}
        # Generate the DSCS-compatible data
        for frame_idx in all_frame_idxs:
            if frame_idx not in component_frame_idxs:
                new_framedata[frame_idx] = interp_method(frame_idx)
            else:
                new_framedata[frame_idx] = framedata[frame_idx]

        curve_data[component_idx] = new_framedata

    return curve_data


def zip_vector_elements(curve_data):
    """
    Takes n dictionaries in a list, with each dictionary containing the frame indices (as keys) and values (as values)
    of a single component of a vector. All dictionaries must have exactly the same keys (frame indices).
    Returns a single dictionary with the frame indices as keys, and the vector components for that frame stored in a
    list as the value for that key.
    """
    new_curve_data = {}
    elements = list(curve_data.values())
    for frame_idxs in zip(*[list(e.keys()) for e in elements]):
        for frame_idx in frame_idxs:
            assert frame_idx == frame_idxs[0]
        frame_idx = frame_idxs[0]
        new_curve_data[frame_idx] = np.array([e[frame_idx] for e in elements])
    return new_curve_data
