import enum
import struct

from .....serialization.Serializable import Serializable
from .....serialization.utils import safe_format


class MeshBinaryBase(Serializable):
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
        self.padding_0x18             = None

        self.vertex_attributes_offset = None
        self.matrix_palette_count     = None
        self.vertex_attribute_count   = None
        self.bytes_per_vertex         = None
        self.index_type               = None

        self.vertex_groups_per_vertex = None
        self.meshflags                = None
        self.primitive_type           = None
        self.name_hash                = None
        self.material_id              = None
        self.vertex_count             = None

        self.index_count              = None
        self.padding_0x44             = None
        self.padding_0x48             = None
        self.bounding_sphere_radius   = None
        self.centre_point             = None
        self.bounding_box_diagonal    = None

        # Data holders
        self.VAO = None
        self.matrix_palette = None
        self.IBO = None
        self.vertex_attributes = None

    def __repr__(self):
        return f"[{self._CLASSTAG}: {safe_format(self.name_hash, hex)}] " \
            f"Flags: {safe_format(self.meshflags, hex)} Material: {self.material_id}" \
            f"VAO: {self.vertex_count}/{self.vertices_offset}/{self.bytes_per_vertex} " \
            f"VAs: {self.vertex_attribute_count}/{self.vertex_attributes_offset}/{self.vertex_groups_per_vertex} " \
            f"IBO: {self.index_count}/{self.indices_offset}/{safe_format(self.index_type, hex)}/{self.primitive_type} " \
            f"Matrix Palette: {self.matrix_palette_count}/{self.matrix_palette_offset} " \
            f"Geometry: {self.centre_point} {safe_format(self.bounding_sphere_radius, list)} {safe_format(self.bounding_box_diagonal, list)}"

    def read_write(self, rw):
        """
        Read/write the descriptor for the Mesh.
        These are stored in an array before the mesh contents are given.
        """
        self.vertices_offset          = rw.rw_uint64(self.vertices_offset)
        self.indices_offset           = rw.rw_uint64(self.indices_offset)
        self.matrix_palette_offset    = rw.rw_uint64(self.matrix_palette_offset)
        self.padding_0x18             = rw.rw_uint64(self.padding_0x18)
        rw.assert_is_zero(self.padding_0x18)

        self.vertex_attributes_offset = rw.rw_uint64(self.vertex_attributes_offset)
        self.matrix_palette_count     = rw.rw_uint16(self.matrix_palette_count)
        self.vertex_attribute_count   = rw.rw_uint16(self.vertex_attribute_count)
        self.bytes_per_vertex         = rw.rw_uint16(self.bytes_per_vertex)
        self.index_type               = rw.rw_uint16(self.index_type)  # 0x1403 / GL_UNSIGNED_SHORT for PC

        self.vertex_groups_per_vertex = rw.rw_uint8(self.vertex_groups_per_vertex)  # takes values 0, 1, 2, 3, 4: 0 means map everything to idx 0, 1 means the idxs are in the position vector
        self.meshflags                = rw.rw_uint8(self.meshflags)  # Mesh flags: >>0 - isRendered, >>1 - isWireframe, >>2 - skinning indices are consecutive
        self.primitive_type           = rw.rw_uint16(self.primitive_type)  # 4 or 5: 4 is Triangles, 5 is TriangleStrips... any OpenGL type should work
        self.name_hash                = rw.rw_uint32(self.name_hash)
        self.material_id              = rw.rw_uint32(self.material_id)
        self.vertex_count             = rw.rw_uint32(self.vertex_count)

        self.index_count              = rw.rw_uint32(self.index_count)
        self.padding_0x44             = rw.rw_uint32(self.padding_0x44)
        rw.assert_is_zero(self.padding_0x44)
        self.padding_0x48             = rw.rw_uint32(self.padding_0x48)
        rw.assert_is_zero(self.padding_0x48)
        self.bounding_sphere_radius   = rw.rw_float32(self.bounding_sphere_radius)

        self.centre_point             = rw.rw_float32s(self.centre_point, 3)
        self.bounding_box_diagonal    = rw.rw_float32s(self.bounding_box_diagonal, 3)

    def rw_contents(self, rw):
        self.rw_VAO(rw)
        self.rw_matrix_palette(rw)
        self.rw_IBO(rw)
        self.rw_vertex_attributes(rw)

    def rw_VAO(self, rw):
        """
        Read/write the vertex data.
        Corresponds to an OpenGL Vertex Array Object (VAO).
        """
        rw.assert_local_file_pointer_now_at("VAO", self.vertices_offset)
        self.VAO = rw.rw_bytestring(self.VAO, self.vertex_count*self.bytes_per_vertex)

    def rw_matrix_palette(self, rw):
        """
        Read/write the matrix palette.
        States which bones are used by the mesh.
        """
        rw.assert_local_file_pointer_now_at("Matrix Palette", self.matrix_palette_offset)
        self.matrix_palette = rw.rw_uint32s(self.matrix_palette, self.matrix_palette_count)

    def rw_IBO(self, rw):
        """
        Read/write the vertex indices.
        Corresponds to an OpenGL Index Buffer Object (IBO).
        """
        rw.assert_local_file_pointer_now_at("IBO", self.indices_offset)
        rw_func = self.retrieve_index_rw_function(rw)
        self.IBO = rw_func(self.IBO, self.index_count)
        rw.align(rw.local_tell(), 0x04)

    def rw_vertex_attributes(self, rw):
        """
        Read/write the vertex attributes.
        States what properties each vertex contains.
        """
        rw.assert_local_file_pointer_now_at("Vertex Attributes", self.vertex_attributes_offset)
        self.vertex_attributes = rw.rw_obj_array(self.vertex_attributes, VertexAttribute, self.vertex_attribute_count)

    ########################################
    # Helpers for (de)serialising vertices #
    ########################################
    def unpack_vertices(self):
        # Inefficient but can't do much more with Python without making the code very unclean
        vertices = [Vertex() for _ in range(self.vertex_count)]
        unpack_funcs = [None]*len(self.vertex_attributes)
        struct_fmts = [None]*len(self.vertex_attributes)
        for i, vertex_attribute in enumerate(self.vertex_attributes):
            dtype = self.DATA_TYPES[vertex_attribute.type]*vertex_attribute.elem_count
            dsize = struct.calcsize(dtype)
            struct_fmts[i] = (dtype, dsize)
            if vertex_attribute.normalised:
                if   dtype[0] == 'b': exp = 7
                elif dtype[0] == 'B': exp = 8
                elif dtype[0] == 'h': exp = 15
                elif dtype[0] == 'H': exp = 16
                elif dtype[0] == 'i': exp = 31
                elif dtype[0] == 'I': exp = 32
                else: raise ValueError("Non-integer Vertex Attribute was set to 'normalised'")
                unpack_funcs[i] = lambda x, dtype=dtype: [val / 2**(exp) for val in struct.unpack(dtype, x)]
            else:
                unpack_funcs[i] = lambda x, dtype=dtype: struct.unpack(dtype, x)

        for vertex_idx, vertex in enumerate(vertices):
            for unpack_func, (dtype, size), va in zip(unpack_funcs, struct_fmts, self.vertex_attributes):
                byte_idx = vertex_idx * self.bytes_per_vertex + va.offset
                bytes = self.VAO[byte_idx:byte_idx + size]
                vertex.buffer[va.index] = unpack_func(bytes)

        return vertices

    def pack_vertices(self, vertices):
        vertex_binaries = [None]*len(vertices)
        pack_funcs  = [None]*len(self.vertex_attributes)
        fmt_sizes = [None] * len(self.vertex_attributes)
        chunk_sizes = [None] * len(self.vertex_attributes)
        total_size = 0
        sorted_vas = sorted(self.vertex_attributes, key=lambda x: x.offset)
        for i, vertex_attribute in enumerate(sorted_vas):
            dtype = self.DATA_TYPES[vertex_attribute.type]*vertex_attribute.elem_count
            fmt_sizes[i] = struct.calcsize(dtype)
            if vertex_attribute.normalised:
                if   dtype[0] == 'b': exp = 7
                elif dtype[0] == 'B': exp = 8
                elif dtype[0] == 'h': exp = 15
                elif dtype[0] == 'H': exp = 16
                elif dtype[0] == 'i': exp = 31
                elif dtype[0] == 'I': exp = 32
                else: raise ValueError("Non-integer Vertex Attribute was set to 'normalised'")
                pack_funcs[i] = lambda x, dtype=dtype: [int(val * 2**(exp)) for val in struct.pack(dtype, x)]
            else:
                pack_funcs[i] = lambda x, dtype=dtype: struct.pack(dtype, *x)

        for i, (va1, va2) in enumerate(zip(sorted_vas, sorted_vas[1:])):
            chunk_sizes[i] = va2.offset - va1.offset
        chunk_sizes[-1] = self.bytes_per_vertex - sorted_vas[-1].offset
        vertex_binary = [None]*len(self.vertex_attributes)
        for vertex_idx, vertex in enumerate(vertices):
            for va_idx, (pack_func, fmt_size, alloc_size, va) in enumerate(zip(pack_funcs, fmt_sizes, chunk_sizes, sorted_vas)):
                vertex_binary[va_idx] = pack_func(vertex.buffer[va.index])
                vertex_binary[va_idx] += b'\x00'*(alloc_size - fmt_size)
            vertex_binaries[vertex_idx] = b''.join(vertex_binary)
        return b''.join(vertex_binaries)

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


class PrimitiveTypes:
    POINTS         = 0
    LINES          = 1
    LINE_LOOP      = 2
    LINE_STRIP     = 3
    TRIANGLES      = 4
    TRIANGLE_STRIP = 5
    TRIANGLE_FAN   = 6
    QUADS          = 7
    QUAD_STRIP     = 8
    POLYGON        = 9


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


class VertexAttribute(Serializable):
    def __init__(self):
        super().__init__()
        self.index      = None
        self.normalised = None
        self.elem_count = None
        self.type       = None
        self.offset     = None

    def __repr__(self):
        return f"[Geom::Mesh::VertexAttribute] {self.index} {self.normalised} {self.elem_count} {self.type} {self.offset}"

    def read_write(self, rw):
        self.index      = rw.rw_uint8(self.index)
        self.normalised = rw.rw_uint8(self.normalised)  # Unused in cgGL
        self.elem_count = rw.rw_uint16(self.elem_count)
        self.type       = rw.rw_uint16(self.type)
        self.offset     = rw.rw_uint16(self.offset)


class Vertex:
    __slots__ = ("buffer",)

    def __init__(self):
        self.buffer = [None]*12

    def __repr__(self):
        return f"[Geom::Mesh::Vertex] {self.position} {self.normal} {self.tangent} {self.binormal} {self.UV1} {self.UV2} {self.UV3} {self.color} {self.indices} {self.weights}"

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
