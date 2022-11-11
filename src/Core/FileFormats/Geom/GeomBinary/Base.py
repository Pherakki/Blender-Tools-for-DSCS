from ....serialization.Serializable import Serializable
from .MaterialBinary import MaterialBinary
from .LightBinary import LightBinary
from .CameraBinary import CameraBinary


class GeomBinaryBase(Serializable):
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

    @property
    def MESH_TYPE(self):
        raise NotImplementedError("MESH_TYPE not implemented on Subclass")

    @property
    def _CLASSTAG(self):
        raise NotImplementedError("_CLASSTAG not implemented on Subclass")

    def __init__(self):
        super().__init__()
        self.filetype              = 100
        self.mesh_count            = None
        self.material_count        = None
        self.light_source_count    = None
        self.camera_count          = None
        self.ibpm_count            = None

        self.texture_section_size  = None
        self.centre_point          = None
        self.bounding_box_diagonal = None
        self.padding_0x3C          = 0

        self.meshes_offset         = None
        self.materials_offset      = None

        self.light_sources_offset  = None
        self.cameras_offset        = None

        self.ibpms_offset          = None
        self.padding_0x58          = 0
        self.textures_offset       = None
        self.extra_clut_offset     = None

        # Data Holders
        self.meshes    = []
        self.materials = []
        self.textures  = []
        self.lights    = []
        self.cameras   = []
        self.ibpms     = []
        self.extra_clut = None

    def __repr__(self):
        return f"[{self._CLASSTAG}] " \
            f"Meshes: {self.mesh_count}/{self.meshes_offset} " \
            f"Materials: {self.material_count}/{self.materials_offset}" \
            f"Lights: {self.light_source_count}/{self.light_sources_offset}" \
            f"Cameras: {self.camera_count}/{self.cameras_offset}" \
            f"IBPMs: {self.ibpm_count}/{self.ibpms_offset}" \
            f"Textures: {self.texture_section_size}/{self.textures_offset}" \
            f"CLUT: {self.extra_clut_offset}" \
            f"Geometry: {self.centre_point} {self.bounding_box_diagonal}"

    def read_write(self, rw):
        self.rw_header(rw)
        self.rw_meshes(rw)
        self.rw_materials(rw)
        self.rw_textures(rw)
        self.rw_lights(rw)
        self.rw_cameras(rw)
        rw.align(rw.local_tell(), 0x10)
        self.rw_ibpms(rw)
        self.rw_extra_clut(rw)
        rw.assert_at_eof()

    def rw_header(self, rw):
        rw.assert_local_file_pointer_now_at("File Start", 0)

        self.filetype              = rw.rw_uint32(self.filetype)  # Always 100.
        rw.assert_equal(self.filetype, 100)
        self.mesh_count            = rw.rw_uint16(self.mesh_count)
        self.material_count        = rw.rw_uint16(self.material_count)
        self.light_source_count    = rw.rw_uint16(self.light_source_count)
        self.camera_count          = rw.rw_uint16(self.camera_count)
        self.ibpm_count            = rw.rw_uint32(self.ibpm_count)

        self.texture_section_size  = rw.rw_uint32(self.texture_section_size)
        self.centre_point          = rw.rw_float32s(self.centre_point, 3)

        self.bounding_box_diagonal = rw.rw_float32s(self.bounding_box_diagonal, 3)
        self.padding_0x3C          = rw.rw_uint32(self.padding_0x3C)
        rw.assert_is_zero(self.padding_0x3C)

        self.meshes_offset         = rw.rw_uint64(self.meshes_offset)
        self.materials_offset      = rw.rw_uint64(self.materials_offset)

        self.light_sources_offset  = rw.rw_uint64(self.light_sources_offset)
        self.cameras_offset        = rw.rw_uint64(self.cameras_offset)

        self.ibpms_offset          = rw.rw_uint64(self.ibpms_offset)
        self.padding_0x58          = rw.rw_uint64(self.padding_0x58)
        rw.assert_is_zero(self.padding_0x58)

        self.textures_offset       = rw.rw_uint64(self.textures_offset)
        self.extra_clut_offset     = rw.rw_uint64(self.extra_clut_offset)

    def rw_meshes(self, rw):
        if self.meshes_offset:
            rw.assert_local_file_pointer_now_at("Meshes", self.meshes_offset)
            self.meshes = rw.rw_obj_array(self.meshes, self.MESH_TYPE, self.mesh_count)
            for mesh in self.meshes:
                rw.rw_obj_method(mesh, mesh.rw_contents)

    def rw_materials(self, rw):
        if self.materials_offset:
            rw.assert_local_file_pointer_now_at("Materials", self.materials_offset)
            self.materials = rw.rw_obj_array(self.materials, MaterialBinary, self.material_count)

    def rw_textures(self, rw):
        if self.textures_offset:
            rw.assert_local_file_pointer_now_at("Textures", self.textures_offset)
            self.textures = rw.rw_bytestrings(self.textures, 0x20, self.texture_section_size // 0x20)

    def rw_lights(self, rw):
        if self.light_sources_offset:
            rw.assert_local_file_pointer_now_at("Lights", self.light_sources_offset)
            self.lights = rw.rw_obj_array(self.lights, LightBinary, self.light_source_count)

    def rw_cameras(self, rw):
        if self.cameras_offset:
            rw.assert_local_file_pointer_now_at("Lights", self.cameras_offset)
            self.cameras = rw.rw_obj_array(self.cameras, CameraBinary, self.camera_count)

    def rw_ibpms(self, rw):
        if self.ibpms_offset:
            rw.assert_local_file_pointer_now_at("IBPMs", self.ibpms_offset)
            self.ibpms = rw.rw_float32s(self.ibpms, (self.ibpm_count, 12))

    def rw_extra_clut(self, rw):
        if self.extra_clut_offset:
            rw.assert_local_file_pointer_now_at("Extra CLUT", self.extra_clut_offset)
            self.extra_clut = rw.rw_unbounded_bytestring(self.extra_clut)
