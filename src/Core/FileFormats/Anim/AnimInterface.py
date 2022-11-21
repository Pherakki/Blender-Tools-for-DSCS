import itertools
import math

from .AnimBinary import AnimBinary, KeyframeChunk
from ...serialization.BinaryTargets import OffsetTracker
from ....Utilities.Bits import chunk_bitvector
from ....Utilities.Math import roundup
from ....Utilities.Interpolation import lerp, slerp
from ....Utilities.Vector import dot


class AnimInterface:
    def __init__(self):
        self.playback_rate = None
        self.bone_count = None

        self.rotations      = {}
        self.locations      = {}
        self.scales         = {}
        self.float_channels = {}

    @classmethod
    def from_file(cls, path, sk):
        binary = AnimBinary(sk)
        binary.read(path)

        return cls.from_binary(binary)

    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        # Only need to take the playback rate; duration can be calculated from this and the total number of frames
        instance.playback_rate = binary.playback_rate
        instance.bone_count = binary.bone_count

        # Set up the data holder variables
        for idx in range(binary.bone_count):
            instance.rotations[idx] = {}
            instance.locations[idx] = {}
            instance.scales[idx] = {}
        for idx in range(binary.skel_binary_ref.float_channel_count):
            instance.float_channels[idx] = {}

        # Get the bits that are constant throughout the animation
        for bone_idx, rotation in zip(binary.static_rotation_idxs, binary.static_rotations):
            instance.rotations[bone_idx][0] = rotation
        for bone_idx, location in zip(binary.static_location_idxs, binary.static_locations):
            instance.locations[bone_idx][0] = location
        for bone_idx, scale in zip(binary.static_scale_idxs, binary.static_scales):
            instance.scales[bone_idx][0] = scale
        for channel_idx, channel_data in zip(binary.static_float_channel_idxs, binary.static_float_channels):
            instance.float_channels[channel_idx][0] = channel_data

        # Now add in the rotations, locations, and scales that change throughout the animation
        for keyframe_chunk in binary.keyframe_chunks:
            # Each keyframe chunk begins with a single frame
            current_frame = keyframe_chunk.keyframe_start
            for bone_idx, value in zip(binary.animated_rotation_idxs, keyframe_chunk.frame_0_rotations):
                instance.rotations[bone_idx][current_frame] = value
            for bone_idx, value in zip(binary.animated_location_idxs, keyframe_chunk.frame_0_locations):
                instance.locations[bone_idx][current_frame] = value
            for bone_idx, value in zip(binary.animated_scale_idxs, keyframe_chunk.frame_0_scales):
                instance.scales[bone_idx][current_frame] = value
            for channel_idx, value in zip(binary.animated_float_channel_idxs, keyframe_chunk.frame_0_float_channels):
                instance.float_channels[channel_idx][current_frame] = value

            # The keyframe rotations, locations, etc. for all bones are all concatenated together into one big list
            # per transform type.
            # The keyframes that use each transform are stored in a bit-vector with an equal length to the number of
            # frames. These bit-vectors are all concatenated together in one huge bit-vector, in the order
            # rotations->locations->scales->float_channels
            # Therefore, it's pretty reasonable to turn these lists of keyframe rotations, locations, etc.
            # into generators using the built-in 'iter' function or the 'chunks' function defined at the bottom of the
            # file.
            nframes = keyframe_chunk.keyframe_count
            if nframes != 0:
                # assert len(keyframe_chunk.keyframes_in_use)*8 % nframes == 0, \
                #     f"{len(keyframe_chunk.keyframes_in_use)*8} keyframes cannot be split into chunks of {nframes}."
                keyframe_indices = chunk_bitvector(keyframe_chunk.keyframes_in_use, nframes)
            else:
                keyframe_indices = []

            rotations      = iter(keyframe_chunk.keyframed_rotations)
            locations      = iter(keyframe_chunk.keyframed_locations)
            scales         = iter(keyframe_chunk.keyframed_scales)
            float_channels = iter(keyframe_chunk.keyframed_float_channels)

            # The benefit of doing this is that generators behave like a Queue. We can pop the next element off these
            # generators and never have to worry about keeping track of the state of each generator, because the
            # generator keeps track of it for us.
            # In this function, the bit-vector is chunked and labelled 'keyframe_indices'.
            # Schematically, the bit-vector might look like this: (annotated)
            #
            # <------------------ Rotations -------------------><------------- Locations --------------><-Scales->
            # <-Frames-><-Frames-><-Frames-><-Frames-><-Frames-><-Frames-><-Frames-><-Frames-><-Frames-><-Frames->
            # 0001101011000011010010101011111000010100101010001010111001010010101000000001101011100100101011111101
            #
            # In this case, the animation is 11 frames long (the number of 1s and 0s under each part annotated as
            # '<-Frames->'), and each part labelled "<-Frames->" corresponds to the frames attached to a single bone
            # index in the animated_<TYPE>_bone_idxs variables. For this example, there would be 5 bone indices in the
            # animated_rotations_bone_idxs, four in animated_locations_bone_idxs, and one in animated_scales_bone_idxs.
            #
            # Starting from the beginning, we see that there are 5 1s in the first section of 11 frames. This means
            # that we need to record the indices of these 1s (modulo 11, the number of frames) and then take the first
            # 5 elements from the big list of keyframe rotations. We then record these frame indices and rotation
            # values as the keyframe data (points on the 'f-curve') for whichever bone this first set of 11 frames
            # corresponds to. We continue iterating through this bit-vector by grabbing the next chunk of indices from
            # 'keyframe_indices', and we should consume the entire generator of rotation data after 5 keyframe_indices.
            # The next index chunk we grab should then correspond to location data, so we move onto the next for-loop
            # below, and so on for the scale data.
            # Rotations
            for bone_idx, indices in zip(binary.animated_rotation_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(rotations, len(frame_indices))  # Pop the next num_frames rotations
                for frame, value in zip(frame_indices, values):
                    instance.rotations[bone_idx][frame] = value
            # Locations
            for bone_idx, indices in zip(binary.animated_location_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(locations, len(frame_indices))  # Pop the next num_frames locations
                for frame, value in zip(frame_indices, values):
                    instance.locations[bone_idx][frame] = value
            # Scales
            for bone_idx, indices in zip(binary.animated_scale_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(scales, len(frame_indices))  # Pop the next num_frames scales
                for frame, value in zip(frame_indices, values):
                    instance.scales[bone_idx][frame] = value
            # Float channels
            for channel_idx, indices in zip(binary.animated_float_channel_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(float_channels, len(frame_indices))  # Pop the next num_frames user channel data
                for frame, value in zip(frame_indices, values):
                    instance.float_channels[channel_idx][frame] = value

            # We should now have consumed all the keyframe bitvectors, so let's just check that is the case...
            # If any masks are left over, they should just be padding bits required to fill their containing byte
            for indices in keyframe_indices:
                assert all([item == 0 for item in indices]), f"Leftover keyframes bitvector was not padding: {indices}."

        # Recover quaternion signs lost during compression
        for bone_idx, rotations in instance.rotations.items():
            instance.rotations[bone_idx] = match_quat_signs_in_dict(instance.rotations[bone_idx])

        return instance
#####################
# QUATERNION FIXERS #
#####################


def match_quat_signs_in_dict(dictquats):
    keys = list(dictquats.keys())
    quats = list(dictquats.values())
    if len(quats) > 0:
        to_return = [quats[0]]
        for quat in quats[1:]:
            to_return.append(match_quaternion_signs(to_return[-1], quat))
        return {key: value for key, value in zip(keys, to_return)}
    else:
        return dictquats


def match_quaternion_signs(comparison_quat, quat):
    dp = dot(comparison_quat, quat)
    sign = math.copysign(1, dp)

    return [sign * q for q in quat]
