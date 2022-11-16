from .Base import MeshBinaryBase, PrimitiveTypes


class MeshBinaryDSCSPS(MeshBinaryBase):
    __DATA_TYPES = {
        0: 'B',
        8: 'e',
        9: 'f'
    }

    __PRIMITIVE_TYPES = {
        0x0000: PrimitiveTypes.TRIANGLE_STRIP,
        0x0004: PrimitiveTypes.TRIANGLES
    }

    @property
    def _CLASSTAG(self):
        return "DSCS PS MeshBinary"

    @property
    def DATA_TYPES(self):
        return self.__DATA_TYPES

    @property
    def PRIMITIVE_TYPES(self):
        return self.__PRIMITIVE_TYPES

    def retrieve_index_rw_function(self, rw):
        dtype = 'H'
        rw.assert_equal(self.index_type, 0)
        return lambda value, shape, endianness=None: rw.rw_multiple(dtype, value, shape, endianness)
