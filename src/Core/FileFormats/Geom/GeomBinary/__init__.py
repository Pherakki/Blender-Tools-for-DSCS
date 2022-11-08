from ....serialization.Serializable import Serializable


class GeomBinary(Serializable):
    """
    A class to read and write geom files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section of mesh data.
        3. A section of material data.
        4. A section of texture filenames.
        5. A section of light source data.
        6. A section of camera data.
        7. A section of inverse bind pose matrices.
        8. An optional 1D texture.

    Completion status
    ------
    (o) GeomBinary can successfully parse all geom files in DSDB archive within current constraints.
    (o) GeomBinary can fully interpret all data in geom files in DSDB archive.
    (o) GeomBinary can write data to geom files.
    """

    def __init__(self):
        super().__init__()
        self.header = GeomHeader()


class GeomHeader(Serializable):
    def __init__(self):
        super().__init__()
        self.filetype              = 100
        self.mesh_count            = None
        self.material_count        = None
        self.light_source_count    = None
        self.camera_count          = None
        self.bone_count            = None

        self.texture_section_size  = None
        self.centre_point          = None
        self.bounding_box_diagonal = None
        self.padding_0x2C          = 0

        self.meshes_offset         = None
        self.materials_offset      = None

        self.light_sources_offset  = None
        self.cameras_offset        = None

        self.ibpms_offset          = None
        self.padding_0x58          = 0
        self.textures_offset       = None
        self.extra_clut_offset     = None

    def read_write(self, rw):
        rw.assert_local_file_pointer_now_at(0)

        self.filetype             = rw.rw_uint32(self.filetype)  # Always 100.
        rw.assert_equal(self.filetype, 100)
        self.mesh_count           = rw.rw_uint16(self.mesh_count)
        self.material_count       = rw.rw_uint16(self.material_count)
        self.light_source_count   = rw.rw_uint16(self.light_source_count)
        self.camera_count         = rw.rw_uint16(self.camera_count)
        self.bone_count           = rw.rw_uint32(self.bone_count)

        self.texture_section_size  = rw.rw_uint32(self.texture_section_size)
        self.centre_point          = rw.rw_float32s(self.centre_point, 3)

        self.bounding_box_diagonal = rw.rw_float32s(self.bounding_box_diagonal, 3)
        self.padding_0x3C          = rw.rw_uint32(self.padding_0x3C)
        rw.assert_is_zero(self.padding_0x3C)

        self.meshes_offset         = rw.rw_pointer(self.meshes_offset)
        self.materials_offset      = rw.rw_pointer(self.materials_offset)

        self.light_sources_offset  = rw.rw_pointer(self.light_sources_offset)
        self.cameras_offset        = rw.rw_pointer(self.cameras_offset)

        self.ibpms_offset          = rw.rw_pointer(self.ibpms_offset)
        self.padding_0x58          = rw.rw_pointer(self.padding_0x58)
        rw.assert_is_zero(self.padding_0x58)

        self.textures_offset       = rw.rw_pointer(self.textures_offset)
        self.extra_clut_offset     = rw.rw_pointer(self.extra_clut_offset)
