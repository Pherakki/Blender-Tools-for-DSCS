from .BaseRW import BaseRW


class SkelReader(BaseRW):
    """
    A class to read skel files. These files are split into seven main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. Pairs of bone indices that seem to have something to do with parent-child relationships, 8 int16s per element
        3. A section of 12 floats per bone
        4. A section of 1 int16 per bone that gives the parent of each bone
        5. A section of currently incalculable length, that contains multiples of 8
        6. A section of 1 (u?)int32 per unknown_0x0C
        7. A section of unknown data plus pad bytes

    Completion status
    ------
    (o) SkelReader can successfully parse all name files in DSDB archive within current constraints.
    (x) SkelReader cannot yet fully interpret all data in name files in DSDB archive.
    (o) SkelReader can write data to skel files.

    Current hypotheses and observations
    ------
    1. There may be a section containing IK data.
    2. There may be a section containing bone constraints.
    3. The above two may instead be in the anim file, if they exist at all
    """
    def __init__(self, io_stream):
        super().__init__(io_stream)

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
        self.read_write(self.read_buffer, self.read_ascii, self.read_raw)
        self.interpret_skel_data()

    def write(self):
        self.reinterpret_skel_data()
        self.read_write(self.write_buffer, self.write_ascii, self.write_raw)

    def read_write(self, rw_operator, rw_operator_ascii, rw_operator_raw):
        self.rw_header(rw_operator, rw_operator_ascii)
        self.rw_unknown_parent_child_data(rw_operator)
        self.rw_bone_data(rw_operator)
        self.rw_parent_bones(rw_operator)
        self.rw_parent_bone_padding(rw_operator_raw)
        self.rw_unknown_data_2(rw_operator_raw)
        self.rw_unknown_data_3(rw_operator)
        self.rw_unknown_data_4(rw_operator_raw)

    def rw_header(self, rw_operator, rw_operator_ascii):
        self.assert_file_pointer_now_at(0)

        rw_operator_ascii('filetype', 4)
        self.assert_equal("filetype", "20SE")
        rw_operator('total_bytes', 'Q')
        rw_operator('remaining_bytes_after_parent_bones_chunk', 'I')
        rw_operator('num_bones',  'H')
        rw_operator('unknown_0x0C', 'H')
        rw_operator('num_unknown_parent_child_data', 'I')

        upcd_pos = self.bytestream.tell()
        rw_operator('rel_ptr_to_end_of_unknown_parent_child_data', 'I')
        bonedefs_pos = self.bytestream.tell()
        rw_operator('rel_ptr_to_end_of_bone_defs', 'I')
        pb_chunk_ptr_pos = self.bytestream.tell()
        rw_operator('rel_ptr_to_end_of_parent_bones_chunk', 'I')
        unk2_pos = self.bytestream.tell()
        rw_operator('unknown_rel_ptr_2', 'I')
        unk3_pos = self.bytestream.tell()
        rw_operator('unknown_rel_ptr_3', 'I')
        pcp_pos = self.bytestream.tell()
        rw_operator('rel_ptr_to_end_of_parent_bones', 'I')

        rw_operator('padding_0x26', 'I')
        self.assert_is_zero("padding_0x26")
        rw_operator('padding_0x2A', 'I')
        self.assert_is_zero("padding_0x2A")
        rw_operator('padding_0x2E', 'I')
        self.assert_is_zero("padding_0x2E")
        rw_operator('padding_0x32', 'I')
        self.assert_is_zero("padding_0x32")

        self.abs_ptr_unknown_parent_child_data = upcd_pos + self.rel_ptr_to_end_of_unknown_parent_child_data - (self.num_unknown_parent_child_data * 16)
        self.abs_ptr_bone_defs = bonedefs_pos + self.rel_ptr_to_end_of_bone_defs - (self.num_bones * 12 * 4)
        self.abs_ptr_parent_bones = pcp_pos + self.rel_ptr_to_end_of_parent_bones - self.num_bones * 2
        self.abs_ptr_end_of_parent_bones_junk = pb_chunk_ptr_pos + self.rel_ptr_to_end_of_parent_bones_chunk
        self.abs_ptr_unknown_2 = unk2_pos + self.unknown_rel_ptr_2 - self.num_bones * 4
        self.abs_ptr_unknown_3 = unk3_pos + self.unknown_rel_ptr_3 - self.unknown_0x0C * 4

        self.assert_equal("total_bytes", self.abs_ptr_unknown_2 + self.remaining_bytes_after_parent_bones_chunk)

    def rw_unknown_parent_child_data(self, rw_operator):
        # Seems to contain the same info as the parent_bones with repeats and bugs..?
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_parent_child_data)
        int16s_to_read = self.num_unknown_parent_child_data * 8
        rw_operator('unknown_parent_child_data', 'h'*int16s_to_read)
        #joint_data = self.decode_data_as('h', self.bytestream.read(bytes_to_read))
        #self.unknown_parent_child_data = [(child, parent) for child, parent in zip(joint_data[::2], joint_data[1::2])]

    def rw_bone_data(self, rw_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_bone_defs)
        floats_to_read = self.num_bones * 12  # * 4
        rw_operator('bone_data', 'f'*floats_to_read)
        #self.bone_data = self.decode_data_as_chunks('f', self.bytestream.read(bytes_to_read), 12)

    def rw_parent_bones(self, rw_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_parent_bones)
        rw_operator('parent_bones', 'h'*self.num_bones)
        #self.parent_bones = [(i, idx) for i, idx in enumerate(parents)]

    def rw_parent_bone_padding(self, rw_operator_raw):
        cur_pos = self.bytestream.tell()
        # (16 - (num_bones*2) % 16) % 16 works for bytes_remaining_after_parent_child_pairs <= 32... sometimes for more
        # Need to be able to calculate the size and contents in order for the write to work...
        bytes_to_read = self.abs_ptr_end_of_parent_bones_junk - cur_pos  # could equally just use abs_ptr_unknown_2...
        rw_operator_raw('parent_bones_junk', bytes_to_read)
        # Interesting that the bytes are multiples of 8 - does this have some significance?!
        for byte in self.parent_bones_junk:
            assert byte == 0 or byte == 8 or byte == 16, self.parent_bones_junk

    def rw_unknown_data_2(self, rw_operator_raw):
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_2)
        bytes_to_read = self.num_bones * 4
        # B, H, I, e, f all seem to give nonsensical results...
        # Changing the endianness doesn't help
        rw_operator_raw('unknown_data_2', bytes_to_read)  # self.decode_data_as('I', self.bytestream.read(bytes_to_read), endianness='>')

    def rw_unknown_data_3(self, rw_operator):
        self.assert_file_pointer_now_at(self.abs_ptr_unknown_3)
        #bytes_to_read = self.unknown_0x0C * 4
        # Looks like uint32s, no idea what these are for though.
        rw_operator('unknown_data_3', 'I'*self.unknown_0x0C)

    def rw_unknown_data_4(self, rw_operator_raw):
        # Contains some information (?) and pad bytes
        rw_operator_raw('unknown_data_4')

    def interpret_skel_data(self):
        self.unknown_parent_child_data = self.chunk_list(self.unknown_parent_child_data, 8)
        self.bone_data = self.chunk_list(self.bone_data, 12)
        self.parent_bones = [(i, idx) for i, idx in enumerate(self.parent_bones)]
        # Basic error checking - make sure no bone idx exceeds the known number of bones
        if len(self.parent_bones) != 0:
            max_idx = max([subitem for item in self.parent_bones for subitem in item])
        else:
            max_idx = -1
        assert max_idx == self.num_bones - 1, f'{max_idx}, {self.num_bones - 1}'

    def reinterpret_skel_data(self):
        self.unknown_parent_child_data = self.flatten_list(self.unknown_parent_child_data)
        self.bone_data = self.flatten_list(self.bone_data)
        self.parent_bones = [parent for child, parent in self.parent_bones]
