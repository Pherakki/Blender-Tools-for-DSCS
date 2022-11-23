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
                values = itertools.islice(float_channels, len(frame_indices))  # Pop the next num_frames float channel data
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

    def to_file(self, path, sk, isBase):
        binary = self.to_binary(sk, isBase)
        binary.write(path)

    def to_binary(self, sk, isBase):
        # Determine how many frames are in the animation
        max_rotation_frames = max([max(keyframes.keys()) if len(keyframes) else 0 for keyframes in self.rotations.values()]) \
            if len(self.rotations) \
            else 0
        max_location_frames = max([max(keyframes.keys()) if len(keyframes) else 0 for keyframes in self.locations.values()]) \
            if len(self.locations) \
            else 0
        max_scales_frames = max([max(keyframes.keys()) if len(keyframes) else 0 for keyframes in self.scales.values()]) \
            if len(self.scales) \
            else 0
        max_float_channel_frames = max([max(keyframes.keys()) if len(keyframes) else 0 for keyframes in self.float_channels.values()]) \
            if len(self.float_channels) \
            else 0

        frame_count = int(max((max_rotation_frames, max_location_frames, max_scales_frames, max_float_channel_frames)))
        frame_count += 1

        # Find out how many bones there are
        max_rotation_bones = max(self.rotations.keys()) if len(self.rotations) else 0
        max_location_bones = max(self.locations.keys()) if len(self.locations) else 0
        max_scale_bones    = max(self.scales.keys())    if len(self.scales) else 0
        bone_count = max((max_rotation_bones, max_location_bones, max_scale_bones))

        # Find out how many float channels there are
        float_channel_count = max(self.float_channels) if len(self.float_channels) else 0

        # Start filling in the header
        binary = AnimBinary(sk)
        binary.animation_duration = (frame_count - 1) / self.playback_rate
        binary.playback_rate      = self.playback_rate
        binary.bone_count         = bone_count
        binary.frame_count        = frame_count
        binary.always_0x4000      = 0x4000

        # Time to figure out how to organise the keyframes...
        static_rots, anim_rots, unused_rots = split_keyframes_by_role(self.rotations)
        static_locs, anim_locs, unused_locs = split_keyframes_by_role(self.locations)
        static_scls, anim_scls, unused_scls = split_keyframes_by_role(self.scales)
        static_fchs, anim_fchs, unused_fchs = split_keyframes_by_role(self.float_channels)
        unused_bones = sorted(list(set(unused_rots).intersection(unused_locs).intersection(unused_scls)))

        # Sort the static bones into the correct order after adding malformed blend bones
        # Redundant?
        static_rots = {k: v for k, v in sorted(list(static_rots.items()), key=lambda x: x[0])}
        static_locs = {k: v for k, v in sorted(list(static_locs.items()), key=lambda x: x[0])}
        static_scls = {k: v for k, v in sorted(list(static_scls.items()), key=lambda x: x[0])}
        static_fchs = {k: v for k, v in sorted(list(static_fchs.items()), key=lambda x: x[0])}

        # Slap down the counts of the static and animated bones
        binary.static_rotations_count       = len(static_rots)
        binary.static_locations_count       = len(static_locs)
        binary.static_scales_count          = len(static_scls)
        binary.static_float_channel_count   = len(static_fchs)
        binary.animated_rotations_count     = len(anim_rots)
        binary.animated_locations_count     = len(anim_locs)
        binary.animated_scales_count        = len(anim_scls)
        binary.animated_float_channel_count = len(anim_fchs)
        binary.padding_0x26 = 0
        binary.animation_masks_size = 0  # Calculate later

        # Fill in section 1: Bone indices used by the relevant data sections
        binary.static_rotation_idxs        = list(static_rots.keys())
        binary.static_location_idxs        = list(static_locs.keys())
        binary.static_scale_idxs           = list(static_scls.keys())
        binary.static_float_channel_idxs   = list(static_fchs.keys())
        binary.animated_rotation_idxs      = list(anim_rots.keys())
        binary.animated_location_idxs      = list(anim_locs.keys())
        binary.animated_scale_idxs         = list(anim_scls.keys())
        binary.animated_float_channel_idxs = list(anim_fchs.keys())

        # Fill in sections 2-5: Rotations, locations, scales, float_channels
        binary.static_rotations      = list(static_rots.values())
        binary.static_locations      = list(static_locs.values())
        binary.static_scales         = list(static_scls.values())
        binary.static_float_channels = list(static_fchs.values())

        # Now for the really tough bit
        # It's time to figure out how to divvy up the keyframes into chunks
        chunk_holders = generate_keyframe_chunks(anim_rots, anim_locs, anim_scls, anim_fchs, frame_count)
        binary.keyframe_chunk_count = len(chunk_holders)
        binary.keyframe_chunks = [KeyframeChunk() for _ in range(binary.keyframe_chunk_count)]
        running_total = 0
        for kf, chunk in zip(binary.keyframe_chunks, chunk_holders):
            kf.keyframe_start = running_total
            kf.keyframe_count = chunk.contained_frames - 1
            running_total += chunk.contained_frames

        # Now do the masks...
        # If it's a base animation, or there are no unused channels, no need for masks...
        if isBase or (not len(unused_bones) and not len(unused_fchs)):
            binary.bone_masks = []
            binary.float_channel_masks = []
        else:
            # Now construct the unused bone mask
            bone_mask = [-1 for _ in range(binary.bone_count)]
            for bone_idx in unused_bones:
                bone_mask[bone_idx] = 0
            binary.bone_masks = bone_mask

            # Now do the unused shader uniform mask
            float_channels_mask = [-1 for _ in range(float_channel_count)]
            for float_channel_idx in unused_fchs:
                float_channels_mask[float_channel_idx] = 0
            binary.float_channel_masks = float_channels_mask

        # Finally, go back and do KF chunk pointers
        final_chunk_size = chunk_holders[-1].total_size
        for kf, chunk in zip(binary.keyframe_chunks, chunk_holders[:-1]):
            kf.size = chunk.total_size + final_chunk_size
        binary.keyframe_chunks[-1].size = 0

        # Then finally dump the chunks themselves
        for chunk, kf_chunk in zip(chunk_holders, binary.keyframe_chunks):
            # Header variables
            kf_chunk.frame_0_rotations_bytecount = chunk.initial_rotation_bytes
            kf_chunk.frame_0_locations_bytecount = chunk.initial_location_bytes
            kf_chunk.frame_0_scales_bytecount = chunk.initial_scale_bytes
            kf_chunk.frame_0_float_channels_bytecount = chunk.initial_uvc_bytes
            kf_chunk.keyframed_rotations_bytecount = chunk.later_rotation_bytes
            kf_chunk.keyframed_locations_bytecount = chunk.later_location_bytes
            kf_chunk.keyframed_scales_bytecount = chunk.later_scale_bytes
            kf_chunk.keyframed_float_channels_bytecount = chunk.later_uvc_bytes

            # Data holders
            kf_chunk.frame_0_rotations = chunk.initial_rotations
            kf_chunk.frame_0_locations = chunk.initial_locations
            kf_chunk.frame_0_scales = chunk.initial_scales
            kf_chunk.frame_0_float_channels = chunk.initial_uvcs
            kf_chunk.keyframes_in_use = chunk.total_bitvector
            kf_chunk.keyframed_rotations = flatten_list(chunk.later_rotations)
            kf_chunk.keyframed_locations = flatten_list(chunk.later_locations)
            kf_chunk.keyframed_scales = flatten_list(chunk.later_scales)
            kf_chunk.keyframed_float_channels = flatten_list(chunk.later_uvcs)

        # Do offsets
        ot = OffsetTracker()
        ot.rw_obj_method(binary, binary.rw_header)
        ot.rw_obj_method(binary, binary.rw_bone_idx_lists)
        binary.static_rotations_offset = ot.tell() if len(binary.static_rotations) else 0
        ot.rw_obj_method(binary, binary.rw_static_rotations)
        binary.static_locations_offset = ot.tell() if len(binary.static_locations) else 0
        ot.rw_obj_method(binary, binary.rw_static_locations)
        binary.static_scales_offset = ot.tell() if len(binary.static_scales) else 0
        ot.rw_obj_method(binary, binary.rw_static_scales)
        binary.static_float_channels_offset = ot.tell() if len(binary.static_float_channels) else 0
        ot.rw_obj_method(binary, binary.rw_static_float_channels)
        binary.keyframe_chunks_offsets_offset = ot.tell() if len(binary.keyframe_chunks) else 0
        ot.rw_obj_method(binary, binary.rw_keyframe_chunk_offsets)
        binary.keyframe_chunks_counts_offset = ot.tell() if len(binary.keyframe_chunks) else 0
        ot.rw_obj_method(binary, binary.rw_keyframe_chunk_counts)
        binary.animation_masks_offset = ot.tell()
        binary.bone_mask_offset = ot.tell() if len(binary.bone_masks) or len(binary.float_channel_masks) else 0
        ot.rw_obj_method(binary, binary.rw_animation_masks)
        binary.animation_masks_size = ot.tell() - binary.bone_mask_offset
        keyframes_size = (binary.animated_rotations_count + binary.animated_locations_count + binary.animated_scales_count + binary.animated_float_channel_count) / 8
        for kf in binary.keyframe_chunks:
            kf.offset = ot.tell()
            ot.rw_obj_method(kf, kf.rw_data, keyframes_size)

        return binary


def flatten_list(lst):
    return [subitem for item in lst for subitem in item]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def split_keyframes_by_role(keyframe_set):
    statics = {}
    animated = {}
    unused = []

    for bone_idx, keyframes in keyframe_set.items():
        if len(keyframes) == 0:
            unused.append(bone_idx)
        elif len(keyframes) == 1:
            statics[bone_idx] = list(keyframes.values())[0]
        else:
            animated[bone_idx] = keyframes
    return statics, animated, unused

#########################################
# FUNCTIONS TO GENERATE KEYFRAME CHUNKS #
#########################################


def generate_keyframe_chunks(animated_rotations, animated_locations, animated_scales, animated_float_chs, frame_count):
    """
    This function has a very high bug potential...
    """
    # These lines create lists of length num_frames with None for frames with no data
    rotations = populate_frames(frame_count, animated_rotations)
    locations = populate_frames(frame_count, animated_locations)
    scales    = populate_frames(frame_count, animated_scales)
    float_chs = populate_frames(frame_count, animated_float_chs)

    # The above is done so that the frames can be easily chunked by this function:
    rotations, locations, scales, float_chs, chunksizes = adaptive_chunk_frames(rotations, locations, scales, float_chs, frame_count)

    # And now we can iterate through the chunks and strip out the None values, and save the results
    # We also might need to perform some interpolation inside these functions in order to satisfy the requirements of
    # the DSCS animation format
    # Also need to isolate the final frame in here for the same reasons
    rotation_keyframe_chunks_data, rotation_bitvector_data = strip_and_validate_all_bones(rotations, chunksizes, slerp)
    location_keyframe_chunks_data, location_bitvector_data = strip_and_validate_all_bones(locations, chunksizes, lerp)
    scale_keyframe_chunks_data, scale_bitvector_data       = strip_and_validate_all_bones(scales, chunksizes, lerp)
    float_ch_keyframe_chunks_data, float_ch_bitvector_data = strip_and_validate_all_bones(float_chs, chunksizes, lerp)

    # Now we can bundle all the chunks into a sequential list, ready for turning into KeyframeChunks instances
    chunk_data = [[{}, {}, {}, {}] for _ in range(len(chunksizes))]
    for bone_idx, rotation_chunks in rotation_keyframe_chunks_data.items():
        for i, rotation_data in enumerate(rotation_chunks):
            chunk_data[i][0][bone_idx] = rotation_data
    for bone_idx, location_chunks in location_keyframe_chunks_data.items():
        for i, location_data in enumerate(location_chunks):
            chunk_data[i][1][bone_idx] = location_data
    for bone_idx, scale_chunks in scale_keyframe_chunks_data.items():
        for i, scale_data in enumerate(scale_chunks):
            chunk_data[i][2][bone_idx] = scale_data
    for channel_idx, uvc_chunks in float_ch_keyframe_chunks_data.items():
        for i, uvc_data in enumerate(uvc_chunks):
            chunk_data[i][3][channel_idx] = uvc_data

    # We also need the final elements of each animation
    final_rotations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_rotations.items()}
    final_locations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_locations.items()}
    final_scales    = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_scales.items()}
    final_float_chs = {channel_id: [list(data.values())[-1]] for channel_id, data in animated_float_chs.items()}

    chunks = []
    if frame_count > 1:
        for chunk_idx, (chunk_datum, chunksize) in enumerate(zip(chunk_data[:-1], chunksizes[:-1])):
            r_bitvecs = [rotation_bitvector_data[bone_id][chunk_idx] for bone_id in rotation_bitvector_data]
            l_bitvecs = [location_bitvector_data[bone_id][chunk_idx] for bone_id in location_bitvector_data]
            s_bitvecs = [scale_bitvector_data[bone_id][chunk_idx] for bone_id in scale_bitvector_data]
            u_bitvecs = [float_ch_bitvector_data[channel_id][chunk_idx] for channel_id in float_ch_bitvector_data]
            if len(r_bitvecs):
                assert chunksize == len(r_bitvecs[0])
            if len(l_bitvecs):
                assert chunksize == len(l_bitvecs[0])
            if len(s_bitvecs):
                assert chunksize == len(s_bitvecs[0])
            if len(u_bitvecs):
                assert chunksize == len(u_bitvecs[0])
            chunks.append(ChunkHolder(*chunk_datum, r_bitvecs, l_bitvecs, s_bitvecs, u_bitvecs, chunksize))

        pen_r_bitvecs = [rotation_bitvector_data[bone_id][-1] for bone_id in rotation_bitvector_data]
        pen_l_bitvecs = [location_bitvector_data[bone_id][-1] for bone_id in location_bitvector_data]
        pen_s_bitvecs = [scale_bitvector_data[bone_id][-1] for bone_id in scale_bitvector_data]
        pen_u_bitvecs = [float_ch_bitvector_data[channel_id][-1] for channel_id in float_ch_bitvector_data]

        chunks.append(ChunkHolder.init_penultimate_chunk(*chunk_data[-1],
                                                         pen_r_bitvecs, pen_l_bitvecs, pen_s_bitvecs, pen_u_bitvecs,
                                                         chunksizes[-1]))
    chunks.append(ChunkHolder(final_rotations, final_locations, final_scales, final_float_chs,
                              [1 for _ in final_rotations], [1 for _ in final_locations],
                              [1 for _ in final_scales], [1 for _ in final_float_chs],
                              1))

    return chunks


def populate_frames(frame_count, animation_data):
    """
    Takes a dictionary of frame_id: data pairs and produces a list of length frame_count with data inserted at indices
    specified by frame_id, and None everywhere else.
    """
    frame_data = {}
    for bone_id, keyframes in animation_data.items():
        frame_data[bone_id] = [None] * frame_count
        for frame_id, frame_value in keyframes.items():
            frame_data[bone_id][frame_id] = frame_value
    return frame_data

def adaptive_chunk_frames(rotation_frames, location_frames, scale_frames, float_ch_frames, frame_count):
    cuts = [0]

    # Calculate how many bytes each frame will cost to store
    rotation_costs = bytecost_per_frame(rotation_frames, frame_count, 6)
    location_costs = bytecost_per_frame(location_frames, frame_count, 12)
    scale_costs    = bytecost_per_frame(scale_frames, frame_count, 12)
    float_ch_costs = bytecost_per_frame(float_ch_frames, frame_count, 4)
    bone_frame_costs = [sum(frames) for frames in zip(rotation_costs, location_costs, scale_costs)]

    # Calculate how many bits need to get added to the bitvector per frame
    # Do this by determining how many bones are kept track of per animation type
    # and adding one bit per bone, if any bones are animated at all
    include_rotation_bitvector = sum(rotation_costs) != 0
    rotation_bitvector_price   = len(rotation_frames) * include_rotation_bitvector
    include_location_bitvector = sum(location_costs) != 0
    location_bitvector_price   = len(location_frames) * include_location_bitvector
    include_scale_bitvector    = sum(scale_costs)    != 0
    scale_bitvector_price      = len(scale_frames)    * include_scale_bitvector
    include_float_ch_bitvector = sum(float_ch_costs) != 0
    float_ch_bitvector_price   = len(float_ch_costs)  * include_float_ch_bitvector

    bitvector_frame_cost = rotation_bitvector_price + location_bitvector_price + scale_bitvector_price + float_ch_bitvector_price

    # The rot + loc + scale gets rounded up to nearest 4
    first_frame_price = roundup(bone_frame_costs[0], 4)
    first_frame_price += float_ch_costs[0]
    # This is the cost of a chunk containing only the first-frame data. Includes a 0x10-byte header + round up to 0x10
    additional_cost   = roundup(first_frame_price + 16, 16)
    bitvector_bitcost = 0
    maximum_cost = 0x4000 - additional_cost  # Presumably, need to subtract off the cost of the final frame chunk: the first frame price?
    maximum_cost = 0x2000
    # Skip the first frame, we already know how much that one costs
    for frame_idx in range(1, frame_count):
        # Probably needs fixing...
        animation_cost = sum(bone_frame_costs[cuts[-1] + 1:frame_idx + 1])
        animation_cost += sum(float_ch_costs[cuts[-1] + 1:frame_idx + 1])
        bitvector_bitcost += bitvector_frame_cost
        bitvector_cost = roundup(bitvector_bitcost, 8) // 8

        total_chunk_cost = roundup(roundup(16 + first_frame_price + bitvector_cost + animation_cost, 4), 16)

        exceeded_cost = total_chunk_cost >= maximum_cost
        at_maximum_frames = frame_idx - cuts[-1] == 130  # Not sure if this limitation is necessary, implements 128 per chunk
        if exceeded_cost or at_maximum_frames:
            if frame_idx - 1 == cuts[-1]:
                raise ValueError(f"Frame {frame_idx} too expensive to convert to DSCS frame "
                                 f"[requires {total_chunk_cost}/{maximum_cost} available bytes]. "
                                 f"Reduce number of animated bones in this frame to export.")
            cuts.append(frame_idx - 1)
            # Don't count this frame, since it will be replaced by the maximum cost as the new "frame 0" of the new
            # chunk
            bitvector_bitcost = 0
    cuts.append(frame_count)

    rotation_chunks = {}
    location_chunks = {}
    scale_chunks = {}
    float_ch_chunks = {}
    chunksizes = [ed - st for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in rotation_frames.items():
        rotation_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in location_frames.items():
        location_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in scale_frames.items():
        scale_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for channel_idx, data in float_ch_frames.items():
        float_ch_chunks[channel_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]

    return rotation_chunks, location_chunks, scale_chunks, float_ch_chunks, chunksizes


def bytecost_per_frame(frames, num_frames, cost):
    """
    Count the number of bytes required to store each frame in a series of frames organised in a nested dict as
    {bone_idxs: {frame_idxs: value}}
    """
    costs = [0] * num_frames
    for bone_id, data in frames.items():
        for frame_idx, value in enumerate(data):
            if value is not None:
                costs[frame_idx] += cost
    return costs


def strip_and_validate_all_bones(frame_data, chunksizes, interpolation_method):
    keyframe_chunks_data = {}
    bitvector_data = {}
    for i, (bone_idx, chunks) in enumerate(frame_data.items()):
        reduced_chunks, bitvectors = strip_and_validate(chunks, chunksizes, interpolation_method)
        keyframe_chunks_data[bone_idx] = reduced_chunks
        bitvector_data[bone_idx] = bitvectors
    for (bone_idx, bone_data), bitvectors in zip(keyframe_chunks_data.items(), bitvector_data.values()):
        for subdata, bitvector in zip(bone_data, bitvectors):
            assert len(subdata) == sum([elem == '1' for elem in bitvector]), f"{bone_idx}"
    return keyframe_chunks_data, bitvector_data


def strip_and_validate(keyframes, chunksizes, method):
    reduced_chunks, bitvectors, initial_values, final_values = generate_keyframe_chunks_entry_data(keyframes)
    already_handled_chunks = []

    for chunk_idx, (reduced_chunk, bitvector, initial_pair, final_pair) in enumerate(
            zip(reduced_chunks, bitvectors, initial_values, final_values)):
        if chunk_idx in already_handled_chunks:
            continue
        skipped_chunks = []
        # This should *never* be the case for the first chunk
        # Every chunk must have data in its first frame, so check if what we have does...
        if bitvector[0] == 0:
            if chunk_idx == 0:
                assert 0, "Invalid input data to animation: first frame has no data."
            # If it doesn't, we'll need to interpolate it using the closest data in the past (from the previous chunk)
            # and the closest data in the future (an arbitrary number of chunks away)
            # Get the previous chunk so we can use that as the first point to interpolate from
            interp_origin = final_values[chunk_idx - 1]
            # And now get the next piece of data, keeping track of any chunks that are empty and must also be
            # interpolated for later
            interp_end = None
            for i, (iter_initial_pair, bv) in enumerate(zip(initial_values[chunk_idx:], bitvectors[chunk_idx:])):
                # If the chunk doesn't have an initial value, we need to interpolate that value
                # So keep track of the chunk if we need to interpolate its first value
                if bv[0] == 0:
                    skipped_chunks.append(chunk_idx + i)
                # If the chunk contains *some* data, stop here because we've found the next non-zero value
                # We'll carry this value forward and use it as the end point of the interpolation.
                if iter_initial_pair is not None:
                    interp_end = iter_initial_pair
                    break
            if interp_end is None:
                interp_end = interp_origin

            # Now, for every chunk we've identified as missing a first frame in the range where the data we've picked
            # out is applicable, do that generation
            interp_start_data, interp_start_frame = interp_origin
            interp_end_data, interp_end_frame = interp_end
            absolute_start_frame_index = sum(chunksizes[:(chunk_idx - 1)]) + interp_start_frame
            absolute_end_frame_index = sum(chunksizes[:skipped_chunks[-1]]) + interp_end_frame
            for curr_skipped_chunk_idx, skipped_chunk_idx in enumerate(skipped_chunks):
                interpolation_index = sum(chunksizes[:skipped_chunk_idx])
                t = ((interpolation_index - absolute_start_frame_index) / (
                            absolute_end_frame_index - absolute_start_frame_index))
                # Interpolate
                interpolated_frame_data = method(interp_start_data, interp_end_data, t)  # Needs to be lerp for pos, slerp for quat
                # Make relevant assignments to register the interpolated frame
                bitvectors[skipped_chunk_idx] = '1' + bitvectors[skipped_chunk_idx][1:]
                reduced_chunks[skipped_chunk_idx] = [interpolated_frame_data, *reduced_chunks[skipped_chunk_idx]]
                already_handled_chunks.extend(skipped_chunks)

    return reduced_chunks, bitvectors


def generate_keyframe_chunks_entry_data(keyframes):
    reduced_chunks = []
    bitvectors = []
    initial_values = []
    final_values = []
    for chunk in keyframes:
        reduced_chunk, bitvector, indices = boil_down_chunk(chunk)
        if len(reduced_chunk):
            initial_pair = (reduced_chunk[0], indices[0])
            final_pair = (reduced_chunk[-1], indices[-1])
        else:
            initial_pair = None
            final_pair = None
        reduced_chunks.append(reduced_chunk)
        bitvectors.append(bitvector)
        initial_values.append(initial_pair)
        final_values.append(final_pair)
    return reduced_chunks, bitvectors, initial_values, final_values


def boil_down_chunk(chunk):
    bitvector = ''
    reduced_chunk = []
    indices = []
    for j, value in enumerate(chunk):
        if value is None:
            bitvector += 0
        else:
            bitvector += 1
            reduced_chunk.append(value)
            indices.append(j)
    return reduced_chunk, bitvector, indices


class ChunkHolder:
    def __init__(self, rotations, locations, scales, uvcs,
                 rotation_bitvector, location_bitvector, scale_bitvector, uvc_bitvector,
                 contained_frames):
        rotations = list(rotations.values())
        locations = list(locations.values())
        scales = list(scales.values())
        uvcs = list(uvcs.values())

        bytes_read = 16
        self.initial_rotations = [sublist[0] for sublist in rotations]
        self.initial_locations = [sublist[0] for sublist in locations]
        self.initial_scales = [sublist[0] for sublist in scales]
        self.initial_uvcs = [sublist[0] for sublist in uvcs]

        self.initial_rotation_bytes = len(self.initial_rotations) * 6
        self.initial_location_bytes = len(self.initial_locations) * 12
        self.initial_scale_bytes = len(self.initial_scales) * 12
        self.initial_uvc_bytes = len(self.initial_uvcs) * 4
        bytes_read += self.initial_rotation_bytes
        bytes_read += self.initial_location_bytes
        bytes_read += self.initial_scale_bytes
        self.initial_scale_bytes += (4 - (bytes_read % 4)) % 4
        bytes_read += (4 - (bytes_read % 4)) % 4
        bytes_read += self.initial_uvc_bytes

        total_rotation_bitvector = rotation_bitvector[1:]
        total_location_bitvector = location_bitvector[1:]
        total_scale_bitvector = scale_bitvector[1:]
        total_uvc_bitvector = uvc_bitvector[1:]

        self.total_bitvector = total_rotation_bitvector + total_location_bitvector + total_scale_bitvector + total_uvc_bitvector
        remainder = (8 - (len(self.total_bitvector) % 8)) % 8
        self.total_bitvector += [0]*remainder

        packed_bitvector = [None]*(len(self.total_bitvector) // 8)
        for i, (a, b, c, d, e, f, g, h) in enumerate(chunks(self.total_bitvector, 8)):
            elem = a
            elem |= (b << 1)
            elem |= (c << 2)
            elem |= (d << 3)
            elem |= (e << 4)
            elem |= (f << 5)
            elem |= (g << 6)
            elem |= (h << 7)
            packed_bitvector[i] = elem.to_bytes(1, byteorder='little')
        self.total_bitvector = b''.join(packed_bitvector)

        self.bitvector_size = len(self.total_bitvector)
        bytes_read += self.bitvector_size

        self.later_rotations = [sublist[1:] for sublist in rotations]
        self.later_locations = [sublist[1:] for sublist in locations]
        self.later_scales = [sublist[1:] for sublist in scales]
        self.later_uvcs = [sublist[1:] for sublist in uvcs]

        self.later_rotation_bytes = sum([len(elem) for elem in self.later_rotations]) * 6
        self.later_location_bytes = sum([len(elem) for elem in self.later_locations]) * 12
        self.later_scale_bytes = sum([len(elem) for elem in self.later_scales]) * 12
        self.later_uvc_bytes = sum([len(elem) for elem in self.later_uvcs]) * 4
        bytes_read += self.later_rotation_bytes
        bytes_read += self.later_location_bytes
        bytes_read += self.later_scale_bytes
        self.later_scale_bytes += (4 - (bytes_read % 4)) % 4
        bytes_read += (4 - (bytes_read % 4)) % 4
        bytes_read += self.later_uvc_bytes

        self.total_size = self.initial_rotation_bytes + self.initial_location_bytes + \
                          self.initial_scale_bytes + self.initial_uvc_bytes + \
                          self.bitvector_size + \
                          self.later_rotation_bytes + self.later_location_bytes + \
                          self.later_scale_bytes + self.later_uvc_bytes + \
                          16  # 16 is for the header

        size_difference = (16 - (self.total_size % 16)) % 16
        assert size_difference % 4 == 0, "Something went horribly wrong - keyframe chunk not aligned to 4."
        dummy_floats_to_add = size_difference // 4
        self.later_uvcs.append([0.] * dummy_floats_to_add)
        self.later_uvc_bytes += size_difference

        # Recompute total size
        self.total_size = self.initial_rotation_bytes + self.initial_location_bytes + \
                          self.initial_scale_bytes + self.initial_uvc_bytes + \
                          self.bitvector_size + \
                          self.later_rotation_bytes + self.later_location_bytes + \
                          self.later_scale_bytes + self.later_uvc_bytes + \
                          16  # 16 is for the header

        assert self.total_size % 16 == 0, "Something went horribly wrong - final keyframe chunk not aligned to 16."
        # self.total_size = roundup(self.total_size, 16)

        self.contained_frames = contained_frames

        # Error checking
        assert len(flatten_list(self.later_rotations)) == sum([elem == 1 for elem in total_rotation_bitvector]), \
            "Number of rotation frames in keyframe chunk did not equal the number of rotations."
        assert len(flatten_list(self.later_locations)) == sum([elem == 1 for elem in total_location_bitvector]), \
            "Number of location frames in keyframe chunk did not equal the number of locations."
        assert len(flatten_list(self.later_scales)) == sum([elem == 1 for elem in total_scale_bitvector]), \
            "Number of scale frames in keyframe chunk did not equal the number of scales."
        # Do UVCs? Needs to be handled differently because 1 float per channel instead of a list of floats

    @classmethod
    def init_penultimate_chunk(cls, rotations, locations, scales, uvcs,
                               rotation_bitvector, location_bitvector, scale_bitvector, uvc_bitvector,
                               contained_frames):
        pass_rotations, pass_rotation_bitvector = cut_final_frame(rotations, rotation_bitvector)
        pass_locations, pass_location_bitvector = cut_final_frame(locations, location_bitvector)
        pass_scales, pass_scale_bitvector = cut_final_frame(scales, scale_bitvector)
        pass_uvcs, pass_uvc_bitvector = cut_final_frame(uvcs, uvc_bitvector)

        return cls(pass_rotations, pass_locations, pass_scales, pass_uvcs,
                   pass_rotation_bitvector, pass_location_bitvector, pass_scale_bitvector, pass_uvc_bitvector,
                   contained_frames - 1)


def cut_final_frame(data, bitvector):
    return_data = {}
    return_bitvector = {}
    for i, ((bidx, datum), bv) in enumerate(zip(data.items(), bitvector)):
        # If the data contains the final frame, remove it
        if bv[-1] == 1 and len(datum) > 1:
            return_data[bidx] = list(datum)[:-1]
        else:
            return_data[bidx] = list(datum)
        # Irrespective of whether the final frame holds data, we're cutting it off - so remove it from the bitvector
        return_bitvector[bidx] = bv[:-1]

    return return_data, list(return_bitvector.values())

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
