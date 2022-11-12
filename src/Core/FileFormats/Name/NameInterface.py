from .NameBinary import NameBinary


class NameInterface:
    def __init__(self):
        self.bone_names = []
        self.material_names = []

    @classmethod
    def from_file(cls, filepath):
        nf = NameBinary()
        nf.read(filepath)

        instance = cls()
        instance.bone_names = nf.bone_names
        instance.material_names = nf.material_names

        return instance

    def to_file(self, filepath):
        nf = NameBinary()
        nf.bone_name_count = len(self.bone_names)
        nf.material_name_count = len(self.material_names)
        nf.bone_names = self.bone_names
        nf.material_names = self.material_names

        # Manually calculate pointers
        nf.pointers = [None] * (nf.bone_name_count + nf.material_name_count)
        offset = (nf.bone_name_count + nf.material_name_count)*4 + 8
        for i in range(nf.bone_name_count):
            nf.pointers[i] = offset
            offset += len(nf.bone_names[i])
        for i in range(nf.material_name_count):
            nf.pointers[nf.bone_name_count + i] = offset
            offset += len(nf.material_names[i])
        nf.write(filepath)
