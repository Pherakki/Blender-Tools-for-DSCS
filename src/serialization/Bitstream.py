class BitstreamReader:
    def __init__(self, data):
        self._buf = memoryview(data)
        self.scratchspace = 0
        self.buffer_index = 0
        self.chunk_index  = 0
        
        self.type_bytesize = self._buf.itemsize
        self.type_bitsize  = self.typesize*8
        self.type_mask     = (1 << self.type_bytesize) - 1
        
    
    def get(self, n_bits):
        if self.chunk_index < n_bits:
            self.scratchspace &= self._buf[self.buffer_index] << self._type_bitsize
            self.buffer_index += 1
        rval = self.scratchspace & self._type_mask
        self.scratchspace >>= n_bits
        return rval
    
class BitstreamReader1B:
    def __init__(self, data):
        self._buf = memoryview(data)
        self.buffer_index = 0
        self.chunk_index  = 0
        
        if self._buf.itemsize != 1:
            raise ValueError("Initialised 1-byte bitreader with data that does not have byte-sized elements")
        
        def get(self):
            rval = (self._buf[self.buffer_index] >> self.chunk_index) & 1
            self.chunk_index += 1
            if self.chunk_index == 8:
                self.chunk_index = 0
                self.buffer_index += 1
            return rval

class BitstreamWriter1B:
    def __init__(self, initial_capacity):
        self._buf = bytearray(initial_capacity)
        self.buffer_index = 0
        self.chunk_index  = 0
    
    def put(self, value):
        self._buf[self.buffer_index] |= (value & 1) << self.chunk_index
        self.chunk_index += 1
        if self.chunk_index == 8:
            self.chunk_index = 0
            self.buffer_index += 1
            if self.buffer_index >= len(self._buf):
                self._buf += b'\x00'
