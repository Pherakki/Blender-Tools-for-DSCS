import copy

from ...Constants import AttributeTypes
from .Base import MeshBinaryBase, PrimitiveTypes, VertexAttributeBinary
from .ShaderTransforms import PosPackedIndex, IndexDiv3


class MeshBinaryDSCSOpenGL(MeshBinaryBase):
    __DATA_TYPES = {
        0x1400: 'b',
        0x1401: 'B',
        0x1402: 'h',
        0x1403: 'H',
        0x1404: 'i',
        0x1405: 'I',
        0x1406: 'f',
        0x140A: 'd',
        0x140B: 'e'
    }

    __PRIMITIVE_TYPES = {
        0x0000: PrimitiveTypes.POINTS,
        0x0001: PrimitiveTypes.LINES,
        0x0002: PrimitiveTypes.LINE_LOOP,
        0x0003: PrimitiveTypes.LINE_STRIP,
        0x0004: PrimitiveTypes.TRIANGLES,
        0x0005: PrimitiveTypes.TRIANGLE_STRIP,
        0x0006: PrimitiveTypes.TRIANGLE_FAN
    }

    @property
    def _CLASSTAG(self):
        return "DSCS CgGL MeshBinary"

    @property
    def DATA_TYPES(self):
        return self.__DATA_TYPES

    @property
    def PRIMITIVE_TYPES(self):
        return self.__PRIMITIVE_TYPES

    def retrieve_index_rw_function(self, rw):
        dtype = self.__DATA_TYPES[self.index_type]
        return lambda value, shape, endianness=None: rw.rw_multiple(dtype, value, shape, endianness)

    def get_default_shader_transforms(self):
        if self.vertex_groups_per_vertex == 1:
            return [PosPackedIndex()] # Index Div 3
        else:
            return []

    def get_default_vertex_attributes(self, vertex):
        INVERSE_DATA_TYPES = self.INVERSE_DATA_TYPES
        
        def add_va(vas, vertex, offset, attr_type, dtype, dsize):
            attr = vertex.buffer[attr_type]
            if attr is not None:
                count = len(attr)
                va = VertexAttributeBinary(attr_type, 0, count, INVERSE_DATA_TYPES[dtype], offset)
                vas[attr_type] = va
                return dsize*count
            else:
                return 0
            
        vas = {}
        offset = 0
        offset += add_va(vas, vertex, offset, AttributeTypes.POSITION, 'f', 4)
        offset += add_va(vas, vertex, offset, AttributeTypes.NORMAL,   'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV1,      'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV2,      'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.UV3,      'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.COLOR,    'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.TANGENT,  'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.BINORMAL, 'e', 2)
        offset += add_va(vas, vertex, offset, AttributeTypes.INDEX,    'B', 1)
        offset += add_va(vas, vertex, offset, AttributeTypes.WEIGHT,   'e', 2)
        return vas
