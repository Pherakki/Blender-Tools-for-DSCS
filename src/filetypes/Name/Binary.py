from ...serialization.DSCSStructs import DSCSSerializable
import array


class NameSizes:
    def deserialize(rw, name_offsets, names):
        sizes = array.array('I', b'\x00'*4*(len(name_offsets)))
        
        if len(name_offsets):
            for i, (p1, p2) in enumerate(zip(name_offsets, name_offsets[1:])):
                sizes[i] = p2-p1
            
            # if len(name_offsets):
            # Figure out how big the final string is
            curpos = rw.tell()
            rw.seek(0, 2) # Seek to EOF
            sizes[-1] = rw.tell() - name_offsets[-1]
            rw.seek(curpos, 0) # Seek back to start
        return sizes

    def serialize(rw, name_offsets, names):
        return
    
    def count(rw, name_offsets, names):
        return

    def calculate_offsets(rw, name_offsets, names):
        name_offsets.clear()
        base = rw.tell()
        for name in names:
            name_offsets.append(base)
            base += len(name)
        return


class NameFileBinary(DSCSSerializable):
    def __init__(self):
        self.bone_name_count     = 0
        self.material_name_count = 0
        self.name_offsets        = []
        self.names               = []
        
    def exbip_rw(self, rw):
        self.bone_name_count     = rw.rw_int32(self.bone_name_count)
        self.material_name_count = rw.rw_int32(self.material_name_count)
        self.name_offsets        = rw.rw_uint32s(self.name_offsets, self.bone_name_count + self.material_name_count)
        sizes = rw.rw_descriptor(NameSizes, self.name_offsets, self.names)       
        self.names               = rw.rw_bytestrings(self.names, sizes)
        rw.assert_eof()
