import array

from ...serialization.Serializable import Serializable


class DetrBinary(Serializable):

    def __init__(self):
        super().__init__()
        self.context.endianness = '<'

        # Variables that appear in the file header
        self.filetype = b'MSET'[::-1]
        self.version        = 1 # REQUIRED TO BE 1 BY DSCS
        self.element_count  = 0
        self.unknown_floats = []
        self.unknown_0x20   = 0
        self.unknown_0x24   = 0
        
        self.elements = []

    
    def read_write(self, rw):
        rw.assert_file_pointer_now_at("File start", 0)

        self.filetype = rw.rw_bytestring(self.filetype, 4)
        self.version  = rw.rw_uint32(self.version)
        rw.assert_equal(self.filetype, b'MSET'[::-1])
        rw.assert_equal(self.version, 1)
        
        self.element_count  = rw.rw_uint32(self.element_count)
        self.unknown_floats = rw.rw_float32s(self.unknown_floats, 5)
        self.unknown_0x20   = rw.rw_uint32(self.unknown_0x20)
        self.unknown_0x24   = rw.rw_uint32(self.unknown_0x24) # Looks like flags...

        # Elements
        self.elements = rw.rw_obj_array(self.elements, DetrElement, self.element_count)
        

class DetrElement(Serializable):
    def __init__(self):
        super().__init__()
        self.context.endianness = '<'

        # Variables that appear in the file header
        # Get the scaled quaternion by doing:
        #  1) Convert bone quaternion to rotation matrix
        #  2) Multiply rotation matrix by scale matrix
        #  3) Covert back to quaternion without normalising
        self.unknown_0x00 = 0
        self.unknown_0x02 = 0
        self.size         = 0
        self.element_type = b'DNAV'[::-1]
        self.unknown_0x0C = 7 # REQUIRED TO BE 7 BY DSCS
        
        self.unknown_0x10 = 0
        self.unknown_0x14 = 0
        self.unknown_0x18 = 0
        self.unknown_0x1C = 0
        
        self.unknown_0x20 = 0
        self.position_count = 0
        self.unknown_0x28 = 0
        self.unknown_0x2C = 0
    
        self.unknown_0x30 = 0
        self.unknown_0x34 = 0
        self.unknown_0x38 = 0
        self.unknown_0x3C = 0
        
        self.unknown_0x40 = 0
        
        self.unknown_floats = []
        
        self.positions = []
        self.remainder = b''

    def read_write(self, rw):
        st = rw.tell()
        self.unknown_0x00 = rw.rw_uint16(self.unknown_0x00) # Index?
        self.unknown_0x02 = rw.rw_uint16(self.unknown_0x02) # Index?
        self.size         = rw.rw_uint32(self.size)
        self.element_type = rw.rw_bytestring(self.element_type, 4)
        self.unknown_0x0C = rw.rw_uint32(self.unknown_0x0C) # 7
        
        self.unknown_0x10 = rw.rw_uint32(self.unknown_0x10) # Index?
        self.unknown_0x14 = rw.rw_uint32(self.unknown_0x14) # Index?
        self.unknown_0x18 = rw.rw_uint32(self.unknown_0x18) # 0
        self.unknown_0x1C = rw.rw_uint32(self.unknown_0x1C) # 0
        
        self.unknown_0x20 = rw.rw_uint32(self.unknown_0x20) # 76 bytes per entry? Must be composite...
        self.position_count = rw.rw_uint32(self.position_count) # 12 bytes each - 3 floats
        self.unknown_0x28 = rw.rw_uint32(self.unknown_0x28) # 12 bytes each # I hope it's not rotation
        self.unknown_0x2C = rw.rw_uint32(self.unknown_0x2C) # Same as 0x20
        
        self.unknown_0x30 = rw.rw_uint32(self.unknown_0x30) # 12 bytes each # Hope it's not scale...
        self.unknown_0x34 = rw.rw_uint32(self.unknown_0x34) # 4 bytes each # And float channel...
        self.unknown_0x38 = rw.rw_uint32(self.unknown_0x38) # 2x 0x20
        self.unknown_0x3C = rw.rw_uint32(self.unknown_0x3C) # 0
        
        self.unknown_0x40 = rw.rw_uint32(self.unknown_0x40) # Same as 0x20
        
        self.unknown_floats = rw.rw_float32s(self.unknown_floats, 10)
        
        self.positions = rw.rw_float32s(self.positions, (self.position_count, 3))
        cpos = rw.tell()
        remaining_bytes = self.size - (cpos-st) + 8
        self.remainder = rw.rw_bytestring(self.remainder, remaining_bytes)
        