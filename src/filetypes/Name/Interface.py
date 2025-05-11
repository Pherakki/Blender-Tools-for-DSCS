from .Binary import NameFileBinary


class NameFile:
    def __init__(self):
        self.bone_names     = []
        self.material_names = []

    @classmethod
    def from_file(cls, filepath):
        nf = NameFileBinary()
        nf.read(filepath)
        return cls.from_binary(nf)

    @classmethod
    def from_binary(cls, nb):
        instance = cls()
        instance.bone_names     = nb.names[0:nb.bone_name_count]
        instance.material_names = nb.names[nb.bone_name_count:]

        return instance

    def to_file(self, filepath):
        nf = self.to_binary()
        nf.write(filepath)

    def to_binary(self):
        nb = NameFileBinary()
        nb.bone_name_count     = len(self.bone_names)
        nb.material_name_count = len(self.material_names)
        nb.names = [*self.bone_names, *self.material_names]

        nb.calculate_offsets()
        
        return nb
