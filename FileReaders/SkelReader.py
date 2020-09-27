from .BaseRW import BaseRW


class SkelReader(BaseRW):
    """
    A class to read skel files. These files are split into seven main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. Pairs of bone indices that seem to have something to do with parent-child relationships.
        3. A section of 16 floats per bone
        4. A section of 1 int16 per bone that gives the parent of each bone
        5. A section of currently incalculable length, that contains multiples of 8
        6. A section of 1 (u?)int32 per unknown_0x0C
        7. A section of unknown data plus pad bytes

    Completion status
    ------
    (o) SkelReader can successfully parse all name files in DSDB archive within current constraints.
    (x) SkelReader cannot yet fully interpret all data in name files in DSDB archive.
    (x) SkelReader cannot yet write data to skel files.

    Current hypotheses and observations
    ------
    1. There may be a section containing IK data.
    2. There may be a section containing bone constraints.
    """
    def __init__(self, io_object):
        super().__init__(io_object)

        # Variables that appear in the file header
        self.filetype = None
        self.total_bytes = None
        self.remaining_bytes_after_parent_bones_chunk = None
        self.num_bones = None
        self.unknown_0x0C = None
        self.num_unknown_parent_child_data = None

        self.rel_ptr_to_end_of_unknown_parent_child_data = None
        self.rel_ptr_to_end_of_bone_defs = None
        self.rel_ptr_to_end_of_parent_bones_chunk = None
        self.unknown_rel_ptr_2 = None
        self.unknown_rel_ptr_3 = None
        self.rel_ptr_to_end_of_parent_bones = None

        self.padding_0x26 = None
        self.padding_0x2A = None
        self.padding_0x2E = None
        self.padding_0x32 = None

        # These hold the data stored within the file
        self.unknown_parent_child_data = None
        self.bone_data = None
        self.parent_bones = None
        self.parent_bones_junk = None
        self.unknown_data_2 = None
        self.unknown_data_3 = None
        self.unknown_data_4 = None

        # Utility variables
        self.filesize = None

        self.abs_ptr_unknown_parent_child_data = None
        self.abs_ptr_bone_defs = None
        self.abs_ptr_parent_bones = None
        self.abs_ptr_end_of_parent_bones_junk = None
        self.abs_ptr_unknown_2 = None
        self.abs_ptr_unknown_3 = None
        self.abs_ptr_unknown_4 = None

    def read(self):
        self.read_header()
        self.read_unknown_parent_child_data()
        self.read_bone_data()
        self.read_parent_bones()
        self.read_parent_bone_padding()
        self.read_unknown_data_2()
        self.read_unknown_data_3()
        self.read_unknown_data_4()

    def read_header(self):
        self.assert_file_pointer_now_at(0)

        self.filetype = self.bytestream.read(4).decode("ascii")
        self.assert_equal("filetype", "20SE")
        self.total_bytes = self.unpack('Q')
        self.remaining_bytes_after_parent_bones_chunk = self.unpack('I')
        self.num_bones = self.unpack('H')
        self.unknown_0x0C = self.unpack('H')
        self.num_unknown_parent_child_data = self.unpack('I')

        upcd_pos = self.bytestream.tell()
        self.rel_ptr_to_end_of_unknown_parent_child_data = self.unpack('I')
        bonedefs_pos = self.bytestream.tell()
        self.rel_ptr_to_end_of_bone_defs = self.unpack('I')
        pb_chunk_ptr_pos = self.bytestream.tell()
        self.rel_ptr_to_end_of_parent_bones_chunk = self.unpack('I')
        unk2_pos = self.bytestream.tell()
        self.unknown_rel_ptr_2 = self.unpack('I')
        unk3_pos = self.bytestream.tell()
        self.unknown_rel_ptr_3 = self.unpack('I')
        pcp_pos = self.bytestream.tell()
        self.rel_ptr_to_end_of_parent_bones = self.unpack('I')

        self.padding_0x26 = self.unpack('I')
        self.assert_is_zero("padding_0x26")
        self.padding_0x2A = self.unpack('I')
        self.assert_is_zero("padding_0x2A")
        self.padding_0x2E = self.unpack('I')
        self.assert_is_zero("padding_0x2E")
        self.padding_0x32 = self.unpack('I')
        self.assert_is_zero("padding_0x32")

        self.abs_ptr_unknown_parent_child_data = upcd_pos + self.rel_ptr_to_end_of_unknown_parent_child_data - (self.num_unknown_parent_child_data * 16)
        self.abs_ptr_bone_defs = bonedefs_pos + self.rel_ptr_to_end_of_bone_defs - (self.num_bones * 12 * 4)
        self.abs_ptr_parent_bones = pcp_pos + self.rel_ptr_to_end_of_parent_bones - self.num_bones * 2
        self.abs_ptr_end_of_parent_bones_junk = pb_chunk_ptr_pos + self.rel_ptr_to_end_of_parent_bones_chunk
        self.abs_ptr_unknown_2 = unk2_pos + self.unknown_rel_ptr_2 - self.num_bones * 4
        self.abs_ptr_unknown_3 = unk3_pos + self.unknown_rel_ptr_3 - self.unknown_0x0C * 4

        self.assert_equal("total_bytes", self.abs_ptr_unknown_2 + self.remaining_bytes_after_parent_bones_chunk)

    def read_unknown_parent_child_data(self):
        # Seems to contain the same info as the parent_bones with repeats and bugs..?
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_parent_child_data)
        bytes_to_read = self.num_unknown_parent_child_data * 16
        joint_data = self.decode_data_as('h', self.bytestream.read(bytes_to_read))
        self.unknown_parent_child_data = [(child, parent) for child, parent in zip(joint_data[::2], joint_data[1::2])]

    def read_bone_data(self):
        self.assert_file_pointer_now_at(self.abs_ptr_bone_defs)
        bytes_to_read = self.num_bones * 12 * 4
        self.bone_data = self.decode_data_as_chunks('f', self.bytestream.read(bytes_to_read), 12)

    def read_parent_bones(self):
        self.assert_file_pointer_now_at(self.abs_ptr_parent_bones)
        bytes_to_read = self.num_bones * 2
        parents = self.decode_data_as('h', self.bytestream.read(bytes_to_read))
        self.parent_bones = [(i, idx) for i, idx in enumerate(parents)]

        # Basic error checking - make sure no bone idx exceeds the known number of bones
        if len(self.parent_bones) != 0:
            max_idx = max([subitem for item in self.parent_bones for subitem in item])
        else:
            max_idx = -1
        assert max_idx == self.num_bones - 1, f'{max_idx}, {self.num_bones - 1}'

    def read_parent_bone_padding(self):
        cur_pos = self.bytestream.tell()
        # (16 - (num_bones*2) % 16) % 16 works for bytes_remaining_after_parent_child_pairs <= 32... sometimes for more
        # Need to be able to calculate the size and contents in order for the write to work...
        bytes_to_read = self.abs_ptr_end_of_parent_bones_junk - cur_pos  # could equally just use abs_ptr_unknown_2...
        self.parent_bones_junk = self.bytestream.read(bytes_to_read)
        # Interesting that the bytes are multiples of 8 - does this have some significance?!
        for byte in self.parent_bones_junk:
            assert byte == 0 or byte == 8 or byte == 16, self.parent_bones_junk

    def read_unknown_data_2(self):
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_2)
        bytes_to_read = self.num_bones * 4
        # B, H, I, e, f all seem to give nonsensical results...
        # Changing the endianness doesn't help
        self.unknown_data_2 = self.bytestream.read(bytes_to_read)#self.decode_data_as('I', self.bytestream.read(bytes_to_read), endianness='>')

    def read_unknown_data_3(self):
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_3)
        bytes_to_read = self.unknown_0x0C * 4
        # Looks like uint32s, no idea what these are for though.
        self.unknown_data_3 = self.decode_data_as('I', self.bytestream.read(bytes_to_read))

    def read_unknown_data_4(self):
        # Contains some information (?) and pad bytes
        self.unknown_data_4 = self.bytestream.read()
