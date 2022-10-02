from ...serialization.Serializable import Serializable


class NameFile(Serializable):
    """
    A class to read name files. These files are split into three main sections:
        1. Two integers that state how many bone names and material names are contained within the file.
        2. A section of file pointers, one per bone name and one per material name.
        3. A continuous string of ascii characters that, when split at the locations given by the file pointers,
           resolves to bone names and material names.

    Completion status
    ------
    (o) NameFile can successfully parse all name files in DSDB archive within current constraints.
    (o) NameFile can fully interpret all data in name files in DSDB archive.
    (o) NameFile can write data to name files.
    """
    def __init__(self):
        super().__init__()

        self.bone_name_count = None
        self.material_name_count = None
        self.pointers = []

        self.bone_names = []
        self.material_names = []

    def read_write(self, rw):
        self.rw_header(rw)
        self.rw_names(rw)

    def rw_header(self, rw):
        rw.assert_file_pointer_now_at(0)
        self.bone_name_count     = rw.rw_uint32(self.bone_name_count)
        self.material_name_count = rw.rw_uint32(self.material_name_count)
        self.pointers            = rw.rw_uint32s(self.pointers, self.bone_name_count + self.material_name_count)

    def rw_names(self, rw):
        if len(self.pointers):
            # Check we're in the right place, init the variable holders if necessary
            rw.assert_file_pointer_now_at(self.pointers[0])
            if rw.mode() == "read":
                self.bone_names     = [None for _ in range(self.bone_name_count)]
                self.material_names = [None for _ in range(self.material_name_count)]

            # Calculate how big each string we're going to read/write is
            sizes = [None for _ in range(len(self.pointers) + 1)]
            for i, (p1, p2) in enumerate(zip(self.pointers, self.pointers[1:])):
                sizes[i] = p2 - p1

            # Calculate the length of the final string
            if rw.mode() == "read":
                curpos = rw.tell()
                rw.seek(0, 2) # Seek to EOF
                remaining_size = rw.tell() - curpos
                rw.seek(curpos, 0) # Seek back to start
                sizes[-1] = remaining_size
            else:
                if len(self.material_names):
                    sizes[-1] = len(self.material_names[-1])
                elif len(self.bone_names):
                    sizes[-1] = len(self.bone_names[-1])

            # Now read/write as appropriate
            sizes = iter(sizes)
            for i in range(self.bone_name_count):
                self.bone_names[i] = rw.rw_str(self.bone_names[i], next(sizes))
            for i in range(self.material_name_count):
                self.material_names[i] = rw.rw_str(self.material_names[i], next(sizes))
