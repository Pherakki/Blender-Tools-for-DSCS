import numpy as np
from ...Utilities.ActionDataRetrieval import get_action_data
from ...Utilities.Interpolation import produce_interpolation_method_dict, lerp, slerp


def export_animations(nla_tracks, model_data, strip_single_frame_transforms, required_transforms, out_transforms=None):
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

    for nla_track in nla_tracks:
        strips = nla_track.strips
        if len(strips) != 1:
            print(f"NLA track \'{nla_track.name}\' has {len(strips)} strips; must have one strip ONLY to export.")
            continue

        nla_strip = strips[0]

        animation_data = get_action_data(nla_strip.action, curve_defaults)
        # Normalise the smallest distance between frames to 1 to allow more accurate integerisation
        smallest_frame_delta = get_smallest_frame_delta(animation_data)
        stretch_frame_indices_by_factor(animation_data, 1./smallest_frame_delta)

        # Integerise any float frame indices
        for bone_idx, animation_bone_data in animation_data.items():
            for curve_type, default, interp_method in zip(['rotation_quaternion', 'location', 'scale'],
                                                          [curve_defaults['rotation_quaternion'], curve_defaults['location'], curve_defaults['scale']],
                                                          [slerp, lerp, lerp]):
                channel_data = animation_bone_data[curve_type]
                animation_data[bone_idx][curve_type] = integerise_frame_indices(channel_data, default, interp_method)

        ad = model_data.new_anim(nla_track.name)

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

        # Do this properly later
        ad.uv_data = {}
        curr_idx = 0
        while nla_strip.action.get(f"uv_data_frames_{curr_idx}") is not None:
            ad.uv_data[curr_idx] = {frame: value for frame, value in zip(nla_strip.action.get(f"uv_data_frames_{curr_idx}", []),
                                                                         nla_strip.action.get(f"uv_data_values_{curr_idx}", []))}
            curr_idx += 1


def fetch_subdata(data, bone_name, strip_single_frame_transforms, required_subtransforms, curve_defaults, out_transforms, fetch_string):
    subdata = data.get(fetch_string, {})
    if not len(subdata) and bone_name in required_subtransforms:
        subdata[fetch_string] = curve_defaults[fetch_string]
    elif len(subdata) == 1 and strip_single_frame_transforms:
        subdata = {}
        out_transforms[fetch_string].append(bone_name)
    return subdata


def get_smallest_frame_delta(animation_data):
    smallest_frame_delta = np.inf
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            frame_indices = np.array(list(curve_data.keys()))
            if len(frame_indices) < 2:
                continue
            min_diff = np.min(frame_indices[1:] - frame_indices[:-1])
            smallest_frame_delta = np.min((smallest_frame_delta, min_diff))
    if smallest_frame_delta == np.inf:
        smallest_frame_delta = 1.
    return smallest_frame_delta


def stretch_frame_indices_by_factor(animation_data, factor):
    for bone_name, group in animation_data.items():
        for curve_type, curve_data in group.items():
            # curve_data is a dict...
            # so take all the (index, value) pairs from it, wipe it, then we can re-populate it with the values at new
            # indices
            frame_data = list(curve_data.items())
            curve_data.clear()
            for idx, value in frame_data:
                curve_data[idx*factor] = value


def integerise_frame_indices(animation_channel, frame_default, interpolation_function, debug_output=False):
    """
    Integerise frame indices by rounding up all non-integer frames, and then interpolating between the two
    nearest-neighbour frames to each rounded-up frame using the input interpolation function.
    """
    if not len(animation_channel):
        return {}

    required_frame_indices = [int(np.ceil(idx)) for idx in animation_channel.keys()]
    equivalent_frame_indices = [key == frame for key, frame in zip(animation_channel.keys(), required_frame_indices)]

    # First frame must be 0
    if required_frame_indices[0] != 0:
        required_frame_indices.insert(0, 0)
    interpolation_function = produce_interpolation_method_dict(animation_channel, frame_default, interpolation_function, debug_output)

    return {frame: animation_channel[original_frame] if is_equivalent else interpolation_function(frame)
            for frame, original_frame, is_equivalent in zip(required_frame_indices,
                                                            animation_channel.keys(),
                                                            equivalent_frame_indices)}
