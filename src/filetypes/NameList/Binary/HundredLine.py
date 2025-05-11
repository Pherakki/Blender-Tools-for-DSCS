from ....serialization.DSCSStructs import DSCSSerializable


class NameListBinary(DSCSSerializable):
    def __init__(self):
        self.lines = []
    
    def exbip_rw(self, rw):
        for i, _ in enumerate(rw.array_while_iterator(self.lines, bytes, lambda: len(rw.peek_bytestring(1)))):
            self.lines[i] = rw.rw_cbytestring(self.lines[i], terminator=b"\r\n")
