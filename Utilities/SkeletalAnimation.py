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


def shift_animation_to_reference_frame(reference_frames, animation_data):
    rotations = animation_data['rotation_quaternion']
    locations = animation_data['location']
    scales = animation_data['scale']

    retval = {'rotation_quaternion': {},
              'location': {},
              'scale': {}}
    for bone_idx, reference_frame in enumerate(reference_frames):
        rotation_data = rotations.get(bone_idx, {})
        location_data = locations.get(bone_idx, {})
        scale_data = scales.get(bone_idx, {})

        rotation_interpolator = produce_interpolation_method(list(rotation_data.keys()), list(rotation_data.values()),
                                                             np.array([1., 0., 0., 0.]), slerp)
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
            t, r, s = apply_transform_to_keyframe(reference_frame, frame, rotation_data, rotation_interpolator,
                                                  location_data, location_interpolator, scale_data, scale_interpolator)
            if frame in rotation_data:
                rotation_data[frame] = r
            if frame in location_data:
                location_data[frame] = t
            if frame in scale_data:
                scale_data[frame] = s

        # Check if you actually need to return this
        retval['rotation_quaternion'][bone_idx] = rotation_data
        retval['location'][bone_idx] = location_data
        retval['scale'][bone_idx] = scale_data
    return retval
