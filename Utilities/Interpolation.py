import numpy as np


def lerp(x, y, t):
    return (1-t)*x + t*y


def slerp(x, y, t):
    omega = np.arccos(np.dot(x, y))
    if omega == 0 or np.isnan(omega):
        return x
    term_1 = x * np.sin((1-t)*omega)
    term_2 = y * np.sin(t*omega)
    return (term_1 + term_2) / np.sin(omega)


def interpolate_keyframe(frame_idxs, frame_values, idx, interpolation_function):
    smaller_elements = [idx for idx in frame_idxs if idx < idx]
    next_smallest_frame = max(smaller_elements) if len(smaller_elements) else frame_idxs[0]
    larger_elements = [idx for idx in frame_idxs if idx > idx]
    next_largest_frame = min(larger_elements) if len(larger_elements) else frame_idxs[-1]

    if next_largest_frame == next_smallest_frame:
        t = 0  # Totally arbitrary, since the interpolation will be between two identical values
    else:
        t = (idx - next_smallest_frame) / (next_largest_frame - next_smallest_frame)

    # Should change lerp to the proper interpolation method
    min_value = frame_values[next_smallest_frame]
    max_value = frame_values[next_largest_frame]

    return interpolation_function(np.array(min_value), np.array(max_value), t)


def produce_interpolation_method(frame_idxs, frame_values, default_value, interpolation_function):
    """
    Returns an interpolation function dependant on the number of passed frames.
    """
    if len(frame_idxs) == 0:
        def interp_method(input_frame_idx):
            return default_value
    elif len(frame_idxs) == 1:
        value = frame_values[frame_idxs[0]]

        def interp_method(input_frame_idx):
            return value
    else:
        def interp_method(input_frame_idx):
            return interpolate_keyframe(frame_idxs, frame_values, input_frame_idx, interpolation_function)

    return interp_method


# Surely these can be unified with the above...
def interpolate_keyframe_dict(frames, idx, interpolation_function, debug_output=False):
    frame_idxs = list(frames.keys())
    smaller_elements = [fidx for fidx in frame_idxs if fidx < idx]
    next_smallest_frame = max(smaller_elements) if len(smaller_elements) else frame_idxs[0]
    larger_elements = [fidx for fidx in frame_idxs if fidx > idx]
    next_largest_frame = min(larger_elements) if len(larger_elements) else frame_idxs[-1]

    if next_largest_frame == next_smallest_frame:
        t = 0  # Totally arbitrary, since the interpolation will be between two identical values
    else:
        t = (idx - next_smallest_frame) / (next_largest_frame - next_smallest_frame)

    min_value = frames[next_smallest_frame]
    max_value = frames[next_largest_frame]

    if debug_output:
        print(">>>", next_smallest_frame, idx, next_largest_frame)
        print(">>>", "t", t)
        print(">>>", min_value, max_value)

    return interpolation_function(np.array(min_value), np.array(max_value), t)


def produce_interpolation_method_dict(frames, default_value, interpolation_function, debug_output=False):
    """
    Returns an interpolation function dependant on the number of passed frames.
    """
    if len(frames) == 0:
        def interp_method(input_frame_idx):
            return default_value
    elif len(frames) == 1:
        value = list(frames.values())[0]

        def interp_method(input_frame_idx):
            return value
    else:
        def interp_method(input_frame_idx):
            return interpolate_keyframe_dict(frames, input_frame_idx, interpolation_function, debug_output)

    return interp_method
