import array

from ...serialization.Serializable import Serializable


class SkelBinary(Serializable):
    """
    A class to read and write skel files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. Pairs of bone indices that create parent-bone relationships, 8 int16s per index -> 128 bitwidth.
        3. A section of bone transforms (quat, pos, scale).
        4. A list of bone-parent relationships (same data as 2, but more easily readable).
        5. A section of flaot channel flags.
        6. A section of (hashed) bone names; one per bone.
        7. A section of 1 uint32 per float channel, identifying the array index the float channel puts data into.
           These arrays are deep inside the game logic somewhere and each object type stores different data in these
           arrays. Materials store shader uniforms, cameras and lights both have various object properties (FOV,
           clip distance, light colour...)
        8. A section of (hashed) material/camera/light names the float channel data are associated with.

    Completion status
    ------
    (o) SkelBinary can successfully parse all name files in DSDB archive within current constraints.
    (o) SkelBinary can yet fully interpret all data in name files in DSDB archive.
    (o) SkelBinary can write data to skel files.
    """

    @property
    def BONE_TRANSFORMS_OFFSET_OFFSET            (self): return 0x18
    @property
    def PARENT_BONES_OFFSET_OFFSET               (self): return 0x1C
    @property
    def BONE_NAME_HASHES_OFFSET_OFFSET           (self): return 0x20
    @property
    def FLOAT_CHANNEL_ARRAY_INDICES_OFFSET_OFFSET(self): return 0x24
    @property
    def FLOAT_CHANNEL_NAME_HASHES_OFFSET_OFFSET  (self): return 0x28
    @property
    def FLOAT_CHANNEL_FLAGS_OFFSET_OFFSET        (self): return 0x2C

    def __init__(self):
        super().__init__()

        # Header variables
        self.filetype                   = b'20SE'
        self.filesize                   = None
        self.hashes_section_bytecount   = None
        self.bone_count                 = None
        self.float_channel_count        = None
        self.parent_bone_dataline_count = None

        self.bone_transforms_offset             = None
        self.parent_bones_offset                = None
        self.bone_name_hashes_offset            = None
        self.float_channel_array_indices_offset = None
        self.float_channel_name_hashes_offset   = None
        self.float_channel_flags_offset         = None

        # Data holders
        self.parent_bone_datalines            = None
        self.bone_transforms                  = None
        self.parent_bones                     = None
        self.float_channel_flags              = None
        self.bone_name_hashes                 = None
        self.float_channel_array_indices      = None
        self.float_channel_object_name_hashes = None

    def read_write(self, rw):
        self.rw_header(rw)
        self.rw_parent_bone_datalines(rw)
        self.rw_bone_transforms(rw)
        self.rw_parent_bones(rw)
        self.rw_float_channel_flags(rw)
        self.rw_bone_name_hashes(rw)
        self.rw_float_channel_array_indices(rw)
        self.rw_float_channel_object_names(rw)
        rw.assert_at_eof()

    def rw_header(self, rw):
        # 0x00
        self.filetype = rw.rw_bytestring(self.filetype, 4)
        if self.filetype != b"20SE":
            raise ValueError("Attempted to read a file that is not a valid skel file")
        self.filesize                   = rw.rw_uint64(self.filesize)
        self.hashes_section_bytecount   = rw.rw_uint32(self.hashes_section_bytecount)

        # 0x10
        self.bone_count                 = rw.rw_uint16(self.bone_count)
        self.float_channel_count        = rw.rw_uint16(self.float_channel_count)
        self.parent_bone_dataline_count = rw.rw_uint32(self.parent_bone_dataline_count)
        self.bone_transforms_offset     = rw.rw_offset_uint32(self.bone_transforms_offset, self.BONE_TRANSFORMS_OFFSET_OFFSET)
        self.parent_bones_offset        = rw.rw_offset_uint32(self.parent_bones_offset, self.PARENT_BONES_OFFSET_OFFSET)

        # 0x20
        self.bone_name_hashes_offset            = rw.rw_offset_uint32(self.bone_name_hashes_offset, self.BONE_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_array_indices_offset = rw.rw_offset_uint32(self.float_channel_array_indices_offset, self.FLOAT_CHANNEL_ARRAY_INDICES_OFFSET_OFFSET)
        self.float_channel_name_hashes_offset   = rw.rw_offset_uint32(self.float_channel_name_hashes_offset, self.FLOAT_CHANNEL_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_flags_offset         = rw.rw_offset_uint32(self.float_channel_flags_offset, self.FLOAT_CHANNEL_FLAGS_OFFSET_OFFSET)

        # 0x30
        rw.align(0x30, 0x40)

        if self.filesize != self.bone_name_hashes_offset + self.hashes_section_bytecount:
            raise ValueError("Inconsistent file header; hashes section bytecount inconsistent with file size")

    def rw_parent_bone_datalines(self, rw):
        self.parent_bone_datalines = rw.rw_int16s(self.parent_bone_datalines, (self.parent_bone_dataline_count, 8))

    def rw_bone_transforms(self, rw):
        rw.assert_file_pointer_now_at("Bone Transforms", self.bone_transforms_offset)
        self.bone_transforms = rw.rw_obj_array(self.bone_transforms, BoneTransforms, self.bone_count)

    def rw_parent_bones(self, rw):
        rw.assert_file_pointer_now_at("Bone Parents", self.parent_bones_offset)
        self.parent_bones = rw.rw_int16s(self.parent_bones, self.bone_count)

    def rw_float_channel_flags(self, rw):
        rw.assert_file_pointer_now_at("Float Channel Flags", self.float_channel_flags_offset)
        self.float_channel_flags = rw.rw_uint8s(self.float_channel_flags, self.float_channel_count)
        rw.align(rw.tell(), 0x10)

    def rw_bone_name_hashes(self, rw):
        rw.assert_file_pointer_now_at("Bone Name Hashes", self.bone_name_hashes_offset)
        self.bone_name_hashes = rw.rw_uint32s(self.bone_name_hashes, self.bone_count)

    def rw_float_channel_array_indices(self, rw):
        rw.assert_file_pointer_now_at("Float Channel Array Indices", self.float_channel_array_indices_offset)

        self.float_channel_array_indices = rw.rw_uint32s(self.float_channel_array_indices, self.float_channel_count)

    def rw_float_channel_object_names(self, rw):
        rw.assert_file_pointer_now_at("Float Channel Object Names", self.float_channel_name_hashes_offset)
        self.float_channel_object_name_hashes = rw.rw_uint32s(self.float_channel_object_name_hashes, self.float_channel_count)
        rw.align(rw.tell(), 0x10)


class QuaternionBinary(Serializable):
    __slots__ = ("data",)

    def __init__(self):
        super().__init__()
        self.data = []

    def __repr__(self):
        return f"[XYZW Quat] {list(self.data)}"

    def rw_XYZW(self, rw):
        self.data = rw.rw_float32s(self.data, 4)

    def rw_WXYZ(self, rw):
        if rw.mode() == "read":
            self.data = rw.rw_float32s(None, 4)
            self.data = array.array('f', [*self.data[1:4], self.data[0]])
        else:
            data = [self.data[3], *self.data[0:3]]
            rw.rw_float32s(data, 4)


class BoneTransforms(Serializable):
    __slots__ = ("quat", "pos", "scale")

    def __init__(self):
        super().__init__()
        self.quat  = QuaternionBinary()
        self.pos   = None
        self.scale = None

    def __repr__(self):
        return f"[BoneTransforms] {self.quat} {list(self.pos)} {list(self.scale)}"

    def read_write(self, rw):
        rw.rw_obj_method(self.quat, self.quat.rw_XYZW)
        self.pos   = rw.rw_float32s(self.pos, 4)
        self.scale = rw.rw_float32s(self.scale, 4)
