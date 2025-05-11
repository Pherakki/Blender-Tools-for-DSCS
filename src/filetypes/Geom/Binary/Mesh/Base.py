import math
import struct

from .....serialization.DSCSStructs import DSCSSerializable
from .....serialization.DSCSFormatters import HEX32_formatter, list_formatter
from .....serialization import OffsetMarker
from ...Constants import AttributeTypes, PrimitiveTypes


class MeshBinaryBase(DSCSSerializable):
    """
    A class to read mesh data within geom files. These files are split into five main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section that contains raw byte data for each vertex, corresponding to an OpenGL VAO.
        3. A section that contains the indices of bones used by the mesh - the "Matrix Palette".
        4. A section of vertex indices, corresponding to an OpenGL IBO.
        5. A section of vertex attributes, similar but not identical to an OpenGL vertex attributes.

    The headers for each Mesh are stored together in an array that immediately precedes the Mesh data.

    Completion status
    ------
    (o) MeshReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (o) MeshReader can fully interpret all mesh data in geom files in DSDB archive.
    (o) MeshReader can write data to geom files.

    """
    def __init__(self):
        super().__init__()

        # Header variables
        self.vertices_offset          = None
        self.indices_offset           = None
        self.matrix_palette_offset    = None
        self.padding_0x18             = 0

        self.vertex_attributes_offset = None
        self.matrix_palette_count     = None
        self.vertex_attribute_count   = None
        self.bytes_per_vertex         = None
        self.index_type               = None

        self.vertex_groups_per_vertex = None
        self.flags                    = None
        self.primitive_type           = None
        self.name_hash                = None
        self.material_id              = None
        self.vertex_count             = None

        self.index_count              = None
        self.padding_0x44             = 0
        self.padding_0x48             = 0
        self.bounding_sphere_radius   = None
        self.centre_point             = None
        self.bounding_box_diagonal    = None

        # Data holders
        self.VBO = None
        self.matrix_palette = None
        self.IBO = None
        self.vertex_attributes = None
        
        # Offset Calculators
        self.vertices_marker          = OffsetMarker().subscribe(self, "vertices_offset")
        self.indices_marker           = OffsetMarker().subscribe(self, "indices_offset")
        self.matrix_palette_marker    = OffsetMarker().subscribe(self, "matrix_palette_offset")
        self.vertex_attributes_marker = OffsetMarker().subscribe(self, "vertex_attributes_offset")

    def __repr__(self):
        return f"[{self._CLASSTAG}: {HEX32_formatter(self.name_hash)}] " \
            f"Flags: {HEX32_formatter(self.flags)} Material: {self.material_id} " \
            f"VAO: {self.vertex_count}/{self.vertices_offset}/{self.bytes_per_vertex} " \
            f"VAs: {self.vertex_attribute_count}/{self.vertex_attributes_offset}/{self.vertex_groups_per_vertex} " \
            f"IBO: {self.index_count}/{self.indices_offset}/{HEX32_formatter(self.index_type)}/{self.primitive_type} " \
            f"Matrix Palette: {self.matrix_palette_count}/{self.matrix_palette_offset} " \
            f"Geometry: {self.centre_point} {self.bounding_sphere_radius} {list_formatter(self.bounding_box_diagonal)}"

    def exbip_rw(self, rw):
        """
        Read/write the descriptor for the Mesh.
        These are stored in an array before the mesh contents are given.
        """
        self.vertices_offset          = rw.rw_uint64(self.vertices_offset)
        self.indices_offset           = rw.rw_uint64(self.indices_offset)
        self.matrix_palette_offset    = rw.rw_uint64(self.matrix_palette_offset)
        self.padding_0x18             = rw.rw_uint64(self.padding_0x18)
        rw.assert_equal(self.padding_0x18, 0)

        self.vertex_attributes_offset = rw.rw_uint64(self.vertex_attributes_offset)
        self.matrix_palette_count     = rw.rw_uint16(self.matrix_palette_count)
        self.vertex_attribute_count   = rw.rw_uint16(self.vertex_attribute_count)
        self.bytes_per_vertex         = rw.rw_uint16(self.bytes_per_vertex)
        self.index_type               = rw.rw_uint16(self.index_type)  # 0x1403 / GL_UNSIGNED_SHORT for PC

        self.vertex_groups_per_vertex = rw.rw_uint8(self.vertex_groups_per_vertex)  # takes values 0, 1, 2, 3, 4: 0 means map everything to idx 0, 1 means the idxs are in the position vector
        self.flags                    = rw.rw_uint8(self.flags)  # Mesh flags: >>0 - isRendered, >>1 - isWireframe, >>2 - skinning indices are consecutive
        self.primitive_type           = rw.rw_uint16(self.primitive_type)  # 4 or 5: 4 is Triangles, 5 is TriangleStrips... any OpenGL type should work
        self.name_hash                = rw.rw_uint32(self.name_hash)
        self.material_id              = rw.rw_uint32(self.material_id)
        self.vertex_count             = rw.rw_uint32(self.vertex_count)

        self.index_count              = rw.rw_uint32(self.index_count)
        self.padding_0x44             = rw.rw_uint32(self.padding_0x44)
        rw.assert_equal(self.padding_0x44, 0)
        self.padding_0x48             = rw.rw_uint32(self.padding_0x48)
        rw.assert_equal(self.padding_0x48, 0)
        self.bounding_sphere_radius   = rw.rw_float32(self.bounding_sphere_radius)

        self.centre_point             = rw.rw_float32s(self.centre_point, 3)
        self.bounding_box_diagonal    = rw.rw_float32s(self.bounding_box_diagonal, 3)

    def rw_contents(self, rw):
        
        rw.verify_stream_offset(self.vertices_offset, "Vertex Buffer Object", HEX32_formatter, self.vertices_marker)
        self.VBO = rw.rw_bytestring(self.VBO, self.vertex_count*self.bytes_per_vertex)
        
        rw.verify_stream_offset(self.matrix_palette_offset, "Matrix Palette", HEX32_formatter, self.matrix_palette_offset)
        self.matrix_palette = rw.rw_uint32s(self.matrix_palette, self.matrix_palette_count)
        
        rw.verify_stream_offset(self.indices_offset, "Index Buffer Object", HEX32_formatter, self.indices_marker)
        self.IBO = self.retrieve_index_rw_function(rw)(self.IBO, self.index_count)
        rw.align(rw.tell(), 0x04)
        
        rw.verify_stream_offset(self.vertex_attributes_offset, "Vertex Attributes", HEX32_formatter, self.vertex_attributes_marker)
        self.vertex_attributes = rw.rw_dynamic_objs(self.vertex_attributes, VertexAttributeBinary, self.vertex_attribute_count)
    
    
    @property
    def vertices(self):
        vertices = [Vertex() for _ in range(self.vertex_count)]
        VBO    = self.VBO
        vcount = self.vertex_count
        stride = self.bytes_per_vertex
        
        for va in self.vertex_attributes:
            offset  = va.offset
            va_idx  = va.index
            dtype = self.DATA_TYPES[va.type]*va.elem_count
            dsize = struct.calcsize(dtype)
            
            unpack  = struct.Struct(dtype).unpack
            
            # OpenGL 4.2+: signed int mapping x -> max(x/INT_MAX, -1)
            # OpenGL <4.2: signed int mapping x -> (2*x + 1) / (UINT_MAX)
            if va.normalised:
                if   dtype[0] == 'b': unpack_fn = lambda data: [max(v/0x7F,      -1) for v in unpack(data)]
                elif dtype[0] == 'h': unpack_fn = lambda data: [max(v/0x7FFF,    -1) for v in unpack(data)]
                elif dtype[0] == 'i': unpack_fn = lambda data: [max(v/0x7FFFFFFF,-1) for v in unpack(data)]
                elif dtype[0] == 'B': unpack_fn = lambda data: [v/0xFF               for v in unpack(data)]
                elif dtype[0] == 'H': unpack_fn = lambda data: [v/0xFFFF             for v in unpack(data)]
                elif dtype[0] == 'I': unpack_fn = lambda data: [v/0xFFFFFFFF         for v in unpack(data)]
                else: unpack_fn = unpack
            else:
                unpack_fn = unpack
            
            # Unpack specified attribute
            for i in range(vcount):
                start = offset+i*stride
                vertices[i].buffer[va_idx] = unpack_fn(VBO[start:start+dsize])
        
        return vertices
        
    @vertices.setter
    def vertices(self, vertices):
        stride = self.bytes_per_vertex
        vcount = len(vertices)
        
        VBO = bytearray(stride*vcount)
        for va in self.vertex_attributes:
            offset = va.offset
            va_idx = va.index
            dtype = self.DATA_TYPES[va.type]*va.elem_count
            dsize = struct.calcsize(dtype)
            
            pack  = struct.Struct(dtype).pack
            
            # OpenGL 4.2+: signed int mapping x -> max(x/INT_MAX, -1)
            # OpenGL <4.2: signed int mapping x -> (2*x + 1) / (UINT_MAX)
            if va.normalised:
                if   dtype[0] == 'b': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0x7F,      0)),0x7F      ),-0x80      )) for v in data])
                elif dtype[0] == 'h': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0x7FFF,    0)),0x7FFF    ),-0x8000    )) for v in data])
                elif dtype[0] == 'i': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0x7FFFFFFF,0)),0x7FFFFFFF),-0x80000000)) for v in data])
                elif dtype[0] == 'B': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0xFF,      0)),0xFF      ),0)          ) for v in data])
                elif dtype[0] == 'H': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0xFFFF,    0)),0xFFFF    ),0)          ) for v in data])
                elif dtype[0] == 'I': pack_fn = lambda *data: pack(*[(max(min(int(round(v*0xFFFFFFFF,0)),0xFFFFFFFF),0)          ) for v in data])
                else: pack_fn = pack
            else:
                pack_fn = pack
            
            # Unpack specified attribute
            for i in range(vcount):
                start = offset+i*stride
                VBO[start:start+dsize] = pack_fn(*vertices[i].buffer[va_idx])
        
        self.VBO = VBO
        self.vertex_count = vcount

    def get_default_unpack_shader_transforms(self):
        return self.get_default_shader_transforms()

    def get_default_pack_shader_transforms(self):
        return self.get_default_shader_transforms()[::-1]
    
    def get_unpack_shader_transforms(self, override_transforms=None):
        if override_transforms is None:
            return self.get_default_shader_transforms()
        else:
            return override_transforms
    
    def get_pack_shader_transforms(self, override_transforms=None):
        if override_transforms is None:
            return self.get_default_shader_transforms()[::-1]
        else:
            return override_transforms[::-1]
        
    def apply_shader_transforms_pack(self, vertices, vertex_attributes, override_transforms=None):
        if not len(vertices):
            return
        
        transforms = self.get_pack_shader_transforms(override_transforms)
        transforms = [t for t in transforms if t.poll(vertices[0])]   
        
        attr_transforms = [t for t in transforms if t.TRANSFORM_ATTRS]
        for transform in attr_transforms:
            transform.attribute_transform_pack(vertex_attributes)
            
        vtx_transforms = [t for t in transforms if t.TRANSFORM_VERTICES]
        for vertex in vertices:
            for transform in vtx_transforms:
                transform.vertex_transform_pack(vertex)
        
    def apply_shader_transforms_unpack(self, vertices, vertex_attributes, override_transforms=None):
        if not len(vertices):
            return
        
        transforms = self.get_unpack_shader_transforms(override_transforms)
        transforms = [t for t in transforms if t.poll(vertices[0])]   
        
        # attr_transforms = [t for t in transforms if t.TRANSFORM_ATTRS]
        # for transform in attr_transforms:
        #     transform.attribute_transform_unpack(vertex_attributes)
            
        vtx_transforms = [t for t in transforms if t.TRANSFORM_VERTICES]
        for vertex in vertices:
            for transform in vtx_transforms:
                transform.vertex_transform_unpack(vertex)
        

    @property
    def INVERSE_DATA_TYPES(self):
        return {v: i for i, v in self.DATA_TYPES.items()}

    # VIRTUAL PROPERTIES
    @property
    def _CLASSTAG(self):
        raise NotImplementedError("_CLASSTAG not implemented on subclass")

    @property
    def DATA_TYPES(self):
        return NotImplementedError("DATA_TYPES not implemented on subclass")

    @property
    def PRIMITIVE_TYPES(self):
        return NotImplementedError("PRIMITIVE_TYPES not implemented on subclass")

    def retrieve_index_rw_function(self, rw):
        raise NotImplementedError("retrieve_index_rw_function not implemented on subclass")

    def get_default_shader_transforms(self):
        # Deprecate in favour of the below two methods: this is not a commutative operation
        raise NotImplementedError("get_default_shader_transforms not implemented on subclass")

    def get_default_vertex_attributes(cls, vertex, shader_transforms):
        raise NotImplementedError("get_default_vertex_attributes not implemented on subclass")


class VertexAttributeBinary(DSCSSerializable):
    def __init__(self, index=None, normalised=None, elem_count=None, type=None, offset=None):
        super().__init__()
        self.index      = index
        self.normalised = normalised
        self.elem_count = elem_count
        self.type       = type
        self.offset     = offset

    def __repr__(self):
        return f"[Geom::Mesh::VertexAttributeBinary] {self.index} {self.normalised} {self.elem_count} {self.type} {self.offset}"

    def exbip_rw(self, rw):
        self.index      = rw.rw_uint8(self.index)
        self.normalised = rw.rw_uint8(self.normalised)  # Unused in cgGL
        self.elem_count = rw.rw_uint16(self.elem_count)
        self.type       = rw.rw_uint16(self.type)
        self.offset     = rw.rw_uint16(self.offset)


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
