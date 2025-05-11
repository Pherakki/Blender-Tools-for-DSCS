from ...serialization.DSCSStructs import DSCSSerializable
from ...serialization.DSCSFormatters import HEX32_formatter
from ...serialization.DSCSFormatters import HEX64_formatter
from ...serialization import OffsetMarker


class SkelFileBinary(DSCSSerializable):
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
    
    @property
    def MAGIC(self): return b'20SE'
    
    def __init__(self):
         # Header variables
         self.magic                             = self.MAGIC
         self.filesize                           = None
         self.hashes_section_bytecount           = None
         self.bone_count                         = None
         self.float_channel_count                = None
         self.bone_parent_vector_count           = None
        
         self.bone_transforms_offset             = None
         self.bone_parents_offset                = None
         self.bone_name_hashes_offset            = None
         self.float_channel_array_indices_offset = None
         self.float_channel_name_hashes_offset   = None
         self.float_channel_flags_offset         = None
        
         # Data holders
         self.bone_parent_vectors                = None
         self.bone_transforms                    = None
         self.bone_parents                       = None
         self.float_channel_flags                = None
         self.bone_name_hashes                   = None
         self.float_channel_array_indices        = None
         self.float_channel_object_name_hashes   = None
         
         self.bone_transforms_marker             = OffsetMarker().subscribe(self, "bone_transforms_offset")
         self.bone_parents_marker                = OffsetMarker().subscribe(self, "bone_parents_offset")
         self.float_channel_flags_marker         = OffsetMarker().subscribe(self, "float_channel_flags_offset")
         self.bone_name_hashes_marker            = OffsetMarker().subscribe(self, "bone_name_hashes_offset")
         self.float_channel_array_indices_marker = OffsetMarker().subscribe(self, "float_channel_array_indices_offset")
         self.float_channel_name_hashes_marker   = OffsetMarker().subscribe(self, "float_channel_name_hashes_offset")
         self.filesize_marker                    = OffsetMarker().subscribe(self, "filesize")
         self.hashsize_marker                    = OffsetMarker().subscribe_callback(lambda pos: setattr(self, "hashes_section_bytecount", self.filesize - self.bone_name_hashes_offset))
    
    def exbip_rw(self, rw):
        # 0x00
        self.magic = rw.rw_bytestring(self.magic, 4)
        if self.magic != self.MAGIC:
            raise ValueError("Stream is not a Skel file: expected the magic number '{self.MAGIC}' but received '{self.magic}'")
        self.filesize                           = rw.rw_uint64(self.filesize)
        self.hashes_section_bytecount           = rw.rw_uint32(self.hashes_section_bytecount)

        # 0x10
        self.bone_count                         = rw.rw_uint16(self.bone_count)
        self.float_channel_count                = rw.rw_uint16(self.float_channel_count)
        self.bone_parent_vector_count           = rw.rw_uint32(self.bone_parent_vector_count)
        self.bone_transforms_offset             = rw.rw_shifted_uint32(self.bone_transforms_offset, self.BONE_TRANSFORMS_OFFSET_OFFSET)
        self.bone_parents_offset                = rw.rw_shifted_uint32(self.bone_parents_offset,    self.PARENT_BONES_OFFSET_OFFSET)

        # 0x20
        self.bone_name_hashes_offset            = rw.rw_shifted_uint32(self.bone_name_hashes_offset,            self.BONE_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_array_indices_offset = rw.rw_shifted_uint32(self.float_channel_array_indices_offset, self.FLOAT_CHANNEL_ARRAY_INDICES_OFFSET_OFFSET)
        self.float_channel_name_hashes_offset   = rw.rw_shifted_uint32(self.float_channel_name_hashes_offset,   self.FLOAT_CHANNEL_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_flags_offset         = rw.rw_shifted_uint32(self.float_channel_flags_offset,         self.FLOAT_CHANNEL_FLAGS_OFFSET_OFFSET)

        # 0x30
        rw.rw_padding(0x10)
        
        # # Don't do this for counts
        # if self.filesize != self.bone_name_hashes_offset + self.hashes_section_bytecount:
        #     raise ValueError("Inconsistent file header; hashes section bytecount inconsistent with file size")
        
        self.bone_parent_vectors = rw.rw_int16s(self.bone_parent_vectors, (self.bone_parent_vector_count, 8))
        
        rw.verify_stream_offset(self.bone_transforms_offset, "Bone Transforms", HEX32_formatter, self.bone_transforms_marker)
        self.bone_transforms = rw.rw_dynamic_objs(self.bone_transforms, BoneTransforms, self.bone_count)

        rw.verify_stream_offset(self.bone_parents_offset, "Bone Parents", HEX32_formatter, self.bone_parents_marker)
        self.bone_parents = rw.rw_int16s(self.bone_parents, self.bone_count)

        rw.verify_stream_offset(self.float_channel_flags_offset, "Float Channel Flags", HEX32_formatter, self.float_channel_flags_marker)
        self.float_channel_flags = rw.rw_uint8s(self.float_channel_flags, self.float_channel_count)
        rw.align(rw.tell(), 0x10)

        rw.verify_stream_offset(self.bone_name_hashes_offset, "Bone Name Hashes", HEX32_formatter, self.bone_name_hashes_marker)
        self.bone_name_hashes = rw.rw_uint32s(self.bone_name_hashes, self.bone_count)
        
        rw.verify_stream_offset(self.float_channel_array_indices_offset, "Float Channel Array Indices", HEX32_formatter, self.float_channel_array_indices_marker)
        self.float_channel_array_indices = rw.rw_uint32s(self.float_channel_array_indices, self.float_channel_count)

        rw.verify_stream_offset(self.float_channel_name_hashes_offset, "Float Channel Object Name Hashes", HEX32_formatter, self.float_channel_name_hashes_marker)
        self.float_channel_object_name_hashes = rw.rw_uint32s(self.float_channel_object_name_hashes, self.float_channel_count)
        rw.align(rw.tell(), 0x10)

        rw.verify_stream_offset(self.filesize, "Filesize", HEX64_formatter, self.filesize_marker)
        rw.dispatch_marker(self.hashsize_marker)


class BoneTransforms:
    __slots__ = ("quat", "pos", "scale")

    def __init__(self):
        super().__init__()
        self.quat  = Quaternion()
        self.pos   = None
        self.scale = None

    @classmethod
    def from_transforms(cls, quat, pos, scale):
        instance = cls()
        instance.quat.data = quat
        instance.pos       = pos
        instance.scale     = scale
        return instance

    def __repr__(self):
        return f"[BoneTransforms] {self.quat} {list(self.pos)} {list(self.scale)}"

    def exbip_rw(self, rw):
        self.quat.rw_xyzw(rw)
        self.pos   = rw.rw_float32s(self.pos, 4)
        self.scale = rw.rw_float32s(self.scale, 4)

class Quaternion:
    __slots__ = ("data",)

    def __init__(self):
        super().__init__()
        self.data = (0, 0, 0, 1)

    def __repr__(self):
        return f"[XYZW Quat] {list(self.data)}"

    def rw_xyzw(self, rw):
        self.data = rw.rw_float32s(self.data, 4)

    def wxyz(self):
        return (self.data[3], *self.data[0:3])
    
    def xyzw(self):
        return self.data
    
    @property
    def x(self):
        return self.data[0]
    @x.setter
    def x(self, value):
        self.data[0] = value
        
    @property
    def y(self):
        return self.data[1]
    @y.setter
    def y(self, value):
        self.data[1] = value
        
    @property
    def z(self):
        return self.data[2]
    @z.setter
    def z(self, value):
        self.data[2] = value
        
    @property
    def w(self):
        return self.data[3]
    @w.setter
    def w(self, value):
        self.data[3] = value
        
