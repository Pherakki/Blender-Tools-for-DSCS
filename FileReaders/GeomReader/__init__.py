import enum
import struct
from ..BaseRW import BaseRW
from .MeshReader import MeshReader
from .MaterialReader import MaterialReader


class GeomReader(BaseRW):
    """
    A class to read geom files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section that describes the geometry of each mesh.
        3. A section that describes each defined material.
        4. A section of file names for texture images.
        5. A section of unknown data that appears in CAM-type files, amongst others.
        6. Another section of unknown data that appears in CAM-type files, amongst others.
        7. A section of bone data which includes bone positions.
        8. A section of unknown data that appears to be largely filler.

    Completion status
    ------
    (o) GeomReader can successfully parse all geom files in DSDB archive within current constraints.
    (x) GeomReader cannot yet fully interpret all data in geom files in DSDB archive.
    (x) GeomReader cannot yet write data to geom files.

    Current hypotheses and observations
    ------
    1. unknown_footer_data generally seems to contain every byte value repeated four times with some preceding padding
        bytes plus some (potentially information-carrying) bytes.
    """

    def __init__(self, io_stream):
        super().__init__(io_stream)
        # Header variables
        self.filetype = None
        self.num_meshes = None
        self.num_materials = None
        self.num_unknown_cam_data_1 = None
        self.num_unknown_cam_data_2 = None
        self.num_bones = None

        self.num_bytes_in_texture_names_section = None
        self.unknown_0x14 = None
        self.unknown_0x20 = None
        self.padding_0x2C = None

        self.meshes_start_ptr = None
        self.materials_start_ptr = None

        self.unknown_cam_data_1_start_ptr = None
        self.unknown_cam_data_2_start_ptr = None

        self.bone_data_start_ptr = None
        self.padding_0x58 = None
        self.texture_names_start_ptr = None
        self.footer_data_start_offset = None

        # Data storage variables
        self.meshes = []
        self.material_data = []
        self.texture_data = []
        self.unknown_cam_data_1 = []
        self.unknown_cam_data_2 = []
        self.bone_data = []
        self.unknown_footer_data = []

        # Utility variables
        self.filesize = None

    def read(self):
        self.read_header()
        self.read_meshes()
        self.read_material_data()
        self.read_texture_names()
        self.read_unknown_cam_data_1()
        self.read_unknown_cam_data_2()
        self.cleanup_ragged_chunk(self.bytestream.tell(), 16)
        self.read_bone_data()
        self.read_footer_data()

    def read_header(self):
        """
        -> Only unknown values bytes 0x14-0x2B, assumed to be 6 floats.
        
        Returns
        -------
        None.

        """
        # Header
        self.assert_file_pointer_now_at(0)

        self.bytestream.seek(0, 2)
        self.filesize = self.bytestream.tell()
        self.bytestream.seek(0)
        self.assert_file_pointer_now_at(0)

        self.filetype = self.unpack('I')  # Always 100.
        self.assert_equal('filetype', 100)
        self.num_meshes = self.unpack('H')
        self.num_materials = self.unpack('H')
        self.num_unknown_cam_data_1 = self.unpack('H')  # 0, 1, 2, 3, 4 ,5
        self.num_unknown_cam_data_2 = self.unpack('H')  # 0, 1, 2, 3, 4, 9
        self.num_bones = self.unpack('I')

        self.num_bytes_in_texture_names_section = self.unpack('I')
        self.unknown_0x14 = self.unpack('fff')  # Unknown: huge variation
        self.unknown_0x20 = self.unpack('fff')  # Unknown: huge variation
        self.padding_0x2C = self.unpack('I')  # Always 0
        self.assert_is_zero('padding_0x2C')

        self.meshes_start_ptr = self.unpack('Q')
        self.materials_start_ptr = self.unpack('Q')
        self.unknown_cam_data_1_start_ptr = self.unpack('Q')
        self.unknown_cam_data_2_start_ptr = self.unpack('Q')

        self.bone_data_start_ptr = self.unpack('Q')
        self.padding_0x58 = self.unpack('Q')
        self.assert_is_zero("padding_0x58")
        self.texture_names_start_ptr = self.unpack('Q')
        self.footer_data_start_offset = self.unpack('Q')

    def is_ndef(self, offset, numValues):
        """
        A utility function that checks whether a file pointer is 0, and if it is, also checks if the associated count
        is 0. Used to skip sections that have 0 size in the file.

        Arguments
        ------
        offset -- a file pointer
        numValues -- the count of values associated with the file pointer

        Returns
        ------
        True if the file pointer is 0
        False if not
        """
        if offset == 0:
            self.assert_is_zero(numValues)
            return True
        return False

    def read_meshes(self):
        if self.is_ndef(self.meshes_start_ptr, 'num_meshes'):
            return
        self.assert_file_pointer_now_at(self.meshes_start_ptr)

        for _ in range(self.num_meshes):
            self.meshes.append(MeshReader(self.bytestream))
            self.meshes[-1].read_header()
        for i, meshReader in enumerate(self.meshes):
            self.assert_file_pointer_now_at(meshReader.vertex_data_start_ptr)
            meshReader.read_vertices()
            meshReader.read_weighted_bone_indices()
            meshReader.read_polygons()
            meshReader.read_vertex_components()
            meshReader.interpret_vertices()

    def read_material_data(self):
        if self.is_ndef(self.materials_start_ptr, 'num_materials'):
            return
        self.assert_file_pointer_now_at(self.materials_start_ptr)

        for _ in range(self.num_materials):
            materialReader = MaterialReader(self.bytestream)
            materialReader.read_header()
            materialReader.read_material_components()
            materialReader.read_unknown_data()

            self.material_data.append(materialReader)

    def read_texture_names(self):
        if self.is_ndef(self.texture_names_start_ptr, 'num_bytes_in_texture_names_section'):
            return
        self.assert_file_pointer_now_at(self.texture_names_start_ptr)

        texture_data = self.bytestream.read(self.num_bytes_in_texture_names_section)
        texture_data = self.chunk_list(texture_data, 32)
        self.texture_data = [datum.rstrip(self.pad_byte).decode('ascii') for datum in texture_data]

    def read_unknown_cam_data_1(self):
        if self.is_ndef(self.unknown_cam_data_1_start_ptr, 'num_unknown_cam_data_1'):
            return
        self.assert_file_pointer_now_at(self.unknown_cam_data_1_start_ptr)

        for _ in range(self.num_unknown_cam_data_1):
            read_bytes = self.bytestream.read(64)
            data = read_bytes  # struct.unpack('hhhhhhhhffffHHHHHHHHHHHHHHHH', read_bytes)
            # clearly some structural alignment between (14, 15) and (16, 17)
            # 15 looks like a count, as does 17... everything past this is 0
            self.unknown_cam_data_1.append(data)

    def read_unknown_cam_data_2(self):
        if self.is_ndef(self.unknown_cam_data_2_start_ptr, 'num_unknown_cam_data_2'):
            return
        self.assert_file_pointer_now_at(self.unknown_cam_data_2_start_ptr)

        for _ in range(self.num_unknown_cam_data_2):
            read_bytes = self.bytestream.read(48)
            data = read_bytes  # struct.unpack('HHHHHHHHhhhhHHHHHHHHHHHH', read_bytes)
            # 12 is 0 or 1, everything after is 0
            self.unknown_cam_data_2.append(data)

    def read_bone_data(self):
        if self.is_ndef(self.bone_data_start_ptr, 'num_bones'):
            return
        self.assert_file_pointer_now_at(self.bone_data_start_ptr)

        for _ in range(self.num_bones):
            self.bone_data.append(BoneDataReader(self.bytestream))
            self.bone_data[-1].read_header()

    def read_footer_data(self):
        if self.footer_data_start_offset == 0:
            assert self.filesize - self.bytestream.tell() == 0, f"File assumed complete, {self.filesize - self.bytestream.tell()} bytes left to go"
            return
        self.assert_file_pointer_now_at(self.footer_data_start_offset)
        self.unknown_footer_data = self.bytestream.read()
        # This data appears to be 16 (potentially useful?) bytes followed by every byte value repeated x4,
        # then 12 \x00 bytes


class BoneDataReader(BaseRW):
    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.unknown_0x00 = None
        self.unknown_0x04 = None
        self.unknown_0x08 = None
        self.xpos = None

        self.unknown_0x0C = None
        self.unknown_0x10 = None
        self.unknown_0x14 = None
        self.ypos = None

        self.unknown_0x18 = None
        self.unknown_0x1C = None
        self.unknown_0x20 = None
        self.zpos = None

    def read_header(self):
        # (3D unit vector, value) * 3
        # 1st is principally in x, 2nd principally in y, 3rd principally in z...?
        self.unknown_0x00 = self.unpack('f')
        self.unknown_0x04 = self.unpack('f')
        self.unknown_0x08 = self.unpack('f')
        self.xpos = self.unpack('f')

        self.unknown_0x0C = self.unpack('f')
        self.unknown_0x10 = self.unpack('f')
        self.unknown_0x14 = self.unpack('f')
        self.ypos = self.unpack('f')

        self.unknown_0x18 = self.unpack('f')
        self.unknown_0x1C = self.unpack('f')
        self.unknown_0x20 = self.unpack('f')
        self.zpos = self.unpack('f')
