from ..BaseRW import BaseRW
from .MeshReader import MeshReader
from .MaterialReader import MaterialReader
import typing


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
    (o) GeomReader can write data to geom files.

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

        self.subreaders = [self.meshes, self.material_data, self.bone_data]

    def read(self):
        self.read_write(self.read_buffer, 'read', self.read_raw, self.prepare_read_op, self.cleanup_ragged_chunk_read)
        self.interpret_geom_data()

    def write(self):
        self.reinterpret_geom_data()
        self.read_write(self.write_buffer, 'write', self.write_raw, lambda: None, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_method_name, rw_operator_raw, preparation_op, chunk_cleanup_operator):
        self.rw_header(rw_operator)
        preparation_op()
        self.rw_meshes(rw_operator, rw_method_name)
        self.rw_material_data(rw_method_name)
        self.rw_texture_names(rw_operator_raw)
        self.rw_unknown_cam_data_1(rw_operator)
        self.rw_unknown_cam_data_2(rw_operator)
        chunk_cleanup_operator(self.bytestream.tell(), 16)
        self.rw_bone_data(rw_method_name)
        self.rw_footer_data(rw_operator_raw)

    def rw_header(self, rw_operator):
        """
        -> Only unknown values bytes 0x14-0x2B, assumed to be 6 floats.
        
        Returns
        -------
        None.

        """
        # Header
        self.assert_file_pointer_now_at(0)

        rw_operator('filetype', 'I')  # Always 100.
        self.assert_equal('filetype', 100)
        rw_operator('num_meshes', 'H')
        rw_operator('num_materials', 'H')
        rw_operator('num_unknown_cam_data_1', 'H')  # 0, 1, 2, 3, 4 ,5
        rw_operator('num_unknown_cam_data_2', 'H')  # 0, 1, 2, 3, 4, 9
        rw_operator('num_bones', 'I')

        rw_operator('num_bytes_in_texture_names_section', 'I')
        rw_operator('unknown_0x14', 'fff')  # Unknown: huge variation
        rw_operator('unknown_0x20', 'fff')  # Unknown: huge variation
        rw_operator('padding_0x2C', 'I')  # Always 0
        self.assert_is_zero('padding_0x2C')

        rw_operator('meshes_start_ptr', 'Q')
        rw_operator('materials_start_ptr', 'Q')
        rw_operator('unknown_cam_data_1_start_ptr', 'Q')
        rw_operator('unknown_cam_data_2_start_ptr', 'Q')

        rw_operator('bone_data_start_ptr', 'Q')
        rw_operator('padding_0x58', 'Q')
        self.assert_is_zero("padding_0x58")
        rw_operator('texture_names_start_ptr', 'Q')
        rw_operator('footer_data_start_offset', 'Q')

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

    def rw_meshes(self, rw_operator, rw_method_name):
        if self.is_ndef(self.meshes_start_ptr, 'num_meshes'):
            return
        self.assert_file_pointer_now_at(self.meshes_start_ptr)

        for meshReader in self.meshes:
            getattr(meshReader, f'{rw_method_name}_header')()
        for i, meshReader in enumerate(self.meshes):
            getattr(meshReader, rw_method_name)()

    def rw_material_data(self, rw_method_name):
        if self.is_ndef(self.materials_start_ptr, 'num_materials'):
            return
        self.assert_file_pointer_now_at(self.materials_start_ptr)

        for materialReader in self.material_data:
            getattr(materialReader, rw_method_name)()

    def rw_texture_names(self, rw_operator_raw):
        if self.is_ndef(self.texture_names_start_ptr, 'num_bytes_in_texture_names_section'):
            return
        self.assert_file_pointer_now_at(self.texture_names_start_ptr)

        rw_operator_raw('texture_data', self.num_bytes_in_texture_names_section)

    def rw_unknown_cam_data_1(self, rw_operator):
        if self.is_ndef(self.unknown_cam_data_1_start_ptr, 'num_unknown_cam_data_1'):
            return
        self.assert_file_pointer_now_at(self.unknown_cam_data_1_start_ptr)

        # clearly some structural alignment between (14, 15) and (16, 17)
        # 15 looks like a count, as does 17... everything past this is 0
        # 64 bytes per unknown_cam_data_1
        rw_operator('unknown_cam_data_1', 'hhhhhhhhffffHHHHHHHHHHHHHHHH'*self.num_unknown_cam_data_1)
        #for _ in range(self.num_unknown_cam_data_1):
        #    read_bytes = self.bytestream.read(64)
        #    data = read_bytes  # struct.unpack('hhhhhhhhffffHHHHHHHHHHHHHHHH', read_bytes)
        #    # clearly some structural alignment between (14, 15) and (16, 17)
        #    # 15 looks like a count, as does 17... everything past this is 0
        #    self.unknown_cam_data_1.append(data)

    def rw_unknown_cam_data_2(self, rw_operator):
        if self.is_ndef(self.unknown_cam_data_2_start_ptr, 'num_unknown_cam_data_2'):
            return
        self.assert_file_pointer_now_at(self.unknown_cam_data_2_start_ptr)

        # 48 bytes per unknown_cam_data_2
        rw_operator('unknown_cam_data_2', 'HHHHHHHHhhhhHHHHHHHHHHHH'*self.num_unknown_cam_data_2)
        #for _ in range(self.num_unknown_cam_data_2):
        #    read_bytes = self.bytestream.read(48)
        #    data = read_bytes  # struct.unpack('HHHHHHHHhhhhHHHHHHHHHHHH', read_bytes)
        #    # 12 is 0 or 1, everything after is 0
        #    self.unknown_cam_data_2.append(data)

    def rw_bone_data(self, rw_method_name):
        if self.is_ndef(self.bone_data_start_ptr, 'num_bones'):
            return
        self.assert_file_pointer_now_at(self.bone_data_start_ptr)

        for boneReader in self.bone_data:
            getattr(boneReader, rw_method_name)()

    def rw_footer_data(self, rw_operator_raw):
        if self.footer_data_start_offset == 0:
            rw_operator_raw('unknown_footer_data')
            assert len(self.unknown_footer_data) == 0, \
                f"File assumed complete, {len(self.unknown_footer_data)} bytes left to go"
            return
        self.assert_file_pointer_now_at(self.footer_data_start_offset)
        rw_operator_raw('unknown_footer_data')
        # This data appears to be 16 (potentially useful?) bytes followed by every byte value repeated x4,
        # then 12 \x00 bytes

    def prepare_read_op(self):
        self.meshes = [MeshReader(self.bytestream) for _ in range(self.num_meshes)]
        self.material_data = [MaterialReader(self.bytestream) for _ in range(self.num_materials)]
        self.bone_data = [BoneDataReader(self.bytestream) for _ in range(self.num_bones)]

    def interpret_geom_data(self):
        texture_data = self.chunk_list(self.texture_data, 32)
        self.texture_data = [datum.rstrip(self.pad_byte).decode('ascii') for datum in texture_data]
        self.unknown_cam_data_1 = self.chunk_list(self.unknown_cam_data_1, 28)
        self.unknown_cam_data_2 = self.chunk_list(self.unknown_cam_data_2, 24)

    def reinterpret_geom_data(self):
        self.texture_data: typing.List[str]

        for texture_name in self.texture_data:
            assert len(texture_name) < 32, f"Texture name {texture_name} is longer than 32 characters; please shorten the filename."
        texture_data = [texture_name.encode('ascii') + self.pad_byte * (32 - len(texture_name))
                        for texture_name in self.texture_data]
        self.texture_data = b''.join(texture_data)
        self.unknown_cam_data_1 = self.flatten_list(self.unknown_cam_data_1)
        self.unknown_cam_data_2 = self.flatten_list(self.unknown_cam_data_2)


class BoneDataReader(BaseRW):
    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.x_axis = None
        self.xpos = None
        self.y_axis = None
        self.ypos = None
        self.z_axis = None
        self.zpos = None

    def read(self):
        self.rw_header(self.read_buffer)

    def write(self):
        self.rw_header(self.write_buffer)

    def rw_header(self, rw_operator):
        # (3D unit vector, value) * 3
        # 1st is principally in x, 2nd principally in y, 3rd principally in z...?
        rw_operator('x_axis', 'fff')
        rw_operator('xpos', 'f')

        rw_operator('y_axis', 'fff')
        rw_operator('ypos', 'f')

        rw_operator('z_axis', 'fff')
        rw_operator('zpos', 'f')
