import struct
from ....serialization.DSCSStructs import DSCSSerializable
from ....serialization.DSCSFormatters import HEX32_formatter
from ....serialization.DSCSFormatters import HEX64_formatter
from ....serialization import OffsetMarker


def bytes_to_alignment(pos, alignment):
    return (alignment - (pos % alignment)) % alignment

def roundup(pos, alignment):
    return pos + bytes_to_alignment(pos, alignment)

class AttributeTypes:
    POSITION = 1
    NORMAL   = 2
    TANGENT  = 3
    BINORMAL = 4
    UV1      = 5
    UV2      = 6
    UV3      = 7
    COLOR    = 9
    INDEX    = 10
    WEIGHT   = 11

class PrimitiveTypes:
    POINTS         = 0
    LINES          = 1
    LINE_LOOP      = 2
    LINE_STRIP     = 3
    TRIANGLES      = 4
    TRIANGLE_STRIP = 5
    TRIANGLE_FAN   = 6

TYPESIZE = {'f': 4, 'e': 2, 'B': 1}

class Vertex:
    __slots__ = ("buffer",)
    ATTRIBUTES = AttributeTypes

    def __init__(self):
        self.buffer = [None]*12

    def __repr__(self):
        return f"[Geom::Mesh::Vertex] {self.position} {self.normal} {self.tangent} {self.binormal} {self.UV1} {self.UV2} {self.UV3} {self.color} {self.indices} {self.weights}"

    def __getitem__(self, idx):
        return self.buffer[idx]

    @property
    def position(self): return self.buffer[AttributeTypes.POSITION]
    @position.setter
    def position(self, value): self.buffer[AttributeTypes.POSITION] = value

    @property
    def normal(self): return self.buffer[AttributeTypes.NORMAL]
    @normal.setter
    def normal(self, value): self.buffer[AttributeTypes.NORMAL] = value

    @property
    def tangent(self): return self.buffer[AttributeTypes.TANGENT]
    @tangent.setter
    def tangent(self, value): self.buffer[AttributeTypes.TANGENT] = value

    @property
    def binormal(self): return self.buffer[AttributeTypes.BINORMAL]
    @binormal.setter
    def binormal(self, value): self.buffer[AttributeTypes.BINORMAL] = value

    @property
    def UV1(self): return self.buffer[AttributeTypes.UV1]
    @UV1.setter
    def UV1(self, value): self.buffer[AttributeTypes.UV1] = value

    @property
    def UV2(self): return self.buffer[AttributeTypes.UV2]
    @UV2.setter
    def UV2(self, value): self.buffer[AttributeTypes.UV2] = value

    @property
    def UV3(self): return self.buffer[AttributeTypes.UV3]
    @UV3.setter
    def UV3(self, value): self.buffer[AttributeTypes.UV3] = value

    @property
    def color(self): return self.buffer[AttributeTypes.COLOR]
    @color.setter
    def color(self, value): self.buffer[AttributeTypes.COLOR] = value

    @property
    def indices(self): return self.buffer[AttributeTypes.INDEX]
    @indices.setter
    def indices(self, value): self.buffer[AttributeTypes.INDEX] = value

    @property
    def weights(self): return self.buffer[AttributeTypes.WEIGHT]
    @weights.setter
    def weights(self, value): self.buffer[AttributeTypes.WEIGHT] = value


class VertexAttributeBinary:
    def __init__(self):
        self.atype    = 0
        self.count    = 0
        self.dtype    = 0
        self.offset   = 0
    
    @classmethod
    def create(cls, atype, count, dtype, offset):
        instance = cls()
        instance.atype  = atype
        instance.count  = count
        instance.dtype  = dtype
        instance.offset = offset
        return instance
    
    def exbip_rw(self, rw):
        self.atype    = rw.rw_uint16(self.atype)
        self.count    = rw.rw_uint16(self.count)
        self.dtype    = rw.rw_uint16(self.dtype)
        self.offset   = rw.rw_uint16(self.offset)
    
    def __repr__(self):
        return f"VertexAttribute({self.atype}, {self.count}, {self.dtype}, {self.offset})"

class UnknownMeshData:
    def __init__(self):
        self.unknown_0x00 = 0
        self.vertex_count = 0
        self.unknown_0x04 = 8
        self.unknown_0x06 = 1
        
        self.unknown_0x10 = 1
        self.unknown_0x12 = 65
        self.unknown_0x14 = 0
        
        self.payload = []
    
    def exbip_rw(self, rw):
        self.unknown_0x00 = rw.rw_uint16(self.unknown_0x00)
        self.vertex_count = rw.rw_uint16(self.vertex_count)
        self.unknown_0x04 = rw.rw_uint16(self.unknown_0x04)
        self.unknown_0x06 = rw.rw_uint16(self.unknown_0x06)
        
        rw.rw_padding(0x08)
        
        self.unknown_0x10 = rw.rw_uint16(self.unknown_0x10)
        self.unknown_0x12 = rw.rw_uint16(self.unknown_0x12)
        self.unknown_0x14 = rw.rw_uint32(self.unknown_0x14)
        
        self.payload = rw.rw_uint64s(self.payload, self.vertex_count)
        
        rw.assert_equal(self.unknown_0x00, 0)
        rw.assert_equal(self.unknown_0x04, 8)
        rw.assert_equal(self.unknown_0x06, 1)
        rw.assert_equal(self.unknown_0x10, 1)
        rw.assert_equal(self.unknown_0x12, 65)
        rw.assert_equal(self.unknown_0x14, 0)
        
        

class MeshBinaryHundredLine:
    DATA_TYPES = {
        0: 'B',
        8: 'e',
        9: 'f'
    }
    
    INVERSE_DATA_TYPES = {v: k for k,v in DATA_TYPES.items()}

    PRIMITIVE_TYPES = {
        0x0000: PrimitiveTypes.TRIANGLE_STRIP,
        0x0001: PrimitiveTypes.TRIANGLES
    }
    
    INVERSE_PRIMITIVE_TYPES = {v: k for k,v in PRIMITIVE_TYPES.items()}

    def __init__(self):
        self.vertices_offset          = 0
        self.indices_offset           = 0
        self.matrix_palette_offset    = 0
        self.unknown_0x18             = 0
        
        self.attributes_offset        = 0
        self.matrix_palette_count     = 0
        self.attribute_count          = 0
        self.bytes_per_vertex         = 0
        self.index_type               = 0 # 0=uint16, 1=uint32?
        
        self.vertex_groups_per_vertex = 0
        self.flags                    = 0 
        self.primitive_type           = 0
        self.name_hash                = 0
        self.name_offset              = 0
        self.unknown_0x3C             = 0

        self.material_idx = 0
        self.vertex_count = 0
        self.index_count  = 0
        self.unknown_0x4C = 0
        
        self.unknown_0x50 = 0
        self.bounding_sphere_radius = 0
        self.centre_point           = 0
        self.bounding_box_diagonal  = 0
        
        self.unknown_mesh_data_offset = 0
        
        self.vertex_buffer = []
        self.index_buffer  = []
        self.matrix_palette = []
        self.attributes = []
        self.unknown_mesh_data = None
        
        self.vertices_marker       = OffsetMarker().subscribe(self, "vertices_offset")
        self.indices_marker        = OffsetMarker().subscribe(self, "indices_offset")
        self.matrix_palette_marker = OffsetMarker().subscribe(self, "matrix_palette_offset")
        self.attributes_marker     = OffsetMarker().subscribe(self, "attributes_offset")
        self.unknown_data_marker   = OffsetMarker().subscribe(self, "unknown_mesh_data_offset")
    
    def exbip_rw(self, rw):
        self.vertices_offset = rw.rw_uint64(self.vertices_offset)
        self.indices_offset  = rw.rw_uint64(self.indices_offset)
        self.matrix_palette_offset = rw.rw_uint64(self.matrix_palette_offset) # mpalette offset
        self.unknown_0x18 = rw.rw_uint64(self.unknown_0x18)
        
        self.attributes_offset    = rw.rw_uint64(self.attributes_offset)
        self.matrix_palette_count = rw.rw_uint16(self.matrix_palette_count)
        self.attribute_count      = rw.rw_uint16(self.attribute_count)
        self.bytes_per_vertex     = rw.rw_uint16(self.bytes_per_vertex)
        self.index_type           = rw.rw_uint16(self.index_type)
        
        self.vertex_groups_per_vertex = rw.rw_uint8(self.vertex_groups_per_vertex)
        self.flags          = rw.rw_uint8(self.flags)
        self.primitive_type = rw.rw_uint16(self.primitive_type)
        self.name_hash      = rw.rw_uint32(self.name_hash)
        self.name_offset    = rw.rw_uint64(self.name_offset)
        
        self.material_idx = rw.rw_uint32(self.material_idx)
        self.vertex_count = rw.rw_uint32(self.vertex_count)
        self.index_count  = rw.rw_uint32(self.index_count)
        self.unknown_0x4C = rw.rw_uint32(self.unknown_0x4C)
        
        self.unknown_0x50 = rw.rw_uint32(self.unknown_0x50)
        self.bounding_sphere_radius = rw.rw_float32(self.bounding_sphere_radius)
        self.centre_point           = rw.rw_float32s(self.centre_point, 3)
        self.bounding_box_diagonal  = rw.rw_float32s(self.bounding_box_diagonal, 3)
        
        self.unknown_mesh_data_offset = rw.rw_uint64(self.unknown_mesh_data_offset)
        
        rw.rw_padding(0x08)
        
        rw.assert_equal(self.unknown_0x3C, 0)
        rw.assert_equal(self.unknown_0x4C, 0)
        rw.assert_equal(self.unknown_0x50, 0)
    
    def rw_data(self, rw):
        self.unknown_data_marker   = OffsetMarker().subscribe(self, "unknown_mesh_data_offset")
        
        rw.verify_stream_offset(rw.tell(), self.vertices_offset, HEX32_formatter, self.vertices_marker)
        self.vertex_buffer = rw.rw_bytestring(self.vertex_buffer, self.vertex_count*self.bytes_per_vertex)
        
        rw.verify_stream_offset(rw.tell(), self.matrix_palette_offset, HEX32_formatter, self.matrix_palette_marker)
        self.matrix_palette = rw.rw_uint32s(self.matrix_palette, self.matrix_palette_count)
        
        rw.verify_stream_offset(rw.tell(), self.indices_offset, HEX32_formatter, self.indices_marker)
        self.index_buffer = rw.rw_uint16s(self.index_buffer, self.index_count)
        rw.align(rw.tell(), 0x04)
        
        rw.verify_stream_offset(rw.tell(), self.attributes_offset, HEX32_formatter, self.attributes_marker)
        self.attributes = rw.rw_dynamic_objs(self.attributes, VertexAttributeBinary, self.attribute_count)

        if rw.section_exists(self.unknown_mesh_data_offset, self.unknown_mesh_data is not None):
            rw.verify_stream_offset(rw.tell(), self.unknown_mesh_data_offset, HEX32_formatter, self.unknown_data_marker)
            self.unknown_mesh_data = rw.rw_dynamic_obj(self.unknown_mesh_data, UnknownMeshData)
    
    def unpack_vertices(self):
        vertices = [Vertex() for _ in range(self.vertex_count)]
        VBO    = self.vertex_buffer
        vcount = self.vertex_count
        stride = self.bytes_per_vertex
        
        for va in self.attributes:
            offset  = va.offset
            va_idx  = va.atype
            dtype = self.DATA_TYPES[va.dtype]*va.count
            dsize = struct.calcsize(dtype)
            
            unpack_fn  = struct.Struct(dtype).unpack
        
            # Unpack specified attribute
            for i in range(vcount):
                start = offset+i*stride
                vertices[i].buffer[va_idx] = unpack_fn(VBO[start:start+dsize])
        
        return vertices
    
    def pack_vertices(self, vertices):
        last_va = self.attributes[-1]
        bytes_per_vertex = last_va.offset + last_va.count * TYPESIZE[self.DATA_TYPES[last_va.dtype]]
        bytes_per_vertex = roundup(bytes_per_vertex, 4)
        
        
        # Define the structure for repacking
        structure_def = ""
        element_count = 0
        repack_indices = []
        for va in self.attributes:
            typecode = self.DATA_TYPES[va.dtype]
            dsize    = TYPESIZE[typecode]
            count    = va.count
            
            repack_indices.append((va.atype, element_count, count))
            count = ((((dsize*count) + 3) // 4) * 4) // dsize
            structure_def += typecode * count
            element_count += count
        
        repacker = struct.Struct(structure_def)
        repack   = repacker.pack_into
        
        # Now repack
        VBO = bytearray(bytes_per_vertex * len(vertices))
        
        template = [0 for _ in range(element_count)]
        buffer_offset = 0
        for vertex in vertices:
            buffer = vertex.buffer
            for atype, template_offset, count in repack_indices:
                template[template_offset:template_offset+count] = buffer[atype]
            repack(VBO, buffer_offset, *template)
            buffer_offset += bytes_per_vertex
        
        self.bytes_per_vertex = bytes_per_vertex
        self.vertex_buffer = VBO
    
    @classmethod
    def get_default_vertex_attributes(cls, vertex):
        INVERSE_DATA_TYPES = cls.INVERSE_DATA_TYPES
        
        def add_va(vas, vertex, offset, attr_type, dtype, dsize):
            attr = vertex.buffer[attr_type]
            if attr is not None:
                count = len(attr)
                va = VertexAttributeBinary.create(attr_type, count, INVERSE_DATA_TYPES[dtype], offset)
                vas[attr_type] = va
                return dsize*count
            else:
                return 0
            
        vas = {}
        offset = 0
        offset += add_va(vas, vertex, offset, AttributeTypes.POSITION, 'f', 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.NORMAL,   'e', 2); offset = roundup(offset, 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.TANGENT,  'e', 2); offset = roundup(offset, 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.BINORMAL, 'e', 2); offset = roundup(offset, 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV1,      'f', 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV2,      'f', 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV3,      'f', 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.COLOR,    'B', 1); offset = roundup(offset, 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.INDEX,    'B', 1); offset = roundup(offset, 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.WEIGHT,   'e', 2); offset = roundup(offset, 4)
        return vas


class NameOffsets:
    def __init__(self):
        self.bone_name_count    = 0
        self.material_name_count = 0
        self.bone_name_offsets_offset = 0
        self.material_name_offsets_offset = 0
        
        self.bone_name_offsets = []
        self.material_name_offsets = []
    
    def exbip_rw(self, rw):
        self.bone_name_count              = rw.rw_uint32(self.bone_name_count)
        self.material_name_count          = rw.rw_uint32(self.material_name_count)
        self.bone_name_offsets_offset     = rw.rw_uint64(self.bone_name_offsets_offset)
        self.material_name_offsets_offset = rw.rw_uint64(self.material_name_offsets_offset)
        
        rw.verify_stream_offset(rw.tell(), self.bone_name_offsets_offset)
        self.bone_name_offsets    = rw.rw_uint64s(self.bone_name_offsets, self.bone_name_count)
        rw.verify_stream_offset(rw.tell(), self.material_name_offsets_offset)
        self.material_name_offsets = rw.rw_uint64s(self.material_name_offsets, self.material_name_count)

    def __repr__(self):
        return f"NameOffsets({self.bone_name_count}/{self.bone_name_offsets_offset}, {self.material_name_count}/{self.material_name_offsets_offset})"

class ShaderUniformHundredLine:
    def __init__(self):
        self.payload     = b'\x00'*0x10
        self.index       = 0
        self.float_count = 0
        self.unknown_0x14 = 0xFFFFFFFF
        self.unknown_0x18 = 0xFFFFFFFF
        self.unknown_0x1C = 0xFFFFFF00
    
    def exbip_rw(self, rw):
        self.payload      = rw.rw_bytestring(self.payload, 0x10)
        self.index        = rw.rw_uint16(self.index)
        self.float_count  = rw.rw_uint16(self.float_count)
        self.unknown_0x14 = rw.rw_uint32(self.unknown_0x14)
        self.unknown_0x18 = rw.rw_uint32(self.unknown_0x18)
        self.unknown_0x1C = rw.rw_uint32(self.unknown_0x1C)
    
    def unpack(self):
        if self.float_count == 0:
            return struct.unpack("QII", self.payload)  # Texture Offset is first of these
        else:
            return struct.unpack("f"*self.float_count, self.payload[:4*self.float_count])
    
    def __repr__(self):
        payload = self.unpack()
        return f"ShaderUniform({self.index}, {self.float_count}, {self.unknown_0x14}, {self.unknown_0x18}, {self.unknown_0x1C}, {payload})"

class ShaderSettingHundredLine:
    def __init__(self):
        self.payload     = b'\x00'*0x10
        self.index       = 0
        self.unknown_0x12 = 0
        self.unknown_0x14 = 0xFFFFFFFF
        self.unknown_0x18 = 0xFFFFFFFF
        self.unknown_0x1C = 0xFFFFFF00
    
    def exbip_rw(self, rw):
        self.payload      = rw.rw_bytestring(self.payload, 0x10)
        self.index        = rw.rw_uint16(self.index)
        self.unknown_0x12 = rw.rw_uint16(self.unknown_0x12)
        self.unknown_0x14 = rw.rw_uint32(self.unknown_0x14)
        self.unknown_0x18 = rw.rw_uint32(self.unknown_0x18)
        self.unknown_0x1C = rw.rw_uint32(self.unknown_0x1C)


class MaterialBinaryHundredLine:
    def __init__(self):
        self.name_hash = 0
        self.line_0 = b"\x00"*56
        self.line_1 = b"\x00"*56
        self.line_2 = b"\x00"*56
        self.line_3 = b"\x00"*56
        self.line_4 = b"\x00"*56
        self.line_5 = b"\x00"*56
        self.line_6 = b"\x00"*56
        self.line_7 = b"\x00"*56
        self.line_8 = b"\x00"*56
        self.line_9 = b"\x00"*56
        self.line_10 = b"\x00"*56
        self.line_11 = b"\x00"*56
        self.line_12 = b"\x00"*56
        self.line_13 = b"\x00"*56
        
        self.unknown_0x314 = 0
        self.unknown_0x318 = 0
        self.unknown_0x31C = 0
        
        self.uniform_count = 0
        self.setting_count = 0
        self.unknown_0x324 = 0x5A1
        self.unknown_0x326 = 0x500
        
        self.uniforms = []
        self.settings = []
    
    def exbip_rw(self, rw):
        self.name_hash = rw.rw_uint32(self.name_hash)
        self.line_0  = rw.rw_bytestring(self.line_0, 56)
        self.line_1  = rw.rw_bytestring(self.line_1, 56)
        self.line_2  = rw.rw_bytestring(self.line_2, 56)
        self.line_3  = rw.rw_bytestring(self.line_3, 56)
        self.line_4  = rw.rw_bytestring(self.line_4, 56)
        self.line_5  = rw.rw_bytestring(self.line_5, 56)
        self.line_6  = rw.rw_bytestring(self.line_6, 56)
        self.line_7  = rw.rw_bytestring(self.line_7, 56)
        self.line_8  = rw.rw_bytestring(self.line_8, 56)
        self.line_9  = rw.rw_bytestring(self.line_9, 56)
        self.line_10 = rw.rw_bytestring(self.line_10, 56)
        self.line_11 = rw.rw_bytestring(self.line_11, 56)
        self.line_12 = rw.rw_bytestring(self.line_12, 56)
        self.line_13 = rw.rw_bytestring(self.line_13, 56)
        
        self.unknown_0x314 = rw.rw_uint32(self.unknown_0x314)
        self.unknown_0x318 = rw.rw_uint32(self.unknown_0x318)
        self.unknown_0x31C = rw.rw_uint32(self.unknown_0x31C)
        
        self.uniform_count = rw.rw_uint8(self.uniform_count)
        self.setting_count = rw.rw_uint8(self.setting_count)
        rw.align(rw.tell(), 0x04)
        self.unknown_0x324 = rw.rw_uint16(self.unknown_0x324)
        self.unknown_0x326 = rw.rw_uint16(self.unknown_0x326)
        
        self.uniforms = rw.rw_dynamic_objs(self.uniforms, ShaderUniformHundredLine, self.uniform_count)
        self.settings = rw.rw_dynamic_objs(self.settings, ShaderSettingHundredLine, self.setting_count)

class CameraBinaryHundredLine:
    def __init__(self):
        super().__init__()

        self.bone_name_hash = None
        self.fov            = None
        self.aspect_ratio   = None
        self.zNear          = None

        self.zFar               = None
        # self.orthographic_scale = None
        
        self.unknown_0x14 = 0
        self.unknown_0x18 = 0
        self.unknown_0x1C = 0
        self.projection         = None

    def exbip_rw(self, rw):
        self.bone_name_hash     = rw.rw_uint32(self.bone_name_hash)
        self.fov                = rw.rw_float32(self.fov)
        self.aspect_ratio       = rw.rw_float32(self.aspect_ratio)
        self.zNear              = rw.rw_float32(self.zNear)
        self.zFar               = rw.rw_float32(self.zFar)
        # self.orthographic_scale = rw.rw_float32(self.orthographic_scale)
        self.unknown_0x14 = rw.rw_float32(self.unknown_0x14)
        self.unknown_0x18 = rw.rw_float32(self.unknown_0x18)
        self.unknown_0x1C = rw.rw_float32(self.unknown_0x1C)
        self.projection         = rw.rw_uint32(self.projection)  # 0 = Perspective, 1 = Ortho
        rw.align(0x24, 0x38)


class StringChunkSizeDescriptor:
    def deserialize(rw, binary):
        return binary.skel_offset - binary.strings_offset
    
    def serialize(rw, binary):
        return len(binary.string_chunk)
    
    def count(rw, binary):
        return len(binary.string_chunk)


class SkelFileBinaryHundredLine(DSCSSerializable):
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
    
    MAGIC = b'60SE'
    
    def __init__(self):
        self.magic = b'60SE'
        self.filesize = 0
        self.hashes_section_bytecount = 0
        self.bone_count = 0
        self.float_channel_count = 0
        self.bone_parent_vector_size = 2
        self.bone_transforms_offset = 0
        self.bone_parents_offset = 0
        self.bone_name_hashes_offset = 0
        self.float_channel_array_indices_offset = 0
        self.float_channel_name_hashes_offset   = 0
        self.float_channel_flags_offset         = 0
        
        self.bone_parent_pairs_count = 0
        
        # Data holders
        self.bone_parent_vectors                = []
        self.bone_transforms                    = []
        self.bone_parents                       = []
        self.float_channel_flags                = []
        self.bone_name_hashes                   = []
        self.float_channel_array_indices        = []
        self.float_channel_object_name_hashes   = []
       
        self.bone_transforms_marker             = OffsetMarker().subscribe(self, "bone_transforms_offset")
        self.bone_parents_marker                = OffsetMarker().subscribe(self, "bone_parents_offset")
        self.float_channel_flags_marker         = OffsetMarker().subscribe(self, "float_channel_flags_offset")
        self.bone_name_hashes_marker            = OffsetMarker().subscribe(self, "bone_name_hashes_offset")
        self.float_channel_array_indices_marker = OffsetMarker().subscribe(self, "float_channel_array_indices_offset")
        self.float_channel_name_hashes_marker   = OffsetMarker().subscribe(self, "float_channel_name_hashes_offset")
        self.filesize_marker                    = OffsetMarker().subscribe(self, "filesize")
        self.hashsize_marker                    = OffsetMarker().subscribe_callback(lambda pos: setattr(self, "hashes_section_bytecount", self.filesize - self.bone_name_hashes_offset))
    
    
    def exbip_rw(self, rw):
        self.magic = rw.rw_bytestring(self.magic, 4)
        if self.magic != self.MAGIC:
            raise ValueError(f"Stream is not a Skel file: expected the magic number '{self.MAGIC}' but received '{self.magic}'")
        self.filesize                           = rw.rw_uint64(self.filesize)
        self.hashes_section_bytecount           = rw.rw_uint32(self.hashes_section_bytecount)

        # 0x10
        self.bone_count                         = rw.rw_uint16(self.bone_count)
        self.float_channel_count                = rw.rw_uint16(self.float_channel_count)
        self.bone_parent_vector_size            = rw.rw_uint32(self.bone_parent_vector_size)
        self.bone_transforms_offset             = rw.rw_shifted_uint32(self.bone_transforms_offset, self.BONE_TRANSFORMS_OFFSET_OFFSET)
        self.bone_parents_offset                = rw.rw_shifted_uint32(self.bone_parents_offset,    self.PARENT_BONES_OFFSET_OFFSET)

        # 0x20
        self.bone_name_hashes_offset            = rw.rw_shifted_uint32(self.bone_name_hashes_offset,            self.BONE_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_array_indices_offset = rw.rw_shifted_uint32(self.float_channel_array_indices_offset, self.FLOAT_CHANNEL_ARRAY_INDICES_OFFSET_OFFSET)
        self.float_channel_name_hashes_offset   = rw.rw_shifted_uint32(self.float_channel_name_hashes_offset,   self.FLOAT_CHANNEL_NAME_HASHES_OFFSET_OFFSET)
        self.float_channel_flags_offset         = rw.rw_shifted_uint32(self.float_channel_flags_offset,         self.FLOAT_CHANNEL_FLAGS_OFFSET_OFFSET)

        rw.assert_equal(self.bone_parent_vector_size, 2)

        # # 0x30
        rw.rw_padding(0x0C)
        self.bone_parent_pairs_count = rw.rw_uint32(self.bone_parent_pairs_count)
    
        self.bone_parent_vectors = rw.rw_uint16s(self.bone_parent_vectors, (self.bone_parent_pairs_count,self.bone_parent_vector_size))
        rw.align(rw.tell(), 0x10)
    
        rw.verify_stream_offset(self.bone_transforms_offset, "Bone Transforms", HEX32_formatter, self.bone_transforms_marker)
        self.bone_transforms = rw.rw_dynamic_objs(self.bone_transforms, BoneTransforms, self.bone_count)

        rw.verify_stream_offset(self.bone_parents_offset, "Bone Parents", HEX32_formatter, self.bone_parents_marker)
        self.bone_parents = rw.rw_int16s(self.bone_parents, self.bone_count)
        rw.align(rw.tell(), 0x04)

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
        self.data = [0, 0, 0, 1]

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
        
   
        
class GeomFileBinaryHundredLine(DSCSSerializable):
    def __init__(self):
        self.version        = 0
        self.mesh_count     = 0
        self.material_count = 0
        self.light_count    = 0
        self.camera_count   = 0
        self.ibpm_count     = 0
        
        self.unknown_0x10          = 0
        self.centre_point          = [0,0,0]
        self.bounding_box_diagonal = [0,0,0]
        self.padding_0x3C          = 0

        self.unknown_0x40        = 0
        self.unknown_0x44        = 0
        self.skel_size           = 0
        self.meshes_offset       = 0
        self.materials_offset    = 0
        self.lights_offset       = 0
        self.cameras_offset      = 0
        self.ibpms_offset        = 0
        self.padding_0x78        = 0
        self.strings_offset      = 0
        self.extra_clut_offset   = 0
        self.padding_0x90        = 0
        self.name_offsets_offset = 0
        self.skel_offset         = 0
        self.padding_0xA8        = 0
        
        self.name_offsets = NameOffsets()
        self.meshes          = []
        self.materials       = []
        self.cameras         = []
        self.ibpms           = []
        self.extra_clut      = b''
        self.string_chunk    = b''
        self.skel = SkelFileBinaryHundredLine()
        
        self.skel_size_marker    = OffsetMarker().subscribe_callback(lambda rw: setattr(self, "skel_size", rw.tell() - self.skel_offset))
        self.meshes_marker       = OffsetMarker().subscribe(self, "meshes_offset")
        self.materials_marker    = OffsetMarker().subscribe(self, "materials_offset")
        self.lights_marker       = OffsetMarker().subscribe(self, "lights_offset")
        self.cameras_marker      = OffsetMarker().subscribe(self, "cameras_offset")
        self.ibpms_marker        = OffsetMarker().subscribe(self, "ibpms_offset")
        self.strings_marker      = OffsetMarker().subscribe(self, "strings_offset")
        self.extra_clut_marker   = OffsetMarker().subscribe(self, "extra_clut_offset")
        self.name_offsets_marker = OffsetMarker().subscribe(self, "name_offsets_offset")
        self.skel_marker         = OffsetMarker().subscribe(self, "skel_offset")
        
        
    
    def get_string(self, offset):
        size = 0
        c = self.string_chunk[offset]
        while c != 0:
            size += 1
            c = self.string_chunk[offset+size]
        
        return self.string_chunk[offset:offset+size]
            
        
    def exbip_rw(self, rw):
        self.version               = rw.rw_uint32(self.version)
        self.mesh_count            = rw.rw_uint16(self.mesh_count)
        self.material_count        = rw.rw_uint16(self.material_count)
        self.light_count           = rw.rw_uint16(self.light_count)
        self.camera_count          = rw.rw_uint16(self.camera_count)
        self.ibpm_count            = rw.rw_uint16(self.ibpm_count)
        rw.align(rw.tell(), 0x10)
        
        self.unknown_0x10            = rw.rw_uint32(self.unknown_0x10)
        self.centre_point            = rw.rw_float32s(self.centre_point, 3)
        self.bounding_box_diagonal   = rw.rw_float32s(self.bounding_box_diagonal, 3)
        self.padding_0x3C            = rw.rw_uint32(self.padding_0x3C)
        
        self.unknown_0x40            = rw.rw_uint32(self.unknown_0x40)
        self.unknown_0x44            = rw.rw_uint32(self.unknown_0x44)
        self.skel_size               = rw.rw_uint64(self.skel_size)
        self.meshes_offset           = rw.rw_uint64(self.meshes_offset)
        self.materials_offset        = rw.rw_uint64(self.materials_offset)
        self.lights_offset           = rw.rw_uint64(self.lights_offset)
        self.cameras_offset          = rw.rw_uint64(self.cameras_offset)
        self.ibpms_offset            = rw.rw_uint64(self.ibpms_offset)
        self.padding_0x78            = rw.rw_uint64(self.padding_0x78)
        self.strings_offset          = rw.rw_uint64(self.strings_offset)
        self.extra_clut_offset       = rw.rw_uint64(self.extra_clut_offset)
        self.padding_0x90            = rw.rw_uint64(self.padding_0x90)
        self.name_offsets_offset     = rw.rw_uint64(self.name_offsets_offset)
        self.skel_offset             = rw.rw_uint64(self.skel_offset)
        self.padding_0xA8            = rw.rw_uint64(self.padding_0xA8)
        
        rw.assert_equal(self.unknown_0x10, 0)
        # rw.assert_equal(self.padding_0x3C, 0)
        rw.assert_equal(self.padding_0x78, 0)
        rw.assert_equal(self.padding_0x90, 0)
        rw.assert_equal(self.padding_0xA8, 0)
        
        rw.verify_stream_offset(rw.tell(), self.name_offsets_offset, HEX32_formatter, self.name_offsets_marker)
        rw.rw_obj(self.name_offsets)
        
        if rw.section_exists(self.meshes_offset, self.mesh_count):
            rw.verify_stream_offset(rw.tell(), self.meshes_offset, HEX32_formatter, self.meshes_marker)
            self.meshes = rw.rw_dynamic_objs(self.meshes, MeshBinaryHundredLine, self.mesh_count)
            for m in self.meshes:
                m.rw_data(rw)
        
        if rw.section_exists(self.materials_offset, self.material_count):
            rw.verify_stream_offset(rw.tell(), self.materials_offset, HEX32_formatter, self.materials_marker)
            self.materials = rw.rw_dynamic_objs(self.materials, MaterialBinaryHundredLine, self.material_count)

        if rw.section_exists(self.lights_offset, self.light_count):
            assert 0, "Nonzero light offset"

        if rw.section_exists(self.cameras_offset, self.camera_count):
            rw.verify_stream_offset(rw.tell(), self.cameras_offset, HEX32_formatter, self.cameras_marker)
            self.cameras = rw.rw_dynamic_objs(self.cameras, CameraBinaryHundredLine, self.camera_count)
        
        rw.align(rw.tell(), 0x10)
        
        if rw.section_exists(self.ibpms_offset, self.ibpm_count):
            rw.verify_stream_offset(rw.tell(), self.ibpms_offset, HEX32_formatter, self.ibpms_marker)
            self.ibpms = rw.rw_float32s(self.ibpms, (self.ibpm_count, 12))

        if rw.section_exists(self.extra_clut_offset, len(self.extra_clut)):
            rw.verify_stream_offset(rw.tell(), self.extra_clut_offset, HEX32_formatter, self.extra_clut_marker)
            self.extra_clut = rw.rw_bytestring(self.extra_clut, 1024 + 0x10 + 0x0C)
        
        if rw.section_exists(self.strings_offset, len(self.string_chunk)):
            rw.verify_stream_offset(rw.tell(), self.strings_offset, HEX32_formatter, self.strings_marker)
            stringchunk_size = rw.rw_descriptor(StringChunkSizeDescriptor, self)
            self.string_chunk = rw.rw_bytestring(self.string_chunk, stringchunk_size)
        rw.align(rw.tell(), 0x10)
    
        rw.verify_stream_offset(rw.tell(), self.skel_offset, HEX32_formatter, self.skel_marker)
        with rw.new_origin():
            rw.rw_obj(self.skel)
        rw.verify_stream_offset(rw.tell(), self.skel_offset + self.skel_size, HEX32_formatter, self.skel_size_marker)
        
        rw.assert_eof()
