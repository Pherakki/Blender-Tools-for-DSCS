import itertools
import numpy as np

from ..FileReaders.AnimReader import AnimReader
from ..Utilities.Interpolation import lerp, slerp
import copy

class AnimInterface:
    def __init__(self):
        self.playback_rate = None
        self.num_bones = None

        self.rotations = {}
        self.locations = {}
        self.scales = {}
        self.user_channels = {}

    @classmethod
    def from_file(cls, path):
        instance = cls()
        with open(path, 'rb') as F:
            readwriter = AnimReader(F)
            readwriter.read()

        # Only need to take the playback rate; duration can be calculated from this and the total number of frames
        instance.playback_rate = readwriter.playback_rate
        instance.num_bones = readwriter.num_bones

        # Set up the data holder variables
        for idx in range(readwriter.num_bones):
            instance.rotations[idx] = {}
            instance.locations[idx] = {}
            instance.scales[idx] = {}
        total_uv_channels = readwriter.unknown_0x1C + readwriter.unknown_0x24
        for idx in range(total_uv_channels):
            instance.user_channels[idx] = {}
        # Get the bits that are constant throughout the animation
        for bone_idx, rotation in zip(readwriter.static_pose_rotations_bone_idxs, readwriter.static_pose_bone_rotations):
            instance.rotations[bone_idx][0] = rotation
        for bone_idx, location in zip(readwriter.static_pose_locations_bone_idxs, readwriter.static_pose_bone_locations):
            instance.locations[bone_idx][0] = location
        for bone_idx, scale in zip(readwriter.static_pose_scales_bone_idxs, readwriter.static_pose_bone_scales):
            instance.scales[bone_idx][0] = scale
        for channel_idx, channel_data in zip(readwriter.unknown_bone_idxs_4, readwriter.unknown_data_4):
            instance.user_channels[channel_idx][0] = channel_data

        # Now add in the rotations, locations, and scales that change throughout the animation
        for (cumulative_frames, nframes), substructure in zip(readwriter.keyframe_counts, readwriter.keyframe_chunks):
            # Each keyframe chunk begins with a single frame
            for bone_idx, value in zip(readwriter.animated_rotations_bone_idxs, substructure.frame_0_rotations):
                instance.rotations[bone_idx][cumulative_frames] = value
            for bone_idx, value in zip(readwriter.animated_locations_bone_idxs, substructure.frame_0_locations):
                instance.locations[bone_idx][cumulative_frames] = value
            for bone_idx, value in zip(readwriter.animated_scales_bone_idxs, substructure.frame_0_scales):
                instance.scales[bone_idx][cumulative_frames] = value
            for channel_idx, value in zip(readwriter.unknown_bone_idxs_8, substructure.unknown_data_4):
                instance.user_channels[channel_idx][cumulative_frames] = value

            # The keyframe rotations, locations, etc. for all bones are all concatenated together into one big list
            # per transform type.
            # The keyframes that use each transform are stored in a bit-vector with an equal length to the number of
            # frames. These bit-vectors are all concatenated together in one huge bit-vector, in the order
            # rotations->locations->scales->unknown_4
            # Therefore, it's pretty reasonable to turn these lists of keyframe rotations, locations, etc.
            # into generators using the built-in 'iter' function or the 'chunks' function defined at the bottom of the
            # file.
            if nframes != 0:
                masks = chunks(substructure.keyframes_in_use, nframes)
            else:
                masks = []

            rotations = iter(substructure.keyframed_rotations)
            locations = iter(substructure.keyframed_locations)
            scales = iter(substructure.keyframed_scales)
            user_channels = iter(substructure.unknown_data_9)

            # The benefit of doing this is that generators behave like a Queue. We can pop the next element off these
            # generators and never have to worry about keeping track of the state of each generator, because the
            # generator keeps track of it for us.
            # In this function, the bit-vector is chunked and labelled 'masks'.
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
            # corresponds to. We continue iterating through this bit-vector by grabbing the next mask from 'masks',
            # and we should consume the entire generator of rotation data after 5 masks. The next mask we grab should
            # then correspond to location data, so we move onto the next for-loop below, and so on for the scale data.
            for bone_idx, mask in zip(readwriter.animated_rotations_bone_idxs, masks):
                frames = [j+cumulative_frames+1 for j, elem in enumerate(mask) if elem == '1']
                values = itertools.islice(rotations, len(frames))  # Pop the next num_frames rotations
                for frame, value in zip(frames, values):
                    instance.rotations[bone_idx][frame] = value
            for bone_idx, mask in zip(readwriter.animated_locations_bone_idxs, masks):
                frames = [j+cumulative_frames+1 for j, elem in enumerate(mask) if elem == '1']
                values = itertools.islice(locations, len(frames))  # Pop the next num_frames locations
                for frame, value in zip(frames, values):
                    instance.locations[bone_idx][frame] = value
            for bone_idx, mask in zip(readwriter.animated_scales_bone_idxs, masks):
                frames = [j+cumulative_frames+1 for j, elem in enumerate(mask) if elem == '1']
                values = itertools.islice(scales, len(frames))  # Pop the next num_frames scales
                for frame, value in zip(frames, values):
                    instance.scales[bone_idx][frame] = value
            for channel_idx, mask in zip(readwriter.unknown_bone_idxs_8, masks):
                frames = [j+cumulative_frames+1 for j, elem in enumerate(mask) if elem == '1']
                values = itertools.islice(user_channels, len(frames))  # Pop the next num_frames user channel data
                for frame, value in zip(frames, values):
                    instance.user_channels[channel_idx][frame] = value
            assert len(list(masks)) == 0

        # Recover quaternion signs lost during compression
        for bone_idx, rotations in instance.rotations.items():
            instance.rotations[bone_idx] = match_quat_signs_in_dict(instance.rotations[bone_idx])

        return instance

    def to_file(self, path, blend_bones=None):
        try:
            max_rotations = max([list(self.rotations[bone_idx].keys())[-1] if len(self.rotations[bone_idx].keys()) else 0 for bone_idx in self.rotations])
        except:
            max_rotations = 0
        try:
            max_locations = max([list(self.locations[bone_idx].keys())[-1] if len(self.locations[bone_idx].keys()) else 0 for bone_idx in self.locations])
        except:
            max_locations = 0
        try:
            max_scales = max([list(self.scales[bone_idx].keys())[-1] if len(self.scales[bone_idx].keys()) else 0 for bone_idx in self.scales])
        except:
            max_scales = 0
        try:
            max_user_channels = max([list(self.user_channels[channel_idx].keys())[-1] if len(self.user_channels[channel_idx].keys()) else 0 for channel_idx in self.user_channels])
        except:
            max_user_channels = 0

        num_frames = int(max([max_rotations, max_locations, max_scales, max_user_channels]))
        num_frames += 1  # This is because the frames start from index 0
        num_bones = self.num_bones

        with open(path, 'wb') as F:
            readwriter = AnimReader(F)
            readwriter.filetype = '40AE'
            readwriter.animation_duration = (num_frames - 1)/self.playback_rate
            readwriter.playback_rate = self.playback_rate

            # skip setup_and_static_data_size for now
            readwriter.num_bones = num_bones
            readwriter.total_frames = num_frames
            # skip num_keyframe_chunks for now
            readwriter.always_16384 = 16384

            # Time to figure out how to organise the keyframes...
            static_rots, anim_rots, blend_rots = split_keyframes_by_role(self.rotations)
            static_locs, anim_locs, blend_locs = split_keyframes_by_role(self.locations)
            static_scls, anim_scls, blend_scls = split_keyframes_by_role(self.scales)
            static_uvcs, anim_uvcs, blend_uvcs = split_keyframes_by_role(self.user_channels)
            if blend_bones is None:
                blend_bones = blend_locs

            # Sort the static bones into the correct order after adding malformed blend bones
            # Redundant?
            static_rots = {k: v for k, v in sorted(list(static_rots.items()), key=lambda x: x[0])}
            static_locs = {k: v for k, v in sorted(list(static_locs.items()), key=lambda x: x[0])}
            static_scls = {k: v for k, v in sorted(list(static_scls.items()), key=lambda x: x[0])}
            static_uvcs = {k: v for k, v in sorted(list(static_uvcs.items()), key=lambda x: x[0])}

            # Slap down the counts of the static and animated bones
            readwriter.static_pose_bone_rotations_count = len(static_rots)
            readwriter.static_pose_bone_locations_count = len(static_locs)
            readwriter.static_pose_bone_scales_count = len(static_scls)
            readwriter.unknown_0x1C = len(static_uvcs)
            readwriter.animated_bone_rotations_count = len(anim_rots)
            readwriter.animated_bone_locations_count = len(anim_locs)
            readwriter.animated_bone_scales_count = len(anim_scls)
            readwriter.unknown_0x24 = len(anim_uvcs)
            readwriter.padding_0x26 = 0
            readwriter.bone_mask_bytes = num_bones if len(blend_bones) else 0

            # Fill in the pointers to the main data sections, just add in the offset for now
            # readwriter.abs_ptr_bone_mask is handled in the blend_bones section
            readwriter.rel_ptr_keyframe_chunks_ptrs = - 0x30
            readwriter.rel_ptr_keyframe_chunks_counts = - 0x34
            readwriter.rel_ptr_static_pose_bone_rotations = - 0x38
            readwriter.rel_ptr_static_pose_bone_locations = - 0x3C
            readwriter.rel_ptr_static_pose_bone_scales = - 0x40
            readwriter.rel_ptr_static_unknown_4 = - 0x44

            # Padding variables
            readwriter.padding_0x48 = 0
            readwriter.padding_0x4C = 0
            readwriter.padding_0x50 = 0
            readwriter.padding_0x54 = 0
            readwriter.padding_0x58 = 0
            readwriter.padding_0x5C = 0

            virtual_pointer = 0x60  # Set pointer to the end of the header

            # Fill in section 1: Bone indices used by the relevant data sections
            readwriter.static_pose_rotations_bone_idxs = list(static_rots.keys())
            readwriter.static_pose_locations_bone_idxs = list(static_locs.keys())
            readwriter.static_pose_scales_bone_idxs = list(static_scls.keys())
            readwriter.unknown_bone_idxs_4 = list(static_uvcs.keys())
            readwriter.animated_rotations_bone_idxs = list(anim_rots.keys())
            readwriter.animated_locations_bone_idxs = list(anim_locs.keys())
            readwriter.animated_scales_bone_idxs = list(anim_scls.keys())
            readwriter.unknown_bone_idxs_8 = list(anim_uvcs.keys())

            # Update the virtual pointer for section 1
            virtual_pointer += roundup(readwriter.static_pose_bone_rotations_count, 8)*2
            virtual_pointer += roundup(readwriter.static_pose_bone_locations_count, 4)*2
            virtual_pointer += roundup(readwriter.static_pose_bone_scales_count, 4)*2
            virtual_pointer += roundup(readwriter.unknown_0x1C, 4)*2
            virtual_pointer += roundup(readwriter.animated_bone_rotations_count, 4)*2
            virtual_pointer += roundup(readwriter.animated_bone_locations_count, 4)*2
            virtual_pointer += roundup(readwriter.animated_bone_scales_count, 4)*2
            virtual_pointer += roundup(readwriter.unknown_0x24, 4)*2

            virtual_pointer = roundup(virtual_pointer, 16)

            # Fill in sections 2-5: Rotations, locations, scales, unknown_4
            readwriter.static_pose_bone_rotations = list(static_rots.values())
            readwriter.static_pose_bone_locations = list(static_locs.values())
            readwriter.static_pose_bone_scales = list(static_scls.values())
            readwriter.unknown_data_4 = list(static_uvcs.values())

            # Update the virtual pointer and set pointers
            readwriter.rel_ptr_static_pose_bone_rotations += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_rotations)*6
            virtual_pointer = roundup(virtual_pointer, 16)

            readwriter.rel_ptr_static_pose_bone_locations += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_locations)*12
            virtual_pointer = roundup(virtual_pointer, 16)

            readwriter.rel_ptr_static_pose_bone_scales += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_scales)*12
            # No rounding for this section

            readwriter.rel_ptr_static_unknown_4 += virtual_pointer
            virtual_pointer += len(readwriter.unknown_data_4)*4
            virtual_pointer = roundup(virtual_pointer, 16)

            # Now for the really tough bit
            # It's time to figure out how to divvy up the keyframes into chunks
            chunk_holders = generate_keyframe_chunks(anim_rots, anim_locs, anim_scls, anim_uvcs, num_frames)
            readwriter.num_keyframe_chunks = len(chunk_holders)
            readwriter.prepare_read_op()  # This creates enough empty KeyFrameChunk objects for us to fill

            # Note down the pointer to the keyframe chunks for now but fill in later
            readwriter.rel_ptr_keyframe_chunks_ptrs += virtual_pointer
            # < This is where the data would go if it didn't rely on pointers that still have to be computed >
            virtual_pointer += 8 * len(chunk_holders)

            # Then do KF chunk frames
            readwriter.rel_ptr_keyframe_chunks_counts += virtual_pointer
            readwriter.keyframe_counts = []
            running_total = 0
            for chunk in chunk_holders:
                readwriter.keyframe_counts.append((running_total, chunk.contained_frames - 1))
                running_total += chunk.contained_frames
            virtual_pointer += 4 * len(chunk_holders)
            virtual_pointer = roundup(virtual_pointer, 16)

            # Then blend bones
            readwriter.setup_and_static_data_size = virtual_pointer
            readwriter.abs_ptr_bone_mask = 0
            readwriter.bone_mask_bytes = 0
            if len(blend_bones):
                readwriter.abs_ptr_bone_mask = virtual_pointer
                n_mask_entries = roundup(readwriter.num_bones, 4)
                bone_mask = [-1 for _ in range(readwriter.num_bones)]
                virtual_pointer += n_mask_entries
                for bone_idx in blend_bones:
                    bone_mask[bone_idx] = 0
                readwriter.bone_masks = bone_mask
                virtual_pointer = roundup(virtual_pointer, 4)
                readwriter.unknown_data_masks = []  # Fix?
                readwriter.bone_mask_bytes = n_mask_entries

                virtual_pointer = roundup(virtual_pointer, 16)
            # Finally, go back and do KF chunk pointers
            readwriter.keyframe_chunks_ptrs = []
            final_chunk_size = chunk_holders[-1].total_size
            for chunk in chunk_holders[:-1]:
                chunk_size = chunk.total_size
                readwriter.keyframe_chunks_ptrs.append((0, chunk_size + final_chunk_size, virtual_pointer))
                virtual_pointer += chunk_size
            readwriter.keyframe_chunks_ptrs.append((0, 0, virtual_pointer))

            # Then finally dump the chunks themselves
            for chunk, kf_chunk in zip(chunk_holders, readwriter.keyframe_chunks):
                # Header variables
                kf_chunk.frame_0_rotations_bytecount = chunk.initial_rotation_bytes
                kf_chunk.frame_0_locations_bytecount = chunk.initial_location_bytes
                kf_chunk.frame_0_scales_bytecount = chunk.initial_scale_bytes
                kf_chunk.unknown_0x06 = chunk.initial_uvc_bytes
                kf_chunk.keyframed_rotations_bytecount = chunk.later_rotation_bytes
                kf_chunk.keyframed_locations_bytecount = chunk.later_location_bytes
                kf_chunk.keyframed_scales_bytecount = chunk.later_scale_bytes
                kf_chunk.unknown_0x0E = chunk.later_uvc_bytes

                # Data holders
                kf_chunk.frame_0_rotations = chunk.initial_rotations
                kf_chunk.frame_0_locations = chunk.initial_locations
                kf_chunk.frame_0_scales = chunk.initial_scales
                kf_chunk.unknown_data_4 = chunk.initial_uvcs
                kf_chunk.keyframes_in_use = chunk.total_bitvector
                kf_chunk.keyframed_rotations = flatten_list(chunk.later_rotations)
                kf_chunk.keyframed_locations = flatten_list(chunk.later_locations)
                kf_chunk.keyframed_scales = flatten_list(chunk.later_scales)
                kf_chunk.unknown_data_9 = flatten_list(chunk.later_uvcs)

            # Just set the hack variables to 0
            readwriter.max_val_1 = 0
            readwriter.max_val_2 = 0

            readwriter.write()


def flatten_list(lst):
    return [subitem for item in lst for subitem in item]


def remaining_chunk_length(size, chunksize):
    return (chunksize - (size % chunksize)) % chunksize


def roundup(size, chunksize):
    return size + remaining_chunk_length(size, chunksize)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def split_keyframes_by_role(keyframe_set):
    statics = {}
    animated = {}
    blend = []

    for bone_idx, keyframes in keyframe_set.items():
        if len(keyframes) == 0:
            blend.append(bone_idx)
        elif len(keyframes) == 1:
            statics[bone_idx] = list(keyframes.values())[0]
        else:
            animated[bone_idx] = keyframes
    return statics, animated, blend


def staticify_malformed_blend_bones(blend_rots, blend_locs, blend_scls):
    all_bones = set()
    all_bones.update(set(blend_rots))
    all_bones.update(set(blend_locs))
    all_bones.update(set(blend_scls))

    bad_bones = []
    good_bones = []
    for bone in all_bones:
        if bone in blend_rots and bone in blend_locs and bone in blend_scls:
            good_bones.append(bone)
        else:
            bad_bones.append(bone)

    return sorted(good_bones), sorted(bad_bones)


def populate_frames(num_frames, animation_data):
    """
    Takes a dictionary of frame_id: data pairs and produces a list of length num_frames with data inserted at indices
    specified by frame_id, and None everywhere else.
    """
    frame_data = {}
    for bone_id, keyframes in animation_data.items():
        frame_data[bone_id] = [None] * num_frames
        for frame_id, frame_value in keyframes.items():
            frame_data[bone_id][frame_id] = frame_value
    return frame_data


def chunk_frames(frames, chunksize):
    chunked_frames = {}
    for bone_id, value in frames.items():
        chunked_frames[bone_id] = chunks(value, chunksize)
    return chunked_frames


def adaptive_chunk_frames(rotation_frames, location_frames, scale_frames, uvc_frames, num_frames):
    cuts = [0]

    # Calculate how many bytes each frame will cost to store
    rotation_costs = bytecost_per_frame(rotation_frames, num_frames, 6)
    location_costs = bytecost_per_frame(location_frames, num_frames, 12)
    scale_costs = bytecost_per_frame(scale_frames, num_frames, 12)
    uvc_costs = bytecost_per_frame(uvc_frames, num_frames, 4)
    frame_costs = [sum(frames) for frames in zip(rotation_costs, location_costs, scale_costs, uvc_costs)]

    # Calculate how many bits need to get added to the bitvector per frame
    # Do this by determining how many bones are kept track of per animation type
    # and adding one bit per bone, if any bones are animated at all
    include_rotation_bitvector = sum(rotation_costs) != 0
    rotation_bitvector_price = len(rotation_frames) * include_rotation_bitvector
    include_location_bitvector = sum(location_costs) != 0
    location_bitvector_price = len(location_frames) * include_location_bitvector
    include_scale_bitvector = sum(scale_costs) != 0
    scale_bitvector_price = len(scale_frames) * include_scale_bitvector
    include_uvc_bitvector = sum(uvc_costs) != 0
    uvc_bitvector_price = len(uvc_frames) * include_uvc_bitvector

    bitvector_frame_cost = rotation_bitvector_price + location_bitvector_price + scale_bitvector_price + uvc_bitvector_price


    # The rot + loc + scale gets rounded up to nearest 4
    first_frame_price = roundup(frame_costs[0], 4)
    # This is the cost of a chunk containing only the first-frame data. Includes a 16-byte header + round up to 16
    additional_cost = roundup(first_frame_price + 16, 16)
    bitvector_bitcost = 0
    maximum_cost = 0xFFFF - additional_cost   # Presumably, need to subtract off the cost of the final frame chunk: the first frame price?
    maximum_cost = 0x2000
    # Skip the first frame, we already know how much that one costs
    for frame_idx in range(1, num_frames):
        animation_cost = sum(frame_costs[cuts[-1]+1:frame_idx+1])
        bitvector_bitcost += bitvector_frame_cost
        bitvector_cost = roundup(bitvector_bitcost, 8) // 8

        total_chunk_cost = roundup(roundup(16 + first_frame_price + bitvector_cost + animation_cost, 4), 16)
        if total_chunk_cost >= maximum_cost:
            # animation_cost -= frame_costs[frame_idx]
            # bitvector_bitcost -= bitvector_frame_cost
            # bitvector_cost = roundup(bitvector_bitcost, 8) // 8
            # total_chunk_cost = roundup(roundup(16 + first_frame_price + bitvector_cost + animation_cost, 4), 16)

            assert frame_idx-1 != cuts[-1], "Frame {frame_idx} too expensive to convert to DSCS frame [requires {current_cost}/{maximum_cost} available bytes]. Reduce number of animated bones in this frame to export."
            cuts.append(frame_idx-1)
            # Don't count this frame, since it will be replaced by the maximum
            # cost as the new "frame 0" of the new chunk
            # animation_cost = 0
            bitvector_bitcost = 0
    cuts.append(num_frames)

    rotation_chunks = {}
    location_chunks = {}
    scale_chunks = {}
    uvc_chunks = {}
    chunksizes = [ed - st for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in rotation_frames.items():
        rotation_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in location_frames.items():
        location_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for bone_idx, data in scale_frames.items():
        scale_chunks[bone_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]
    for channel_idx, data in uvc_frames.items():
        uvc_chunks[channel_idx] = [data[st:ed] for st, ed in zip(cuts[:-1], cuts[1:])]

    return rotation_chunks, location_chunks, scale_chunks, uvc_chunks, chunksizes


def bytecost_per_frame(frames, num_frames, cost):
    """
    Count the number of bytes required to store each frame in a series of frames organised in a nested dict as
    {bone_idxs: {frame_idxs: value}}
    """
    costs = [0]*num_frames
    for bone_id, data in frames.items():
        for frame_idx, value in enumerate(data):
            if value is not None:
                costs[frame_idx] += cost
    return costs


def boil_down_chunk(chunk):
    bitvector = ''
    reduced_chunk = []
    indices = []
    for j, value in enumerate(chunk):
        if value is None:
            bitvector += '0'
        else:
            bitvector += '1'
            reduced_chunk.append(value)
            indices.append(j)
    return reduced_chunk, bitvector, indices


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


def strip_and_validate(keyframes, chunksizes, method):
    reduced_chunks, bitvectors, initial_values, final_values = generate_keyframe_chunks_entry_data(keyframes)
    already_handled_chunks = []
    for chunk_idx, (reduced_chunk, bitvector, initial_pair, final_pair) in enumerate(zip(reduced_chunks, bitvectors, initial_values, final_values)):
        if chunk_idx in already_handled_chunks:
            continue
        skipped_chunks = []
        # This should *never* be the case for the first chunk
        # Every chunk must have data in its first frame, so check if what we have does...
        if bitvector[0] == '0':
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
                if bv[0] == '0':
                    skipped_chunks.append(chunk_idx + i)
                # If the chunk contains *some* data, stop here because we've found the next non-zero value
                # We'll carry this value forward and use it as the end point of the interpolation.
                if iter_initial_pair is not None:
                    interp_end = iter_initial_pair
                    break

            # Now, for every chunk we've identified as missing a first frame in the range where the data we've picked
            # out is applicable, do that generation
            interp_start_data, interp_start_frame = interp_origin
            interp_end_data, interp_end_frame = interp_end
            absolute_start_frame_index = sum(chunksizes[:(chunk_idx-1)]) + interp_start_frame
            absolute_end_frame_index = sum(chunksizes[:skipped_chunks[-1]]) + interp_end_frame
            for curr_skipped_chunk_idx, skipped_chunk_idx in enumerate(skipped_chunks):
                interpolation_index = sum(chunksizes[:skipped_chunk_idx])
                t = ((interpolation_index - absolute_start_frame_index) / (absolute_end_frame_index - absolute_start_frame_index))
                # Interpolate
                interpolated_frame_data = method(np.array(interp_start_data), np.array(interp_end_data), t)  # Needs to be lerp for pos, slerp for quat
                # Make relevant assignments to register the interpolated frame
                bitvectors[skipped_chunk_idx] = '1' + bitvectors[skipped_chunk_idx][1:]
                reduced_chunks[skipped_chunk_idx] = [interpolated_frame_data, *reduced_chunks[skipped_chunk_idx]]
                already_handled_chunks.extend(skipped_chunks)

    return reduced_chunks, bitvectors


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


def generate_keyframe_chunks(animated_rotations, animated_locations, animated_scales, animated_uvcs, num_frames):
    """
    This function has a very high bug potential...
    """
    # These lines create lists of length num_frames with None for frames with no data
    rotations = populate_frames(num_frames, animated_rotations)
    locations = populate_frames(num_frames, animated_locations)
    scales = populate_frames(num_frames, animated_scales)
    uvcs = populate_frames(num_frames, animated_uvcs)

    # The above is done so that the frames can be easily chunked by this function:
    rotations, locations, scales, uvcs, chunksizes = adaptive_chunk_frames(rotations, locations, scales, uvcs, num_frames)

    # And now we can iterate through the chunks and strip out the None values, and save the results
    # We also might need to perform some interpolation inside these functions in order to satisfy the requirements of
    # the DSCS animation format
    # Also need to isolate the final frame in here for the same reasons
    rotation_keyframe_chunks_data, rotation_bitvector_data = strip_and_validate_all_bones(rotations, chunksizes, slerp)
    location_keyframe_chunks_data, location_bitvector_data = strip_and_validate_all_bones(locations, chunksizes, lerp)
    scale_keyframe_chunks_data, scale_bitvector_data = strip_and_validate_all_bones(scales, chunksizes, lerp)
    uvc_keyframe_chunks_data, uvc_bitvector_data = strip_and_validate_all_bones(uvcs, chunksizes, lerp)

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
    for channel_idx, uvc_chunks in uvc_keyframe_chunks_data.items():
        for i, uvc_data in enumerate(uvc_chunks):
            chunk_data[i][3][channel_idx] = uvc_data

    # We also need the final elements of each animation
    final_rotations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_rotations.items()}
    final_locations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_locations.items()}
    final_scales = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_scales.items()}
    final_uvcs = {channel_id: [list(data.values())[-1]] for channel_id, data in animated_uvcs.items()}

    chunks = []
    if num_frames > 1:
        for chunk_idx, (chunk_datum, chunksize) in enumerate(zip(chunk_data[:-1], chunksizes[:-1])):
            r_bitvecs = [rotation_bitvector_data[bone_id][chunk_idx] for bone_id in rotation_bitvector_data]
            l_bitvecs = [location_bitvector_data[bone_id][chunk_idx] for bone_id in location_bitvector_data]
            s_bitvecs = [scale_bitvector_data[bone_id][chunk_idx] for bone_id in scale_bitvector_data]
            u_bitvecs = [uvc_bitvector_data[channel_id][chunk_idx] for channel_id in uvc_bitvector_data]
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
        pen_u_bitvecs = [uvc_bitvector_data[channel_id][-1] for channel_id in uvc_bitvector_data]

        chunks.append(ChunkHolder.init_penultimate_chunk(*chunk_data[-1],
                                                         pen_r_bitvecs, pen_l_bitvecs, pen_s_bitvecs, pen_u_bitvecs,
                                                         chunksizes[-1]))
    chunks.append(ChunkHolder(final_rotations, final_locations, final_scales, final_uvcs,
                              ['1' for _ in final_rotations], ['1' for _ in final_locations],
                              ['1' for _ in final_scales], ['1' for _ in final_uvcs],
                              1))

    return chunks


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

        self.initial_rotation_bytes = len(self.initial_rotations)*6
        self.initial_location_bytes = len(self.initial_locations)*12
        self.initial_scale_bytes = len(self.initial_scales)*12
        self.initial_uvc_bytes = len(self.initial_uvcs)*4
        bytes_read += self.initial_rotation_bytes
        bytes_read += self.initial_location_bytes
        bytes_read += self.initial_scale_bytes
        self.initial_scale_bytes += (4 - (bytes_read % 4)) % 4
        bytes_read += (4 - (bytes_read % 4)) % 4
        bytes_read += self.initial_uvc_bytes

        total_rotation_bitvector = ''.join([elem[1:] for elem in rotation_bitvector])
        total_location_bitvector = ''.join([elem[1:] for elem in location_bitvector])
        total_scale_bitvector = ''.join([elem[1:] for elem in scale_bitvector])
        total_uvc_bitvector = ''.join([elem[1:] for elem in uvc_bitvector])

        self.total_bitvector = total_rotation_bitvector + total_location_bitvector + total_scale_bitvector + total_uvc_bitvector
        self.bitvector_size = roundup(len(self.total_bitvector), 8) // 8
        bytes_read += self.bitvector_size

        self.later_rotations = [sublist[1:] for sublist in rotations]
        self.later_locations = [sublist[1:] for sublist in locations]
        self.later_scales = [sublist[1:] for sublist in scales]
        self.later_uvcs = [sublist[1:] for sublist in uvcs]

        self.later_rotation_bytes = sum([len(elem) for elem in self.later_rotations])*6
        self.later_location_bytes = sum([len(elem) for elem in self.later_locations])*12
        self.later_scale_bytes = sum([len(elem) for elem in self.later_scales])*12
        self.later_uvc_bytes = sum([len(elem) for elem in self.later_uvcs])*4
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
        self.later_uvcs.append([0.]*dummy_floats_to_add)
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
        assert len(flatten_list(self.later_rotations)) == sum([elem == '1' for elem in total_rotation_bitvector]), \
               "Number of rotation frames in keyframe chunk did not equal the number of rotations."
        assert len(flatten_list(self.later_locations)) == sum([elem == '1' for elem in total_location_bitvector]), \
               "Number of location frames in keyframe chunk did not equal the number of locations."
        assert len(flatten_list(self.later_scales)) == sum([elem == '1' for elem in total_scale_bitvector]), \
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
        if bv[-1] == '1' and len(datum) > 1:
            return_data[bidx] = list(datum)[:-1]
        else:
            return_data[bidx] = list(datum)
        # Irrespective of whether the final frame holds data, we're cutting it off - so remove it from the bitvector
        return_bitvector[bidx] = bv[:-1]

    return return_data, list(return_bitvector.values())


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
    dp = np.dot(comparison_quat, quat)
    sign = np.sign(dp)

    return sign * quat
