from .Base import MeshBinaryBase, PrimitiveTypes
from ...Constants import AttributeTypes
from .ShaderTransforms import UVDiv1024


class MeshBinaryMegido72(MeshBinaryBase):
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
        return "Megido72 MeshBinary"

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
        return [UVDiv1024(AttributeTypes.UV1), UVDiv1024(AttributeTypes.UV2), UVDiv1024(AttributeTypes.UV3)]
