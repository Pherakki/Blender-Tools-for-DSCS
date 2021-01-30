import numpy as np
import struct

from .BaseRW import BaseRW


class AnimReader(BaseRW):
    """
    A class to read anim files. These files are split into eight main sections:
        1.  The header, which gives file pointers to split the file into its major sections, plus counts of what appears
            in each section.
        2.  A section that contains up to eight lists of bone indices, depending on non-zero counts in the header.
        3.  A section that defines the initial rotations of bones.
        4.  A section that defines the initial locations of bones.
        5.  A section that defines the initial scales of bones.
        6.  A section that 1 float (?)  per unknown_0x1C.
        7.  A section that contains lengths and start pointers for a set of substructures.
        8.  A section that contains cumulative counts and increments, one set of numbers per substructures.
        9.  A section of 0s and -1s, with one number per bone - may be blank, presumably if all bones have the value '-1'.
        10. A list of substructures, which contain data very similar to sections 3-6.

    Completion status
    ------
    (o) AnimReader can successfully parse all anim files in DSDB archive within current constraints.
    (x) AnimReader cannot yet fully interpret all anim data in DSDB archive.
    (o) AnimReader can write data to anim files.

    Current hypotheses and observations
    ------
    1.  Sections 3-6 (functions in the code are labelled rw_part_2 though to 6) appear to be part of the same data
        structure: the same structure appears twice in every subreader.
        This presumably describes a keyframe; perhaps the first structure describes the initial pose whereas the ones
        that come later describe poses to interpolate through for the animation.
    2.  Sections 4, 5, 6 might therefore be position, rotation, and scale.
    3.  Section 8 contains a cumulative count plus and increment: this might state which keyframe the animation data is
        attached to and the gap until the next keyframe.
    4.  If the above hypothesis is correct, this would make each substructure a pose delta defined for each keyframe.
    """
    def __init__(self, bytestream, skelReader):
        super().__init__(bytestream)
        self.skelReader = skelReader

        # Header variables
        self.filetype = None
        self.unknown_0x04 = None  # Float?
        self.unknown_0x06 = None  # Float?
        self.unknown_0x08 = None  # Float?
        self.unknown_0x0A = None  # Float?

        self.unknown_0x0C = None  # Specifies the end of the initial data chunks
        self.num_bones = None
        self.unknown_0x10 = None  # 1 more than the final count in part 6: total frames in animation?
        self.unknown_0x12 = None  # part 5 is 8x this count, part 6 is 4x this count: count of UnknownAnimSubstructures. Presumably total # of keyframes.
        self.always_16384 = None  # Always 16384; maybe a section terminator, maybe the precision of the rotations

        self.initial_pose_bone_rotations_count = None  # part 1 is 6x this count, counts bone idxs
        self.initial_pose_bone_locations_count = None  # part 2 is 12x this count, counts bone idxs
        self.initial_pose_bone_scales_count = None  # part 3 is 12x this count, counts bone idxs
        self.unknown_0x1C = None  # part 4 is 4x this count, counts bone idxs
        self.keyframe_bone_rotations_count = None  # part 1 of subreaders is 6x this count, counts bone idxs
        self.keyframe_bone_locations_count = None  # part 2 of subreaders is 12x this count,counts bone idxs
        self.keyframe_bone_scales_count = None  # part 3 of subreaders is 12x this count,counts bone idxs
        self.unknown_0x24 = None  # part 4 of subreaders is 4x this count, counts bone idxs
        self.padding_0x26 = None  # Always 0
        self.unknown_0x28 = None  # Specifies the number of cleanup bytes after the initial data chunks
        self.unknown_0x2C = None  # Specifies the end of the initial data chunks if cleanup bytes required

        self.unknown_0x30 = None  # Relative ptr
        self.unknown_0x34 = None  # Relative ptr
        self.rel_ptr_initial_pose_bone_rotations = None  # Relative ptr
        self.rel_ptr_initial_pose_bone_locations = None  # Relative ptr
        self.rel_ptr_initial_pose_bone_scales = None  # Relative ptr
        self.unknown_0x44 = None  # Relative ptr

        self.padding_0x48 = None
        self.padding_0x4C = None
        self.padding_0x50 = None
        self.padding_0x54 = None
        self.padding_0x58 = None
        self.padding_0x5C = None

        # Utility variables
        self.abs_ptr_part_5 = None
        self.abs_ptr_part_6 = None
        self.abs_ptr_initial_pose_bone_rotations = None
        self.abs_ptr_initial_pose_bone_locations = None
        self.abs_ptr_initial_pose_bone_scales = None
        self.abs_ptr_part_4 = None

        # Data holders
        self.initial_pose_rotations_bone_idxs = None
        self.initial_pose_locations_bone_idxs = None
        self.initial_pose_scales_bone_idxs = None
        self.unknown_bone_idxs_4 = None
        self.keyframe_rotations_bone_idxs = None
        self.keyframe_locations_bone_idxs = None
        self.keyframe_scales_bone_idxs = None
        self.unknown_bone_idxs_8 = None

        self.initial_pose_bone_rotations = None
        self.initial_pose_bone_locations = None
        self.initial_pose_bone_scales = None
        self.unknown_data_4 = None
        self.unknown_data_5 = None
        self.keyframe_counts = None
        self.unknown_data_7 = None
        self.unknown_data_7b = None
        self.unknown_data_8 = None
        
        self.max_val_1 = None
        self.max_val_2 = None

    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.read_ascii, self.maxval_read, "read", self.prepare_read_op, self.cleanup_ragged_chunk_read)
        self.interpret_animdata()

    def write(self):
        self.reinterpret_animdata()
        self.read_write(self.write_buffer, self.write_raw, self.write_ascii, self.maxval_write, "write", lambda: None, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_operator_raw, rw_operator_ascii, maxval_op, rw_method_name, preparation_op, chunk_cleanup_operator):
        self.rw_header(rw_operator, rw_operator_ascii)
        preparation_op()
        self.rw_bone_idx_lists(rw_operator, maxval_op, chunk_cleanup_operator)
        self.rw_initial_pose_bone_rotations(rw_operator_raw, chunk_cleanup_operator)
        self.rw_initial_pose_bone_locations(rw_operator, chunk_cleanup_operator)
        self.rw_initial_pose_bone_scales(rw_operator)
        self.rw_part_4(rw_operator, chunk_cleanup_operator)
        self.rw_part_5(rw_operator)
        self.rw_keyframes_per_substructure(rw_operator, chunk_cleanup_operator)
        self.rw_part_7(rw_operator, chunk_cleanup_operator)
        self.rw_part_8(rw_method_name)

    def rw_header(self, rw_operator, rw_operator_ascii):
        self.assert_file_pointer_now_at(0)
        rw_operator_ascii('filetype', 4)

        rw_operator('unknown_0x04', 'f')
        #rw_operator('unknown_0x06', 'BB')
        rw_operator('unknown_0x08', 'f')
        #rw_operator('unknown_0x0A', 'BB')

        rw_operator('unknown_0x0C', 'H')
        rw_operator('num_bones', 'H')
        rw_operator('unknown_0x10', 'H')
        rw_operator('unknown_0x12', 'H')
        rw_operator('always_16384', 'H')  # Maybe this is the precision of the quaternions?
        self.assert_equal('always_16384', 16384)
        assert self.always_16384 == 16384, self.always_16384

        rw_operator('initial_pose_bone_rotations_count', 'H')
        rw_operator('initial_pose_bone_locations_count', 'H')
        rw_operator('initial_pose_bone_scales_count', 'H')
        rw_operator('unknown_0x1C', 'H')
        rw_operator('keyframe_bone_rotations_count', 'H')
        rw_operator('keyframe_bone_locations_count', 'H')
        rw_operator('keyframe_bone_scales_count', 'H')
        rw_operator('unknown_0x24', 'H')
        rw_operator('padding_0x26', 'H')
        self.assert_is_zero('padding_0x26')

        rw_operator('unknown_0x28', 'I')
        rw_operator('unknown_0x2C', 'I')
        if self.unknown_0x28 != 0:
            self.assert_equal('unknown_0x2C', self.unknown_0x0C)

        pos = self.bytestream.tell()
        rw_operator('unknown_0x30', 'I')
        self.abs_ptr_part_5 = pos + self.unknown_0x30
        pos = self.bytestream.tell()
        rw_operator('unknown_0x34', 'I')
        self.abs_ptr_part_6 = pos + self.unknown_0x34
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_initial_pose_bone_rotations', 'I')
        self.abs_ptr_initial_pose_bone_rotations = pos + self.rel_ptr_initial_pose_bone_rotations
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_initial_pose_bone_locations', 'I')
        self.abs_ptr_initial_pose_bone_locations = pos + self.rel_ptr_initial_pose_bone_locations
        pos = self.bytestream.tell()
        rw_operator('rel_ptr_initial_pose_bone_scales', 'I')
        self.abs_ptr_initial_pose_bone_scales = pos + self.rel_ptr_initial_pose_bone_scales
        pos = self.bytestream.tell()
        rw_operator('unknown_0x44', 'I')
        self.abs_ptr_part_4 = pos + self.unknown_0x44

        rw_operator('padding_0x48', 'I')
        rw_operator('padding_0x4C', 'I')
        rw_operator('padding_0x50', 'I')
        rw_operator('padding_0x54', 'I')
        rw_operator('padding_0x58', 'I')
        rw_operator('padding_0x5C', 'I')

    def maxval_read(self, val, key):
        n2r = (8 - getattr(self, key)* 2 % 8) % 8
        self.read_raw(val, n2r)

        res_1 = struct.unpack('H' * (len(getattr(self, val)) // 2), getattr(self, val))
        if len(res_1):
            setattr(self, val, res_1[0])
        else:
            setattr(self, val, 0)

    def maxval_write(self, val, key):
        n2w = (8 - getattr(self, key) * 2 % 8) % 8
        n2w //= 2
        backup = getattr(self, val)
        setattr(self, val, struct.pack('H'*n2w, *([backup]*n2w)))
        self.write_raw(val, n2w*2)
        setattr(self, val, backup)

    def rw_bone_idx_lists(self, rw_operator, maxval_op, chunk_cleanup_operator):
        """
        # Eight lists of indices
        # First three are bone indices that correspond to entries in unknown_data_1-3
        # Fourth is the count of an unknown variable; total number is the sum of two counts and also 0x0C in the skel file
        # Next three are bone indices corresponding to sections of data analogous to unknown_data_1-3, but in each
        # UnknownAnimSubstructure
        # Eighth is similar to #4 but in every UnknownAnimSubstructure
        """
        rw_operator('initial_pose_rotations_bone_idxs', self.initial_pose_bone_rotations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.initial_pose_bone_rotations_count * 2, 16, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('initial_pose_locations_bone_idxs', self.initial_pose_bone_locations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.initial_pose_bone_locations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('initial_pose_scales_bone_idxs', self.initial_pose_bone_scales_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.initial_pose_bone_scales_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('unknown_bone_idxs_4', self.unknown_0x1C*'H', force_1d=True)
        # Cleanup value is max element
        maxval_op("max_val_1", "unknown_0x1C")

        rw_operator('keyframe_rotations_bone_idxs', self.keyframe_bone_rotations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.keyframe_bone_rotations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('keyframe_locations_bone_idxs', self.keyframe_bone_locations_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.keyframe_bone_locations_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('keyframe_scales_bone_idxs', self.keyframe_bone_scales_count * 'H', force_1d=True)
        chunk_cleanup_operator(self.keyframe_bone_scales_count * 2, 8, stepsize=2, bytevalue=struct.pack('H', self.num_bones))
        rw_operator('unknown_bone_idxs_8', self.unknown_0x24*'H', force_1d=True)
        #chunk_cleanup_operator(self.unknown_0x24*2, 8, stepsize=2, bytevalue=struct.pack('H', self.skelReader.unknown_0x0C))
        maxval_op("max_val_2", "unknown_0x24")
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_rotations(self, rw_operator_raw, chunk_cleanup_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_initial_pose_bone_rotations)
        rw_operator_raw('initial_pose_bone_rotations', 6 * self.initial_pose_bone_rotations_count)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_locations(self, rw_operator, chunk_cleanup_operator):
        """
        # 12 bytes assigned to each bone in unknown_bone_idxs_2
        # this is a triplet of floats
        """
        self.assert_file_pointer_now_at(self.abs_ptr_initial_pose_bone_locations)
        rw_operator('initial_pose_bone_locations', 'fff' * self.initial_pose_bone_locations_count)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_initial_pose_bone_scales(self, rw_operator):
        """
        # 12 bytes assigned to each bone in unknown_bone_idxs_3
        # this is a triplet of floats
        """
        self.assert_file_pointer_now_at(self.abs_ptr_initial_pose_bone_scales)
        rw_operator('initial_pose_bone_scales', 'fff' * self.initial_pose_bone_scales_count)

    def rw_part_4(self, rw_operator, chunk_cleanup_operator):
        """
        # 4 bytes assigned to each idx in unknown_bone_idxs_4
        # Probably texture UVs
        """
        self.assert_file_pointer_now_at(self.abs_ptr_part_4)
        rw_operator('unknown_data_4', 'f'*self.unknown_0x1C, force_1d=True)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_part_5(self, rw_operator):
        """
        # Says where the UnknownDataReaders start
        # Format is (0, length, pointer)
        # pointer is the absolute pointer to the start of the UnknownDataReader
        # 'length' is the number of bytes the UnknownDataReader contains, plus the number of bytes from the end of the
        # final data reader to the end of the file (WHY?!!?!)
        """
        self.assert_file_pointer_now_at(self.abs_ptr_part_5)
        rw_operator('unknown_data_5', 'HHI'*self.unknown_0x12)

    def rw_keyframes_per_substructure(self, rw_operator, chunk_cleanup_operator):
        """
        # In the format (cumulative_count, increment)
        # Presumably the total count of frames and the gap between each keyframe
        """
        self.assert_file_pointer_now_at(self.abs_ptr_part_6)
        rw_operator('keyframe_counts', 'HH'*self.unknown_0x12)
        chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_part_7(self, rw_operator, chunk_cleanup_operator):
        """
        Contains 0 or -1 for each bone: If 0, that bone isn't given any location data in the file
        Same for whatever goes in unknown_data_7b - that other set of indices that are unknown
        """
        self.assert_file_pointer_now_at(self.unknown_0x0C)
        num_to_read = max([self.skelReader.unknown_0x0C, self.max_val_1, self.max_val_2])
        #num_to_read = max([self.max_val_1, self.max_val_2])
        tell = self.bytestream.tell()
        if self.unknown_0x28 != 0:
            self.header = list(self.header)
            self.header.insert(20, self.bytestream.tell())

            rw_operator('unknown_data_7', 'b'*(self.num_bones))
            chunk_cleanup_operator(self.bytestream.tell(), 4)

        if (self.unknown_0x28 - (self.bytestream.tell() - tell)) > 0:
            rw_operator('unknown_data_7b', 'b'*(num_to_read))
            chunk_cleanup_operator(self.bytestream.tell(), 4)

            #rw_operator('unknown_data_7', 'b'*self.num_bones)
            #chunk_cleanup_operator(self.num_bones, self.unknown_0x28)
            # Should work, but doesn't?! How is unknown_0x28 calculated if it isn't a roundup of the number of bones?!
        if self.unknown_0x28 != 0:
            chunk_cleanup_operator(self.bytestream.tell(), 16)

    def rw_part_8(self, rw_method_name):
        for i, (unkdatareader, d5, d6) in enumerate(zip(self.unknown_data_8, self.chunk_list(self.unknown_data_5, 3),
                                                        self.chunk_list(self.keyframe_counts, 2))):
            #print(i, self.unknown_data_7, self.unknown_0x28, self.num_bones)
            # Currently misses off the final reader; will be fine once length is calculable
            assert d5[0] == 0
            scale_factor = (self.keyframe_bone_rotations_count + self.keyframe_bone_locations_count + self.keyframe_bone_scales_count + self.unknown_0x24) / 8
            part5_size = int(np.ceil(scale_factor * d6[1]))
            unkdatareader.initialise_variables(self.keyframe_bone_rotations_count, self.keyframe_bone_locations_count, self.keyframe_bone_scales_count, self.unknown_0x24, d5[-1], part5_size, d6[1])
            getattr(unkdatareader, rw_method_name)()

    def prepare_read_op(self):
        self.unknown_data_8 = [UnknownAnimSubstructure(self.bytestream) for _ in range(self.unknown_0x12)]

    def interpret_animdata(self):
        self.initial_pose_bone_rotations = self.chunk_list(self.initial_pose_bone_rotations, 6)
        self.initial_pose_bone_rotations = [deserialise_quaternion(elem) for elem in self.initial_pose_bone_rotations]
        self.initial_pose_bone_locations = self.chunk_list(self.initial_pose_bone_locations, 3)
        self.initial_pose_bone_scales = self.chunk_list(self.initial_pose_bone_scales, 3)

        self.unknown_data_5 = self.chunk_list(self.unknown_data_5, 3)
        self.keyframe_counts = self.chunk_list(self.keyframe_counts, 2)

    def reinterpret_animdata(self):
        self.initial_pose_bone_rotations = [serialise_quaternion(elem) for elem in self.initial_pose_bone_rotations]
        self.initial_pose_bone_rotations = b''.join(self.initial_pose_bone_rotations)
        self.initial_pose_bone_locations = self.flatten_list(self.initial_pose_bone_locations)
        self.initial_pose_bone_scales = self.flatten_list(self.initial_pose_bone_scales)

        self.unknown_data_5 = self.flatten_list(self.unknown_data_5)
        self.keyframe_counts = self.flatten_list(self.keyframe_counts)


class UnknownAnimSubstructure(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)

        # Header variables
        self.unknown_0x00 = None  # Size of part 1; divisible by 6
        self.unknown_0x02 = None  # Size of part 2; divisible by 12
        self.unknown_0x04 = None  # Size of part 3; divisible by 12 + enough bytes to make total so far divisible by 4
        self.unknown_0x06 = None  # Size of part 4; divisible by 4
        self.unknown_0x08 = None  # Size of part 6; divisible by 6
        self.unknown_0x0A = None  # Size of part 7; divisible by 12
        self.unknown_0x0C = None  # Size of part 8; divisible by 12 + enough bytes to make total so far divisible by 4
        self.unknown_0x0E = None  # Size of part 9; divisible by 4

        # Data holders
        self.unknown_data_1 = None  # Contains 6 bytes per entry, dtype smallest-3 quaternion with uint15s. Count in parent header.
        self.unknown_data_2 = None  # Contains 12 bytes per entry, dtype fff. Count in parent header.
        self.unknown_data_3 = None  # Contains 12 bytes per entry, dtype fff. Count in parent header.
        self.unknown_data_4 = None  # Contains 4 bytes per entry, dtype f(?). Count in parent header.
        self.unknown_data_5 = None  # Bit-packed booleans stating which keyframes are in use
        self.unknown_data_6 = None  # Contains 6 bytes per entry, dtype smallest-3 quaternion with uint15s. Count in parent header.
        self.unknown_data_7 = None  # Contains 12 bytes per entry, dtype fff. Count unknown.
        self.unknown_data_8 = None  # Contains 12 bytes per entry, dtype fff. Count unknown.
        self.unknown_data_9 = None  # Contains 4 bytes per entry, dtype f(?). Count unknown.

        # Utility variables
        self.bytes_read = 0

    def initialise_variables(self, part_1_count, part_2_count, part_3_count, part_4_count, start_pointer, part5_size, nframes):
        self.part_1_count = part_1_count
        self.part_2_count = part_2_count
        self.part_3_count = part_3_count
        self.part_4_count = part_4_count
        self.start_pointer = start_pointer
        # Temp variable
        self.part5_size = part5_size
        self.nframes = nframes

    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.cleanup_ragged_chunk_read)
        self.interpret_frame()

    def read_write(self, rw_operator, rw_operator_raw, cleanup_chunk_operator):
        self.rw_header(rw_operator)
        self.rw_part_1(rw_operator, cleanup_chunk_operator)
        self.rw_part_2(rw_operator, cleanup_chunk_operator)
        self.rw_part_3(rw_operator, cleanup_chunk_operator)
        self.rw_part_4(rw_operator, cleanup_chunk_operator)

        self.rw_part_5(rw_operator_raw)

        self.rw_part_6(rw_operator, cleanup_chunk_operator)
        self.rw_part_7(rw_operator, cleanup_chunk_operator)
        self.rw_part_8(rw_operator, cleanup_chunk_operator)
        self.rw_part_9(rw_operator, cleanup_chunk_operator)

        cleanup_chunk_operator(self.bytestream.tell(), 16)

    def rw_header(self, rw_operator):
        self.assert_file_pointer_now_at(self.start_pointer)
        rw_operator('unknown_0x00', 'H')
        rw_operator('unknown_0x02', 'H')
        rw_operator('unknown_0x04', 'H')
        rw_operator('unknown_0x06', 'H')

        rw_operator('unknown_0x08', 'H')
        rw_operator('unknown_0x0A', 'H')
        rw_operator('unknown_0x0C', 'H')
        rw_operator('unknown_0x0E', 'H')

        self.bytes_read += 16

    def rw_part_1(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_1', 'bbbbbb'*self.part_1_count)

        self.bytes_read += self.unknown_0x00

    def rw_part_2(self, rw_operator, cleanup_chunk_operator):
        # Entries are ~0.01 - 0.00001
        rw_operator('unknown_data_2', 'fff'*self.part_2_count)

        self.bytes_read += self.unknown_0x02

    def rw_part_3(self, rw_operator, cleanup_chunk_operator):
        # Each entry is ~1? (c.f. pc002_fc01)
        rw_operator('unknown_data_3', 'fff'*self.part_3_count)
        if self.unknown_0x04 != 0:
            cleanup_chunk_operator(self.bytes_read, 4)

        self.bytes_read += self.unknown_0x04

    def rw_part_4(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_4', 'f'*self.part_4_count, force_1d=True)

        self.bytes_read += self.unknown_0x06

    def rw_part_5(self, rw_operator_raw):
        """
        This is a bit-string denoting keyframes
        """
        rw_operator_raw('unknown_data_5', self.part5_size)

        self.bytes_read += self.part5_size

    def rw_part_6(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_6', 'bbbbbb' * (self.unknown_0x08//6))

        self.bytes_read += self.unknown_0x08

    def rw_part_7(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_7', 'eHeHeH' * (self.unknown_0x0A//12))

        self.bytes_read += self.unknown_0x0A

    def rw_part_8(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_8', 'fff' * (self.unknown_0x0C//12))
        if self.unknown_0x0C != 0:
            cleanup_chunk_operator(self.bytes_read, 4)

        self.bytes_read += self.unknown_0x0C

    def rw_part_9(self, rw_operator, cleanup_chunk_operator):
        rw_operator('unknown_data_9', 'f' * (self.unknown_0x0E//4), force_1d=True)

        self.bytes_read += self.unknown_0x0E

    def interpret_frame(self):
        self.unknown_data_1 = self.chunk_list(self.unknown_data_1, 6)
        self.unknown_data_2 = self.chunk_list(self.unknown_data_2, 3)
        self.unknown_data_3 = self.chunk_list(self.unknown_data_3, 3)

        self.unknown_data_6 = self.chunk_list(self.unknown_data_6, 6)
        self.unknown_data_7 = self.chunk_list(self.unknown_data_7, 6)
        self.unknown_data_8 = self.chunk_list(self.unknown_data_8, 3)
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def bytes_to_bits(bytelist):
    return ("{:0" + str(len(bytelist) * 8) + "b}").format(int(bytelist.hex(), 16))


def bits_to_bytes(bitstring):
    return b''.join([struct.pack('B', (int(elem, 2))) for elem in chunks(bitstring, 8)])


def deserialise_quaternion(dscs_rotation):
    bit_representation = bytes_to_bits(dscs_rotation)
    largest_index = struct.unpack('>B', bits_to_bytes('000000' + bit_representation[46:48]))
    component_bits = bit_representation[1:46]
    component_bits = ''.join(['0'+component_bits[15*i:15*(i+1)] for i in range(3)])
    components = np.array(struct.unpack('>HHH', bits_to_bytes(component_bits)))

    components -= 16383
    components = components/16384
    components *= 1/np.sqrt(2)

    square_vector_length = np.sum(components**2)
    largest_component = np.sqrt(1 - square_vector_length)

    # This is in the XYZW ordering
    components = np.insert(components, largest_index, largest_component)

    # Now it's in the WXYZ ordering
    quaternion = np.roll(components, 1)

    return quaternion


def serialise_quaternion(quat):
    # Start from WXYZ ordering, put it into XYZW
    components = np.roll(quat, -1)
    largest_component = np.amax(components)
    largest_index = np.where(components == largest_component)
    largest_component_sign = np.sign(largest_component)

    # Get rid of the largest component
    # No need to store the sign of the largest component, because
    # (W, X, Y, Z) = (-W, -X, -Y, -Z)
    # So just multiply through by the sign of the removed component to create an equivalent quaternion
    # In this way, the largest component is always +ve
    components = largest_component_sign*np.delete(components, largest_index)
    # Map the remaining components from the interval [-1/sqrt(2), 1/sqrt(2)] to [0, 32767]
    components *= np.sqrt(2)
    components *= 16384
    components = np.around(components).astype(np.int)
    components += 16383
    for i, elem in enumerate(components):
        if elem < 0:
            components[i] = 0
        elif elem > 32767:
            components[i] = 32767

    # Now convert to big-endian uint15s
    component_bits = bytes_to_bits(struct.pack('>HHH', components))
    component_bits = ''.join([component_bits[16*i + 1:16*(i+1)] for i in range(3)])

    # Store the largest index as a uint2
    largest_index_bits = bytes_to_bits(struct.pack('>B', largest_index))[6:]

    # Put everything together
    component_bits = '0' + component_bits + largest_index_bits

    return bits_to_bytes(component_bits)
