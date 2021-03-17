import itertools
import numpy as np

from ..FileReaders.AnimReader import AnimReader
from ..Utilities.Interpolation import lerp, slerp


class AnimInterface:
    def __init__(self):
        self.playback_rate = None
        self.num_bones = None

        self.rotations = {}
        self.locations = {}
        self.scales = {}

    @classmethod
    def from_file(cls, path, skelReader):
        instance = cls()
        with open(path, 'rb') as F:
            readwriter = AnimReader(F, skelReader)
            readwriter.read()

        # Only need to take the playback rate; duration can be calculated from this and the total number of frames
        instance.playback_rate = readwriter.playback_rate
        instance.num_bones = readwriter.num_bones

        # Set up the data holder variables
        for idx in range(readwriter.num_bones):
            instance.rotations[idx] = {}
            instance.locations[idx] = {}
            instance.scales[idx] = {}

        # Get the bits that are constant throughout the animation
        for bone_idx, rotation in zip(readwriter.static_pose_rotations_bone_idxs, readwriter.static_pose_bone_rotations):
            instance.rotations[bone_idx][0] = rotation
        for bone_idx, location in zip(readwriter.static_pose_locations_bone_idxs, readwriter.static_pose_bone_locations):
            instance.locations[bone_idx][0] = location
        for bone_idx, scale in zip(readwriter.static_pose_scales_bone_idxs, readwriter.static_pose_bone_scales):
            instance.scales[bone_idx][0] = scale

        # Now add in the rotations, locations, and scales that change throughout the animation
        for (cumulative_frames, nframes), substructure in zip(readwriter.keyframe_counts, readwriter.keyframe_chunks):
            # Each keyframe chunk begins with a single frame
            for bone_idx, value in zip(readwriter.animated_rotations_bone_idxs, substructure.frame_0_rotations):
                instance.rotations[bone_idx][cumulative_frames] = value
            for bone_idx, value in zip(readwriter.animated_locations_bone_idxs, substructure.frame_0_locations):
                instance.locations[bone_idx][cumulative_frames] = value
            for bone_idx, value in zip(readwriter.animated_scales_bone_idxs, substructure.frame_0_scales):
                instance.scales[bone_idx][cumulative_frames] = value

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
            # In this case, the animation is 11 frames long (the number of 1s and 0s under each bit annotated as
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

        return instance

    def to_file(self, path, sk):
        print("###### DUMPING TO FILE ######")
        num_frames = max([max([list(self.rotations[bone_idx].keys())[-1] if len(self.rotations[bone_idx].keys()) else 0 for bone_idx in self.rotations]),
                          max([list(self.locations[bone_idx].keys())[-1] if len(self.locations[bone_idx].keys()) else 0 for bone_idx in self.locations]),
                          max([list(self.scales[bone_idx].keys())[-1] if len(self.scales[bone_idx].keys()) else 0 for bone_idx in self.scales])])
        num_frames += 1  # This is because the frames start from index 0
        num_bones = self.num_bones

        with open(path, 'wb') as F:
            readwriter = AnimReader(F, sk)
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

            #blend_bones, extra_statics = staticify_malformed_blend_bones(blend_rots, blend_locs, blend_scls)
            # for bone in extra_statics:
            #     static_rots[bone] = (0., 0., 0., 1.)
            #     static_locs[bone] = (0., 0., 0.)
            #     static_scls[bone] = (1., 1., 1.)
            blend_bones = blend_locs

            # Sort the static bones into the correct order after adding malformed blend bones
            static_rots = {k: v for k, v in sorted(list(static_rots.items()), key=lambda x: x[0])}
            static_locs = {k: v for k, v in sorted(list(static_locs.items()), key=lambda x: x[0])}
            static_scls = {k: v for k, v in sorted(list(static_scls.items()), key=lambda x: x[0])}

            # Slap down the counts of the static and animated bones
            readwriter.static_pose_bone_rotations_count = len(static_rots)
            readwriter.static_pose_bone_locations_count = len(static_locs)
            readwriter.static_pose_bone_scales_count = len(static_scls)
            readwriter.unknown_0x1C = 0  # Fix me!
            readwriter.animated_bone_rotations_count = len(anim_rots)
            readwriter.animated_bone_locations_count = len(anim_locs)
            readwriter.animated_bone_scales_count = len(anim_scls)
            readwriter.unknown_0x24 = 0  # Fix me!
            readwriter.padding_0x26 = 0
            readwriter.bone_mask_bytes = num_bones if len(blend_bones) else 0

            # Fill in the pointers to the main data sections, just add in the offset for now
            # readwriter.abs_ptr_bone_mask  Fix me!
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
            readwriter.unknown_bone_idxs_4 = []
            readwriter.animated_rotations_bone_idxs = list(anim_rots.keys())
            readwriter.animated_locations_bone_idxs = list(anim_locs.keys())
            readwriter.animated_scales_bone_idxs = list(anim_scls.keys())
            readwriter.unknown_bone_idxs_8 = []

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
            readwriter.unknown_data_4 = []

            # Update the virtual pointer and set pointers
            readwriter.rel_ptr_static_pose_bone_rotations += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_rotations)*6
            virtual_pointer = roundup(virtual_pointer, 16)

            readwriter.rel_ptr_static_pose_bone_locations += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_locations)*12
            virtual_pointer = roundup(virtual_pointer, 16)

            readwriter.rel_ptr_static_pose_bone_scales += virtual_pointer
            virtual_pointer += len(readwriter.static_pose_bone_scales)*12
            # virtual_pointer = roundup(virtual_pointer, 16)  # No rounding for this section

            readwriter.rel_ptr_static_unknown_4 += virtual_pointer
            virtual_pointer += len(readwriter.unknown_data_4)*4
            virtual_pointer = roundup(virtual_pointer, 16)

            # Now for the really tough bit
            # It's time to figure out how to divvy up the keyframes into chunks
            # Hardcode the chunk size to 1 + 16 for now
            frames_per_chunk = 1 + 17
            frames_per_chunk = min(frames_per_chunk, num_frames-1)
            chunk_holders = generate_keyframe_chunks(anim_rots, anim_locs, anim_scls, num_frames, frames_per_chunk)
            readwriter.num_keyframe_chunks = len(chunk_holders)
            readwriter.prepare_read_op()  # This creates enough empty KeyFrameChunk objects for us to fill

            # Note down the pointer to the keyframe chunks for now but fill in the later later
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
                for bone_idx in blend_bones:
                    bone_mask[bone_idx] = 0
                readwriter.bone_masks = bone_mask
                virtual_pointer = roundup(virtual_pointer, 4)
                readwriter.unknown_data_masks = []
                readwriter.bone_mask_bytes = n_mask_entries

                virtual_pointer = roundup(virtual_pointer, 16)

            # Finally, go back and do KF chunk pointers
            readwriter.keyframe_chunks_ptrs = []
            final_chunk_size = chunk_holders[-1].total_size
            for chunk in chunk_holders:
                chunk_size = chunk.total_size
                readwriter.keyframe_chunks_ptrs.append((0, chunk_size + final_chunk_size, virtual_pointer))
                virtual_pointer += chunk_size

            # Then finally dump the chunks themselves
            # SET PTR TO THIS SECTION HERE
            for chunk, kf_chunk in zip(chunk_holders, readwriter.keyframe_chunks):
                # Header variables
                kf_chunk.frame_0_rotations_bytecount = chunk.initial_rotation_bytes
                kf_chunk.frame_0_locations_bytecount = chunk.initial_location_bytes
                kf_chunk.frame_0_scales_bytecount = chunk.initial_scale_bytes
                kf_chunk.unknown_0x06 = 0
                kf_chunk.keyframed_rotations_bytecount = chunk.later_rotation_bytes
                kf_chunk.keyframed_locations_bytecount = chunk.later_location_bytes
                kf_chunk.keyframed_scales_bytecount = chunk.later_scale_bytes
                kf_chunk.unknown_0x0E = 0

                # Data holders
                kf_chunk.frame_0_rotations = chunk.initial_rotations
                kf_chunk.frame_0_locations = chunk.initial_locations
                kf_chunk.frame_0_scales = chunk.initial_scales
                kf_chunk.unknown_data_4 = []
                kf_chunk.keyframes_in_use = chunk.total_bitvector
                kf_chunk.keyframed_rotations = flatten_list(chunk.later_rotations)
                kf_chunk.keyframed_locations = flatten_list(chunk.later_locations)
                kf_chunk.keyframed_scales = flatten_list(chunk.later_scales)
                kf_chunk.unknown_data_9 = []

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


def strip_and_validate(keyframes, chunksize, method):
    reduced_chunks, bitvectors, initial_values, final_values = generate_keyframe_chunks_entry_data(keyframes)
    already_handled_chunks = []
    for chunk_idx, (reduced_chunk, bitvector, initial_pair, final_pair) in enumerate(zip(reduced_chunks, bitvectors, initial_values, final_values)):
        if chunk_idx in already_handled_chunks:
            continue
        skipped_chunks = []
        # This should *never* be the case for the first chunk
        if bitvector[0] == '0':
            # Get the previous chunk so we can use that as the first point to interpolate from
            interp_origin = final_values[chunk_idx - 1]
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

            for skipped_chunk_idx in skipped_chunks:
                interp_end_data, interp_end_frame = interp_end
                relative_frame_idx = (skipped_chunk_idx - chunk_idx + 1)*chunksize + interp_end_frame  # i.e. (i+1)*chunksize + interp_end_frame
                initial_frame = interp_origin[1]
                t = (chunksize - initial_frame) / (relative_frame_idx - initial_frame)
                interpolated_frame_data = method(interp_origin[0], interp_end_data, t)  # Needs to be lerp for pos, slerp for quat
                bitvectors[skipped_chunk_idx] = '1' + bitvectors[skipped_chunk_idx][1:]
                reduced_chunks[skipped_chunk_idx] = [interpolated_frame_data, *reduced_chunks[skipped_chunk_idx]]
                already_handled_chunks.extend(skipped_chunks)

    return reduced_chunks, bitvectors


def strip_and_validate_all_bones(frame_data, chunksize, interpolation_method):
    keyframe_chunks_data = {}
    bitvector_data = {}
    for i, (bone_idx, chunks) in enumerate(frame_data.items()):
        reduced_chunks, bitvectors = strip_and_validate(chunks, chunksize, interpolation_method)
        keyframe_chunks_data[bone_idx] = reduced_chunks
        bitvector_data[bone_idx] = bitvectors
    for (bone_idx, bone_data), bitvectors in zip(keyframe_chunks_data.items(), bitvector_data.values()):
        for subdata, bitvector in zip(bone_data, bitvectors):
            assert len(subdata) == sum([elem == '1' for elem in bitvector]), f"{bone_idx}"
    return keyframe_chunks_data, bitvector_data


def generate_keyframe_chunks(animated_rotations, animated_locations, animated_scales, num_frames, chunksize):
    # These lines create lists of length num_frames with None for frames with no data
    rotations = populate_frames(num_frames, animated_rotations)
    locations = populate_frames(num_frames, animated_locations)
    scales = populate_frames(num_frames, animated_scales)

    # The above is done so that the frames can be easily chunked by the following three lines:
    rotations = chunk_frames(rotations, chunksize)
    locations = chunk_frames(locations, chunksize)
    scales = chunk_frames(scales, chunksize)

    # And now we can iterate through the chunks and strip out the None values, and save the results
    # We also might need to perform some interpolation inside these functions in order to satisfy the requirements of
    # the DSCS animation format
    # Also need to isolate the final frame in here for the same reasons
    rotation_keyframe_chunks_data, rotation_bitvector_data = strip_and_validate_all_bones(rotations, chunksize, slerp)
    location_keyframe_chunks_data, location_bitvector_data = strip_and_validate_all_bones(locations, chunksize, lerp)
    scale_keyframe_chunks_data, scale_bitvector_data = strip_and_validate_all_bones(scales, chunksize, lerp)

    # Now we can bundle all the chunks into a sequential list, ready for turning into KeyframeChunks instances
    chunk_data = [[{}, {}, {}] for _ in range((num_frames // chunksize) + 1)]
    for bone_idx, rotation_chunks in rotation_keyframe_chunks_data.items():
        for i, rotation_data in enumerate(rotation_chunks):
            chunk_data[i][0][bone_idx] = rotation_data
    for bone_idx, location_chunks in location_keyframe_chunks_data.items():
        for i, location_data in enumerate(location_chunks):
            chunk_data[i][1][bone_idx] = location_data
    for bone_idx, scale_chunks in scale_keyframe_chunks_data.items():
        for i, scale_data in enumerate(scale_chunks):
            chunk_data[i][2][bone_idx] = scale_data

    # We also need the final elements of each animation
    final_rotations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_rotations.items()}
    final_locations = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_locations.items()}
    final_scales = {bone_id: [list(data.values())[-1]] for bone_id, data in animated_scales.items()}

    chunks = []
    for chunk_idx, chunk_datum in enumerate(chunk_data[:-1]):
        r_bitvecs = [rotation_bitvector_data[bone_id][chunk_idx] for bone_id in rotation_bitvector_data]
        l_bitvecs = [location_bitvector_data[bone_id][chunk_idx] for bone_id in location_bitvector_data]
        s_bitvecs = [scale_bitvector_data[bone_id][chunk_idx] for bone_id in scale_bitvector_data]

        chunks.append(ChunkHolder(*chunk_datum, r_bitvecs, l_bitvecs, s_bitvecs, chunksize))

    pen_r_bitvecs = [rotation_bitvector_data[bone_id][-1] for bone_id in rotation_bitvector_data]
    pen_l_bitvecs = [location_bitvector_data[bone_id][-1] for bone_id in location_bitvector_data]
    pen_s_bitvecs = [scale_bitvector_data[bone_id][-1] for bone_id in scale_bitvector_data]
    chunks.append(ChunkHolder.init_penultimate_chunk(*chunk_data[-1],
                                                     pen_r_bitvecs, pen_l_bitvecs, pen_s_bitvecs,
                                                     len(pen_r_bitvecs[0])))
    chunks.append(ChunkHolder(final_rotations, final_locations, final_scales,
                              ['1' for _ in final_rotations], ['1' for _ in final_locations], ['1' for _ in final_scales],
                              1))

    return chunks


class ChunkHolder:
    def __init__(self, rotations, locations, scales,
                 rotation_bitvector, location_bitvector, scale_bitvector,
                 contained_frames):
        rotations = list(rotations.values())
        locations = list(locations.values())
        scales = list(scales.values())

        bytes_read = 16
        self.initial_rotations = [sublist[0] for sublist in rotations]
        self.initial_locations = [sublist[0] for sublist in locations]
        self.initial_scales = [sublist[0] for sublist in scales]

        self.initial_rotation_bytes = len(self.initial_rotations)*6
        self.initial_location_bytes = len(self.initial_locations)*12
        self.initial_scale_bytes = len(self.initial_scales)*12
        bytes_read += self.initial_rotation_bytes
        bytes_read += self.initial_location_bytes
        bytes_read += self.initial_scale_bytes
        self.initial_scale_bytes += (4 - (bytes_read % 4)) % 4
        bytes_read += (4 - (bytes_read % 4)) % 4

        total_rotation_bitvector = ''.join([elem[1:] for elem in rotation_bitvector])
        total_location_bitvector = ''.join([elem[1:] for elem in location_bitvector])
        total_scale_bitvector = ''.join([elem[1:] for elem in scale_bitvector])

        self.total_bitvector = total_rotation_bitvector + total_location_bitvector + total_scale_bitvector
        self.bitvector_size = (len(self.total_bitvector) + ((8 - (len(self.total_bitvector) % 8)) % 8)) // 8
        bytes_read += self.bitvector_size

        self.later_rotations = [sublist[1:] for sublist in rotations]
        self.later_locations = [sublist[1:] for sublist in locations]
        self.later_scales = [sublist[1:] for sublist in scales]

        self.later_rotation_bytes = sum([len(elem) for elem in self.later_rotations])*6
        self.later_location_bytes = sum([len(elem) for elem in self.later_locations])*12
        self.later_scale_bytes = sum([len(elem) for elem in self.later_scales])*12
        bytes_read += self.later_rotation_bytes
        bytes_read += self.later_location_bytes
        bytes_read += self.later_scale_bytes
        self.later_scale_bytes += (4 - (bytes_read % 4)) % 4
        bytes_read += (4 - (bytes_read % 4)) % 4

        self.total_size = self.initial_rotation_bytes + self.initial_location_bytes + self.initial_scale_bytes + \
                          self.bitvector_size + self.later_rotation_bytes + self.later_location_bytes + \
                          self.later_scale_bytes + 16 # 16 is for the header

        self.total_size = roundup(self.total_size, 16)

        self.contained_frames = contained_frames

        # Error checking
        assert len(flatten_list(self.later_rotations)) == sum([elem == '1' for elem in total_rotation_bitvector]), \
               "Number of rotation frames in keyframe chunk did not equal the number of rotations."
        assert len(flatten_list(self.later_locations)) == sum([elem == '1' for elem in total_location_bitvector]), \
               "Number of location frames in keyframe chunk did not equal the number of locations."
        assert len(flatten_list(self.later_scales)) == sum([elem == '1' for elem in total_scale_bitvector]), \
               "Number of scale frames in keyframe chunk did not equal the number of scales."

    @classmethod
    def init_penultimate_chunk(cls, rotations, locations, scales,
                               rotation_bitvector, location_bitvector, scale_bitvector,
                               contained_frames):
        pass_rotations, pass_rotation_bitvector = cut_final_frame(rotations, rotation_bitvector)
        pass_locations, pass_location_bitvector = cut_final_frame(locations, location_bitvector)
        pass_scales, pass_scale_bitvector = cut_final_frame(scales, scale_bitvector)

        return cls(pass_rotations, pass_locations, pass_scales,
                   rotation_bitvector, location_bitvector, scale_bitvector,
                   contained_frames)


def cut_final_frame(data, bitvector):
    return_data = {}
    return_bitvector = {}
    for i, ((bidx, datum), bv) in enumerate(zip(data.items(), bitvector)):
        if bv[-1] == '1' and len(datum) > 1:
            return_data[bidx] = list(datum)[:-1]
        else:
            return_data[bidx] = list(datum)
        return_bitvector[bidx] = bitvector[:-1]

    return return_data, return_bitvector
