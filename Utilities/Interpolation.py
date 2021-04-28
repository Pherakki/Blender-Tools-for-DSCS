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
    next_smallest_element_idx = max(smaller_elements) if len(smaller_elements) else frame_idxs[0]
    larger_elements = [idx for idx in frame_idxs if idx > idx]
    next_largest_element_idx = min(larger_elements) if len(larger_elements) else frame_idxs[-1]

    if next_largest_element_idx == next_smallest_element_idx:
        t = 0  # Totally arbitrary, since the interpolation will be between two identical values
    else:
        t = (idx - next_smallest_element_idx) / (next_largest_element_idx - next_smallest_element_idx)

    # Should change lerp to the proper interpolation method
    min_value = frame_values[next_smallest_element_idx]
    max_value = frame_values[next_largest_element_idx]

    return interpolation_function(min_value, max_value, t)


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
