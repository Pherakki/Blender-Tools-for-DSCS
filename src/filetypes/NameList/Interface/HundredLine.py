from ..Binary.HundredLine import NameListBinary
from ....utilities.Hash import dscs_hash


class NLSTBase:
    def __init__(self):
        self._name_bytes = b""

    @classmethod
    def create(cls, name):
        instance = cls()
        if type(name) is bytes: instance._name_bytes = name
        else:                   instance.name = name
        return instance
    
    @property
    def name(self):
        return self._name_bytes.decode('ascii')
    @name.setter
    def name(self, value):
        self._name_bytes = value.encode('ascii')
    

class NLSTMesh(NLSTBase):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"MeshName({self.name})"
    
    @property
    def parent(self):
        return -1

    @property
    def _dtype_bytes(self):
        return b"mesh"
    
    @property
    def dtype(self):
        return "mesh"

    
class NLSTBone(NLSTBase):
    def __init__(self):
        super().__init__()
        self.parent = -1
        self._dtype_bytes = b""
    
    def __repr__(self):
        return f"BoneName({self.name}, {self.parent}, {self.dtype})"
    
    @classmethod
    def create(cls, name, parent, dtype):
        instance = super().create(name)
        instance.parent = parent
        
        if type(dtype) is bytes: instance._dtype_bytes = dtype
        else:                    instance.dtype = dtype
        
        return instance
        
    @property
    def dtype(self):
        return self._dtype_bytes.decode('ascii')
    @dtype.setter
    def dtype(self, value):
        self._dtype_bytes = value.encode('ascii')
        
        
class NLSTName(NLSTBase):
    def __init__(self):
        super().__init__()
        self.parent = -1
        self._dtype_bytes = b""
    
    def __repr__(self):
        return f"BoneName({self.name}, {self.parent}, {self.dtype})"
    
    @classmethod
    def create(cls, name, parent, dtype):
        instance = super().create(name)
        instance.parent = parent
        
        if type(dtype) is bytes: instance._dtype_bytes = dtype
        else:                    instance.dtype = dtype
        
        return instance
        
    @property
    def dtype(self):
        return self._dtype_bytes.decode('ascii')
    @dtype.setter
    def dtype(self, value):
        self._dtype_bytes = value.encode('ascii')
        
class NameList:
    def __init__(self):
        self.bone_names = []
        self.mesh_names = []

    def add_bone(self, name, parent, dtype):
        self.bone_names.append(NLSTBone.create(name, parent, dtype))
        
    def add_mesh(self, name):
        self.mesh_names.append(NLSTMesh.create(name))

    @classmethod
    def from_file(cls, filepath):
        binary = NameListBinary()
        binary.read(filepath)
        return cls.from_binary(binary)

    @classmethod
    def from_binary(cls, binary):
        elements = [line.split(b", ") for line in binary.lines]
        hash_to_linenumber = {e[1]: i for i, e in enumerate(elements) if e[3] != b"mesh"}
        hash_to_linenumber[b"null"] = -1
        
        instance = cls()
        for name, namehash, parenthash, dtype in elements:
            if dtype == b"mesh":
                if parenthash != b"null":
                    raise ValueError("Invalid parent for mesh: hash must be 'null'")
                instance.add_mesh(name)
            # elif dtype == b"joint" or dtype == b"geometry" or dtype == b"camera" or dtype==b"controller":
            else:
                instance.add_bone(name, hash_to_linenumber[parenthash], dtype)
        
        return instance
    
    def to_binary(self):
        binary = NameListBinary()
        bone_hex_formatter = "{:0>8x}"
        for bone in self.bone_names:
            binary.lines.append(b", ".join((
                bone._name_bytes, 
                bone_hex_formatter.format(dscs_hash(bone._name_bytes)).encode('ascii'), 
                bone_hex_formatter.format(dscs_hash(self.bone_names[bone.parent]._name_bytes)).encode('ascii') if bone.parent > -1 else b"null",
                bone._dtype_bytes
            )))
            
        mesh_hex_formatter = "{:x}"
        for mesh in self.mesh_names:
            binary.lines.append(b", ".join((
                mesh._name_bytes, 
                mesh_hex_formatter.format(dscs_hash(mesh._name_bytes)).encode('ascii'), 
                b"null",
                b"mesh"
            )))
        return binary
    
    def to_file(self, filepath):
        binary = self.to_binary()
        binary.write(filepath)
