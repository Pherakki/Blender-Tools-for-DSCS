import copy
import numpy as np
from ...Utilities.ActionDataRetrieval import get_action_data
from ...Utilities.Interpolation import produce_interpolation_method_dict, lerp, slerp


def create_blank_anim(model_data, anim_name):
    ad = model_data.new_anim(anim_name)
    for bone_idx, bone_name in enumerate(model_data.skeleton.bone_names):
        ad.add_rotation_fcurve(bone_idx, [], [])
        ad.add_location_fcurve(bone_idx, [], [])
        ad.add_scale_fcurve(bone_idx, [], [])
    ad.uv_data = {}


def export_animations(nla_tracks, model_data, name_prefix, strip_single_frame_transforms, required_transforms, out_transforms=None,
                      interp_mode="Interpolate"):
    """
    Main entry point to the animation export functionality.

    This function gets called by the Export class and utilises the remaining functions in the
    BlenderIO/Export/ExportAnimation module.

    Creates an Animation instance in the input IntermediateFormat object ('model_data') for each NLA track in the
    animation data of the input armature.
    """

    curve_defaults = {'location': [0., 0., 0.],
                      'rotation_quaternion': [1., 0., 0., 0.],
                      'scale': [1., 1., 1.],
                      'rotation_euler': [0, 0, 0]}
    if required_transforms is None:
        required_transforms = {}
    if out_transforms is None:
        out_transforms = {'location': [],
                          'rotation_quaternion': [],
                          'scale': []}
    printout = True
    for nla_track in nla_tracks:
        strips = nla_track.strips
        if len(strips) != 1:
            print(f"NLA track \'{nla_track.name}\' has {len(strips)} strips; must have one strip ONLY to export.")
            continue

        if nla_track.name == "base": anim_name = name_prefix
        else:                        anim_name = name_prefix + "_" + nla_track.name
        ad = model_data.new_anim(anim_name)

        nla_strip = strips[0]
        if nla_strip.action is None:
            print(f"NLA track \'{nla_track.name}\' has no action on its strip; must have an action set to export.")
            continue

        # Get the shader uniform animations
        ad.uv_data = {}
        curr_idx = 0
        while nla_strip.action.get(f"uv_data_frames_{curr_idx}") is not None:
            ad.uv_data[curr_idx] = {frame: value for frame, value in zip(nla_strip.action.get(f"uv_data_frames_{curr_idx}", []),
                                                                         nla_strip.action.get(f"uv_data_values_{curr_idx}", []))}
            curr_idx += 1

        # Now prepare to integerise all animation frames
        animation_data = get_action_data(nla_strip.action, curve_defaults)
        animation_uv_data = ad.uv_data

        # Normalise the smallest distance between frames to 1 to allow more accurate integerisation
        smallest_frame_delta = get_smallest_frame_delta(animation_data, animation_uv_data)
        stretch_frame_indices_by_factor(animation_data, animation_uv_data, 1./smallest_frame_delta)

        # Integerise any float frame indices
        for bone_idx, animation_bone_data in animation_data.items():
            for curve_type, default, interp_method in zip(['rotation_quaternion', 'location', 'scale'],
                                                          [curve_defaults['rotation_quaternion'], curve_defaults['location'], curve_defaults['scale']],
                                                          [slerp, lerp, lerp]):
                channel_data = animation_bone_data[curve_type]
                if interp_mode == "Snap":
                    animation_data[bone_idx][curve_type] = snap_frame_indices_to_integers(channel_data)  # Makes wobbly animations for float frame indices
                elif interp_mode == "Interpolate":
                    animation_data[bone_idx][curve_type] = integerise_frame_indices(channel_data, default, interp_method)
                else:
                    raise ValueError(f"Unknown animation integerisation mode \'{interp_mode}\'.")
        for shader_channel_idx, channel_data in animation_uv_data.items():
            animation_uv_data[shader_channel_idx] = snap_frame_indices_to_integers(channel_data)

        fps = 24. / (nla_strip.scale * smallest_frame_delta)
        ad.playback_rate = fps

        required_rotations = required_transforms.get('rotation_quaternion', [])
        required_locations = required_transforms.get('location', [])
        required_scales = required_transforms.get('scale', [])
        for bone_idx, bone_name in enumerate(model_data.skeleton.bone_names):
            data = animation_data.get(bone_name, {})

            subdata = fetch_subdata(data, bone_name, strip_single_frame_transforms, required_rotations, curve_defaults, out_transforms, 'rotation_quaternion')
            ad.add_rotation_fcurve(bone_idx, list(subdata.keys()), list(subdata.values()))

            subdata = fetch_subdata(data, bone_name, strip_single_frame_transforms, required_locations, curve_defaults, out_transforms, 'location')
            ad.add_location_fcurve(bone_idx, list(subdata.keys()), list(subdata.values()))

            subdata = fetch_subdata(data, bone_name, strip_single_frame_transforms, required_scales, curve_defaults, out_transforms, 'scale')
            ad.add_scale_fcurve(bone_idx, list(subdata.keys()), list(subdata.values()))

        ad.uv_data = animation_uv_data


def fetch_subdata(data, bone_name, strip_single_frame_transforms, required_subtransforms, curve_defaults, out_transforms, fetch_string):
    subdata = data.get(fetch_string, {})
    if not len(subdata) and bone_name in required_subtransforms:
        subdata[fetch_string] = curve_defaults[fetch_string]
    elif len(subdata) == 1 and strip_single_frame_transforms:
        subdata = {}
        out_transforms[fetch_string].append(bone_name)
    return subdata


def get_max_keyframe(animation_data, animation_uv_data):
    max_frame = 0.
    # First do animation data
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            frame_indices = np.array(list(curve_data.keys()))
            if len(frame_indices) < 2:
                continue
            max_frame = max(max(frame_indices), max_frame)

    # Now do shader channel data
    for shader_channel_idx, curve_data in animation_uv_data.items():
        frame_indices = np.array(list(curve_data.keys()))
        if len(frame_indices) < 2:
            continue
        max_frame = max(max(frame_indices), max_frame)
    return max_frame


def get_all_diffable_keyframes(animation_data, animation_uv_data):
    keyframes = []
    # First do animation data
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            frame_indices = np.array(list(curve_data.keys()))
            if len(frame_indices) < 2:
                continue
            keyframes.append(frame_indices)

    # Now do shader channel data
    for shader_channel_idx, curve_data in animation_uv_data.items():
        frame_indices = np.array(list(curve_data.keys()))
        if len(frame_indices) < 2:
            continue
        keyframes.append(frame_indices)
    return keyframes


def get_frame_indices_stretch_factor(all_keyframes, tol, max_n):
    # This isn't perfect: Step 1 will blow up to max_n if tol is too strict
    # To fix this, need to figure out the correct tol / dynamic tol

    flat_keyframes = np.array([subitem for item in all_keyframes for subitem in item])
    if not len(flat_keyframes):
        return 1.

    # Step 1: Get all keyframes within a certain frame bucket
    total_product = 1.
    converged = False
    differences = [(keyframes[1:] - keyframes[:-1]) for keyframes in all_keyframes]
    differences = np.array([subitem for item in differences for subitem in item])
    while not converged:
        converged = True
        fdifferences = differences * total_product
        errors = np.abs(fdifferences - np.around(fdifferences))
        for smallest_difference in sorted(errors):
            if smallest_difference > tol:
                converged = False
                break

        if not converged:
            candidate_product = total_product * (1 / smallest_difference)
            if candidate_product > max_n:
                converged = True
                total_product = max_n
            else:
                total_product = candidate_product


    # Step 2: Optimise the value of N
    # Equation is i = xN
    # Can solve for N by calculating N = (i . x) / (x . x)
    new_keyframes = np.around(flat_keyframes * total_product)
    fac_1 = np.dot(flat_keyframes, new_keyframes)
    fac_2 = np.dot(flat_keyframes, flat_keyframes)

    end_result = fac_1 / fac_2
    return end_result

def get_smallest_frame_delta(animation_data, animation_uv_data):
    smallest_frame_delta = np.inf

    # First do animation data
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            frame_indices = np.array(list(curve_data.keys()))
            if len(frame_indices) < 2:
                continue
            min_diff = np.min(frame_indices[1:] - frame_indices[:-1])
            smallest_frame_delta = np.min((smallest_frame_delta, min_diff))

    # Now do shader channel data
    for shader_channel_idx, curve_data in animation_uv_data.items():
        frame_indices = np.array(list(curve_data.keys()))
        if len(frame_indices) < 2:
            continue
        min_diff = np.min(frame_indices[1:] - frame_indices[:-1])
        smallest_frame_delta = np.min((smallest_frame_delta, min_diff))

    # Return
    if smallest_frame_delta == np.inf:
        smallest_frame_delta = 1.
    return smallest_frame_delta


def stretch_frame_indices_by_factor(animation_data, animation_uv_data, factor):
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            # curve_data is a dict...
            # so take all the (index, value) pairs from it, wipe it, then we can re-populate it with the values at new
            # indices
            frame_data = list(curve_data.items())
            curve_data.clear()
            for idx, value in frame_data:
                curve_data[idx*factor] = value
    for shader_channel_idx, curve_data in animation_uv_data.items():
        frame_data = list(curve_data.items())
        curve_data.clear()
        for idx, value in frame_data:
            curve_data[idx * factor] = value


def snap_frame_indices_to_integers(animation_channel):
    return {int(key): value for key, value in animation_channel.items()}


def integerise_frame_indices(animation_channel, frame_default, interpolation_function, debug_output=False):
    """
    Integerise frame indices by rounding up all non-integer frames, and then interpolating between the two
    nearest-neighbour frames to each rounded-up frame using the input interpolation function.
    BUGGED: consider the indices & values [0, 1, 20.01, 21.01]: [0, 0, 0, 1]...
    Going to interpolate to ~[0, 0, .99, 1]
    """
    if not len(animation_channel):
        return {}

    animation_channel_cpy = copy.deepcopy(animation_channel)
    for key in list(animation_channel_cpy.keys()):
        if key < 0:
            val = animation_channel_cpy.pop(key)
            if 0 not in animation_channel_cpy:
                animation_channel_cpy[0] = val

    required_frame_indices = [int(round(idx)) for idx in animation_channel_cpy.keys() if int(round(idx)) >= 0]

    # First frame must be 0
    if required_frame_indices[0] != 0:
        required_frame_indices.insert(0, 0)

    # # Add a capstone keyframe
    # largest_idx = int(np.ceil(list(animation_channel_cpy.keys())[-1]))
    # if largest_idx < 0:
    #     largest_idx = 0
    # if required_frame_indices[-1] != largest_idx:
    #    required_frame_indices.append(largest_idx)
    interpolation_function = produce_interpolation_method_dict(animation_channel_cpy, frame_default, interpolation_function, debug_output)

    return {frame: interpolation_function(frame) for frame in required_frame_indices}
