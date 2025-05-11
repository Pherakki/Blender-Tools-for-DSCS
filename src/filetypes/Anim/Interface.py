import itertools
import math
from .Binary import AnimFileBinary
from .Utils import categorise_channels
from .Utils import ChunkBuilder
from .Utils import interpolate_anim_tracks, lerp, slerp
import numpy as np


def iter_bitvector(uint8_vector):
    for elem in uint8_vector:
        for bit_index in range(7, -1, -1):
            yield (elem >> bit_index) & 1


def chunk_bitvector(uint8_vector, chunksize):
    total_bits = len(uint8_vector)*8
    chunk_count = (total_bits) // chunksize
    remainder = total_bits - (chunk_count*chunksize)
    bitvector_iterator = iter_bitvector(uint8_vector)
    for _ in range(chunk_count):
        yield [next(bitvector_iterator) for _ in range(chunksize)]
    yield [next(bitvector_iterator) for _ in range(remainder)]


class AnimFile:
    def __init__(self):
        self.playback_rate       = 30.
        self.bone_count          = 0
        self.float_channel_count = 0
        self.bone_blend_factors          = []
        self.float_channel_blend_factors = []
        
        self.rotations = {}
        self.positions = {}
        self.scales    = {}
        self.float_channels = {}
        
    @classmethod
    def from_file(cls, path):
        binary = AnimFileBinary()
        binary.read(path)

        return cls.from_binary(binary)

    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        # Only need to take the playback rate; duration can be calculated from this and the total number of frames
        instance.playback_rate       = binary.playback_rate
        instance.bone_count          = binary.bone_count
        instance.float_channel_count = binary.float_channel_count
        instance.bone_blend_factors          = binary.bone_masks
        instance.float_channel_blend_factors = binary.float_channel_masks
        
        # Set up the data holder variables
        for idx in range(binary.bone_count):
            instance.rotations[idx] = {}
            instance.positions[idx] = {}
            instance.scales[idx] = {}
        for idx in range(max((binary.float_channel_count, *[i+1 for i in binary.static_float_channel_idxs], *[i+1 for i in binary.animated_float_channel_idxs]))):
            instance.float_channels[idx] = {}

        # Get the bits that are constant throughout the animation
        for bone_idx, rotation in zip(binary.static_rotation_idxs, binary.static_rotations):
            instance.rotations[bone_idx][0] = rotation
        for bone_idx, location in zip(binary.static_location_idxs, binary.static_locations):
            instance.positions[bone_idx][0] = location
        for bone_idx, scale in zip(binary.static_scale_idxs, binary.static_scales):
            instance.scales[bone_idx][0] = scale
        
        for channel_idx, channel_data in zip(binary.static_float_channel_idxs, binary.static_float_channels):
            instance.float_channels[channel_idx][0] = channel_data

        # Now add in the rotations, locations, and scales that change throughout the animation
        prev_frame = 0
        for chunk_idx, keyframe_chunk in enumerate(binary.keyframe_chunks):
            # Each keyframe chunk begins with a single frame
            current_frame = keyframe_chunk.keyframe_start
            if chunk_idx > 0:
                while prev_frame > current_frame:
                    current_frame += 0x10000
            for bone_idx, value in zip(binary.animated_rotation_idxs, keyframe_chunk.frame_0_rotations):
                instance.rotations[bone_idx][current_frame] = value
            for bone_idx, value in zip(binary.animated_location_idxs, keyframe_chunk.frame_0_locations):
                instance.positions[bone_idx][current_frame] = value
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
                keyframe_indices = chunk_bitvector(keyframe_chunk.keyframes_in_use, nframes)
            else:
                keyframe_indices = []

            rotations      = iter(keyframe_chunk.keyframed_rotations)
            positions      = iter(keyframe_chunk.keyframed_locations)
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
                values = itertools.islice(positions, len(frame_indices))  # Pop the next num_frames locations
                for frame, value in zip(frame_indices, values):
                    instance.positions[bone_idx][frame] = value
            # Scales
            for bone_idx, indices in zip(binary.animated_scale_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(scales, len(frame_indices))  # Pop the next num_frames scales
                for frame, value in zip(frame_indices, values):
                    instance.scales[bone_idx][frame] = value
            # Float channels
            for channel_idx, indices in zip(binary.animated_float_channel_idxs, keyframe_indices):
                frame_indices = [j + current_frame + 1 for j, elem in enumerate(indices) if elem == 1]
                values = itertools.islice(float_channels, len(frame_indices))  # Pop the next num_frames float channel data
                for frame, value in zip(frame_indices, values):
                    instance.float_channels[channel_idx][frame] = value

            # We should now have consumed all the keyframe bitvectors, so let's just check that is the case...
            # If any masks are left over, they should just be padding bits required to fill their containing byte
            for indices in keyframe_indices:
                assert all([item == 0 for item in indices]), f"Leftover keyframes bitvector was not padding: {indices}."

            prev_frame = current_frame

        # Recover quaternion signs lost during compression
        for bone_idx, rotations in instance.rotations.items():
            instance.rotations[bone_idx] = match_quat_signs_in_dict(instance.rotations[bone_idx])

        return instance

    def to_file(self, path, max_chunk_size=0x4000):
        binary = self.to_binary(max_chunk_size)
        binary.write(path)

    def to_binary(self, max_chunk_size=0x4000):
        binary = AnimFileBinary()
        static_positions, animated_positions = categorise_channels(self.positions)
        static_rotations, animated_rotations = categorise_channels(self.rotations)
        static_scales,    animated_scales    = categorise_channels(self.scales)
        static_fcs,       animated_fcs       = categorise_channels(self.float_channels)
        
        unused_bones = set(range(self.bone_count))
        unused_bones -= set(static_positions)
        unused_bones -= set(static_rotations)
        unused_bones -= set(static_scales)
        unused_bones -= set(animated_positions)
        unused_bones -= set(animated_rotations)
        unused_bones -= set(animated_scales)
        unused_bones = sorted(unused_bones)
        
        unused_float_channels = set(range(self.float_channel_count))
        unused_float_channels -= set(static_fcs)
        unused_float_channels -= set(animated_fcs)
        unused_float_channels = sorted(unused_float_channels)   
        
  
        # Sort out header variables    
        binary.static_locations_count     = len(static_positions)
        binary.static_rotations_count     = len(static_rotations)
        binary.static_scales_count        = len(static_scales)
        binary.static_float_channel_count = len(static_fcs)
        binary.static_location_idxs       = static_positions
        binary.static_rotation_idxs       = static_rotations
        binary.static_scale_idxs          = static_scales
        binary.static_float_channel_idxs  = static_fcs
        
        binary.animated_locations_count      = len(animated_positions)
        binary.animated_rotations_count      = len(animated_rotations)
        binary.animated_scales_count         = len(animated_scales)
        binary.animated_float_channel_count  = len(animated_fcs)
        binary.animated_location_idxs        = animated_positions
        binary.animated_rotation_idxs        = animated_rotations
        binary.animated_scale_idxs           = animated_scales
        binary.animated_float_channel_idxs   = animated_fcs
                
        # Dump static animations
        binary.static_locations      = [list(self.positions[k].values())[0]      for k in static_positions]
        binary.static_rotations      = [list(self.rotations[k].values())[0]      for k in static_rotations]
        binary.static_scales         = [list(self.scales   [k].values())[0]      for k in static_scales]
        binary.static_float_channels = [list(self.float_channels[k].values())[0] for k in static_fcs]
        
        # Identify max keyframe
        max_pos_kf = max((max(self.positions     [idx]) for idx in animated_positions), default=0)
        max_rot_kf = max((max(self.rotations     [idx]) for idx in animated_rotations), default=0)
        max_scl_kf = max((max(self.scales        [idx]) for idx in animated_scales),    default=0)
        max_fcs_kf = max((max(self.float_channels[idx]) for idx in animated_fcs),       default=0)
        max_kf = max((max_pos_kf, max_rot_kf, max_scl_kf, max_fcs_kf))
        
        # Finish filling out the header
        binary.playback_rate           = self.playback_rate
        binary.animation_duration      = max_kf / binary.playback_rate
        binary.frame_count             = (max_kf + 1) & 0xFFFF
        binary.keyframe_chunk_count    = 1
        binary.max_keyframe_chunk_size = max_chunk_size
        binary.padding_0x26            = 0
        binary.bone_count              = self.bone_count
        binary.float_channel_count     = self.float_channel_count

        
        binary.bone_masks          = self.bone_blend_factors
        binary.float_channel_masks = self.float_channel_blend_factors
        
        # Calculate the offsets in order to figure out how much the max chunk
        # size gets reduced by the header.
        binary.calculate_offsets()
        
        # Now break the animation up into keyframe chunks.
        animated_position_kfs = [(list(self.positions     [id_].keys()), [np.array(p) for p in self.positions[id_].values()]) for id_ in animated_positions]
        animated_rotation_kfs = [(list(self.rotations     [id_].keys()), [np.array(p) for p in self.rotations[id_].values()]) for id_ in animated_rotations]
        animated_scales_kfs   = [(list(self.scales        [id_].keys()), [np.array(p) for p in self.scales   [id_].values()]) for id_ in animated_scales]
        animated_fcs_kfs      = [(list(self.float_channels[id_].keys()), list(self.float_channels[id_].values())) for id_ in animated_fcs]
        
        frame_idx = 0
        max_intermediate_kf_chunk_size = max_chunk_size - binary.keyframe_chunks_offsets_offset - 0x7F
        
        final_chunk = ChunkBuilder(max_intermediate_kf_chunk_size, max_kf,
                             interpolate_anim_tracks(max_kf, animated_position_kfs, lerp),
                             interpolate_anim_tracks(max_kf, animated_rotation_kfs, slerp),
                             interpolate_anim_tracks(max_kf, animated_scales_kfs,   lerp),
                             interpolate_anim_tracks(max_kf, animated_fcs_kfs,      lerp))
        final_chunk.concretize()
        
        final_chunk_size                    = final_chunk.kf_chunk.calc_size()
        final_chunk.kf_chunk.size           = 0
        final_chunk.kf_chunk.keyframe_count = 0
        
        max_intermediate_kf_chunk_size -= final_chunk_size
        
        chunk_idx = 0
        while frame_idx < max_kf:
            # Init the chunk with the interpolated frame 0 data.
            chunk = ChunkBuilder(max_intermediate_kf_chunk_size, frame_idx,
                                 interpolate_anim_tracks(frame_idx, animated_position_kfs, lerp),
                                 interpolate_anim_tracks(frame_idx, animated_rotation_kfs, slerp),
                                 interpolate_anim_tracks(frame_idx, animated_scales_kfs,   lerp),
                                 interpolate_anim_tracks(frame_idx, animated_fcs_kfs,      lerp))
            
            frame_idx += 1
            local_max = min(max_kf, frame_idx+128)
            while frame_idx < local_max:
                # This can definitely be optimised if it's a problem.
                if not chunk.try_expand_by_frame({cidx: self.positions[bidx][frame_idx]      for cidx, bidx in enumerate(animated_positions) if frame_idx in self.positions[bidx]}, 
                                                 {cidx: self.rotations[bidx][frame_idx]      for cidx, bidx in enumerate(animated_rotations) if frame_idx in self.rotations[bidx]}, 
                                                 {cidx: self.scales[bidx][frame_idx]         for cidx, bidx in enumerate(animated_scales   ) if frame_idx in self.scales[bidx]},
                                                 {cidx: self.float_channels[bidx][frame_idx] for cidx, bidx in enumerate(animated_fcs      ) if frame_idx in self.float_channels[bidx]}):
    
                    break
                frame_idx += 1
        
            chunk.concretize()
            chunk.kf_chunk.size = chunk.kf_chunk.calc_size() + final_chunk_size
            binary.keyframe_chunks.append(chunk.kf_chunk)
            chunk_idx += 1
        
        binary.keyframe_chunks.append(final_chunk.kf_chunk)
        binary.keyframe_chunk_count = len(binary.keyframe_chunks)
        
        # Finally, calculate all remaining offsets.
        binary.calculate_offsets()
        
        return binary



#######################
# SERIALIZATION UTILS #
#######################



#####################
# QUATERNION FIXERS #
#####################


def dot(x, y):
    return sum(xi*yi for xi, yi in zip(x, y))

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
