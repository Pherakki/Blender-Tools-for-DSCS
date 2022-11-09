import enum

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
        self.index_type               = rw.rw_uint16(self.index_type) # 0x1403 / GL_UNSIGNED_SHORT for PC

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
        rw.assert_local_file_pointer_now_at(self.vertices_offset)
        self.VAO = rw.rw_bytestring(self.VAO, self.vertex_count*self.bytes_per_vertex)

    def rw_matrix_palette(self, rw):
        """
        Read/write the matrix palette.
        States which bones are used by the mesh.
        """
        rw.assert_local_file_pointer_now_at(self.matrix_palette_offset)
        self.matrix_palette = rw.uint32s(self.matrix_palette, self.matrix_palette_count)

    def rw_IBO(self, rw):
        """
        Read/write the vertex indices.
        Corresponds to an OpenGL Index Buffer Object (IBO).
        """
        rw.assert_local_file_pointer_now_at(self.indices_offset)
        rw_func = self.retrieve_index_rw_function(rw)
        self.IBO = rw_func(self.IBO, self.index_count)
        rw.align(rw.local_tell(), 0x04)

    def rw_vertex_attributes(self, rw):
        """
        Read/write the vertex attributes.
        States what properties each vertex contains.
        """
        rw.assert_local_file_pointer_now_at(self.vertex_attributes_offset)
        self.vertex_attributes = rw.rw_obj_array(self.vertex_attributes, VertexAttribute, self.vertex_attribute_count)

    def unpack_vertex_attribute_data(self, vertex_idx, vertex_attribute, type_size, unpack_func):
        byte_idx = vertex_idx * self.bytes_per_vertex + vertex_attribute.offset
        bytes = self.VAO[byte_idx:byte_idx + vertex_attribute.size*type_size]
        return unpack_func(bytes)

    def unpack_vertices(self):
        verts = [Vertex()]*self.vertex_count
        for vertex_attribute in self.vertex_attributes:
            assign_func = vertex_attribute.retrieve_unpack_func(self._VA_MAP)
            type_size, unpack_func = self.retrieve_primitive_type_info(vertex_attribute.type)
            for i, vert in enumerate(verts):
                value = self.unpack_vertex_attribute_data(i, vertex_attribute, type_size, unpack_func)
                assign_func(vert, value)

    def pack_vertices(self, vertex_array):
        raise NotImplementedError("pack_vertices not implemented on subclass")

    # VIRTUAL PROPERTIES
    @property
    def _CLASSTAG(self):
        raise NotImplementedError("_CLASSTAG not implemented on subclass")

    @property
    def _VA_MAP(self):
        raise NotImplementedError("_VA_MAP not implemented on subclass")

    def retrieve_index_rw_function(self, rw):
        # Should use retrieve_primitive_type_info to get the type
        raise NotImplementedError("retreive_index_rw_function not implemented on subclass")

    def retrieve_primitive_type_info(self, rw):
        raise NotImplementedError("retrieve_primitive_type_info not implemented on subclass")


class AttributeTypes(enum.Enum):
    POSITION = 0
    NORMAL   = 1
    TANGENT  = 2
    BINORMAL = 3
    COLOR    = 4
    UV1      = 5
    UV2      = 6
    UV3      = 7
    INDEX    = 8
    WEIGHT   = 9


class VertexAttribute:
    def __init__(self):
        super().__init__()
        self.index = None
        self.normalised = None
        self.size = None
        self.type = None
        self.offset = None

    def read_write(self, rw):
        self.index      = rw.rw_uint8(self.index)
        self.normalised = rw.rw_uint8(self.normalised)
        self.size       = rw.rw_uint16(self.size)
        self.type       = rw.rw_uint16(self.type)
        self.offset     = rw.rw_uint16(self.offset)

    def retrieve_unpack_func(self, index_mapping):
        lookup = index_mapping.get(self.index, -1)  # Need to map this depending on exact VertexAttribute type...
        if lookup == AttributeTypes.POSITION:
            def unpack_func(vert, x): vert.position = x
        elif lookup == AttributeTypes.NORMAL:
            def unpack_func(vert, x): vert.normal = x
        elif lookup == AttributeTypes.TANGENT:
            def unpack_func(vert, x): vert.tangent = x
        elif lookup == AttributeTypes.BINORMAL:
            def unpack_func(vert, x): vert.binormal = x
        elif lookup == AttributeTypes.COLOR:
            def unpack_func(vert, x): vert.color = x
        elif lookup == AttributeTypes.UV1:
            def unpack_func(vert, x): vert.UV1 = x
        elif lookup == AttributeTypes.UV2:
            def unpack_func(vert, x): vert.UV2 = x
        elif lookup == AttributeTypes.UV3:
            def unpack_func(vert, x): vert.UV3 = x
        elif lookup == AttributeTypes.INDEX:
            def unpack_func(vert, x): vert.indices = x
        elif lookup == AttributeTypes.WEIGHT:
            def unpack_func(vert, x): vert.weights = x
        elif lookup == -1:
            raise ValueError(f"Unmapped Vertex Attribute Type: {self.index}")
        else:
            raise NotImplementedError(f"Unimplemented Vertex Attribute Type: {lookup}")

        return unpack_func


class Vertex:
    __slots__ = ("position", "normal", "tangent", "binormal", "color", "UV1", "UV2", "UV3", "indices", "weights")

    def __init__(self):
        self.position        = None
        self.normal          = None
        self.tangent         = None
        self.binormal        = None
        self.color           = None
        self.UV1             = None
        self.UV2             = None
        self.UV3             = None
        self.indices         = None
        self.weights         = None
