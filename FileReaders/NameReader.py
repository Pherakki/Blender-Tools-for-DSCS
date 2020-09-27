from .BaseRW import BaseRW


class NameReader(BaseRW):
    """
    A class to read name files. These files are split into three main sections:
        1. Two integers that state how many bone names and material names are contained within the file.
        2. A section of file pointers, one per bone name and one per material name.
        3. A continuous string of ascii characters that, when split at the locations given by the file pointers,
           resolves to bone names and material names.

    Completion status
    ------
    (o) NameReader can successfully parse all name files in DSDB archive within current constraints.
    (o) NameReader can fully interpret all data in name files in DSDB archive.
    (x) NameReader cannot yet write data to name files.
    """
    def __init__(self, bytestream):
        super().__init__(bytestream)

        self.num_bone_names = None
        self.num_material_names = None
        self.bone_name_pointers = None
        self.bone_names = None
        self.material_name_pointers = None
        self.material_names = None

    def read(self):
        """
        Reads and decodes the name file.
        """
        self.read_header()
        self.read_pointers()
        self.read_bone_names()
        self.read_material_names()
        
    def read_header(self):
        self.assert_file_pointer_now_at(0)

        self.num_bone_names = self.unpack('I')
        self.num_material_names = self.unpack('I')
        
    def read_pointers(self):
        self.bone_name_pointers = self.unpack('I'*self.num_bone_names, force_1d=True)
        self.material_name_pointers = self.unpack('I'*self.num_material_names, force_1d=True)

    # There is probably a cleaner way of reading the bone names in.
    # This works for the moment though! May need revisiting for the write method.
    def split_string_by_ptrs(self, ascii_string, ptrs):
        # Split up the ascii-string into its constituent components.
        # The file pointers point to the start of each sub-string.
        retval = []
        for st, ed in zip(ptrs[:-1], ptrs[1:]):
            # The file pointers are absolute locations, so we need to translate them to be relative to the start of the
            # byte-string.
            rel_st = st - ptrs[0]
            rel_ed = ed - ptrs[0]
            stringslice = ascii_string[rel_st:rel_ed]
            retval.append(stringslice)
        # The for loop will miss off the final sub-string because the file pointers just point to the starts of the
        # strings, so read it now
        ed = ptrs[-1] - ptrs[0]
        retval.append(ascii_string[ed:])

        return retval

    def read_bone_names(self):
        if len(self.bone_name_pointers) == 0:
            self.bone_names = []
            return
        self.assert_file_pointer_now_at(self.bone_name_pointers[0])
        if len(self.material_name_pointers) == 0:
            bone_data = self.bytestream.read().decode('ascii')
        else:
            bytes_to_read = self.material_name_pointers[0] - self.bytestream.tell()
            bone_data = self.bytestream.read(bytes_to_read).decode('ascii')

        self.bone_names = self.split_string_by_ptrs(bone_data, self.bone_name_pointers)

    def read_material_names(self):
        if len(self.material_name_pointers) == 0:
            self.material_names = []
            return
        self.assert_file_pointer_now_at(self.material_name_pointers[0])
        material_data = self.bytestream.read().decode('ascii')

        self.material_names = self.split_string_by_ptrs(material_data, self.material_name_pointers)
