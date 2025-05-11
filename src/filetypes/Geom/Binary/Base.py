from ....serialization.DSCSStructs import DSCSSerializable
from ....serialization.DSCSFormatters   import HEX32_formatter
from ....serialization import OffsetMarker
from .Material import MaterialBinary
from .Light import LightBinary
from .Camera import CameraBinary


class GeomBinaryBase(DSCSSerializable):
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
        self.light_count           = None
        self.camera_count          = None
        self.ibpm_count            = None

        self.texture_section_size  = None
        self.centre_point          = None
        self.bounding_box_diagonal = None
        self.padding_0x3C          = 0

        self.meshes_offset         = None
        self.materials_offset      = None

        self.lights_offset         = None
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
        self.extra_clut = b''
        
        self.meshes_marker    = OffsetMarker().subscribe(self, "meshes_offset")
        self.materials_marker = OffsetMarker().subscribe(self, "materials_offset")
        self.textures_marker  = OffsetMarker().subscribe(self, "textures_offset")
        self.lights_marker    = OffsetMarker().subscribe(self, "lights_offset")
        self.cameras_marker   = OffsetMarker().subscribe(self, "cameras_offset")
        self.ibpms_marker     = OffsetMarker().subscribe(self, "ibpms_offset")
        self.clut_marker      = OffsetMarker().subscribe(self, "extra_clut_offset")
        

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

    def exbip_rw(self, rw):
        # self.rw_header(rw)
        # self.rw_meshes(rw)
        # self.rw_materials(rw)
        # self.rw_textures(rw)
        # self.rw_lights(rw)
        # self.rw_cameras(rw)
        # rw.align(rw.local_tell(), 0x10)
        # self.rw_ibpms(rw)
        # self.rw_extra_clut(rw)
        # rw.assert_at_eof()

        self.filetype              = rw.rw_uint32(self.filetype)  # Always 100.
        rw.assert_equal(self.filetype, 100)
        self.mesh_count            = rw.rw_uint16(self.mesh_count)
        self.material_count        = rw.rw_uint16(self.material_count)
        self.light_count           = rw.rw_uint16(self.light_count)
        self.camera_count          = rw.rw_uint16(self.camera_count)
        self.ibpm_count            = rw.rw_uint32(self.ibpm_count)

        self.texture_section_size  = rw.rw_uint32(self.texture_section_size)
        self.centre_point          = rw.rw_float32s(self.centre_point, 3)

        self.bounding_box_diagonal = rw.rw_float32s(self.bounding_box_diagonal, 3)
        self.padding_0x3C          = rw.rw_uint32(self.padding_0x3C)
        rw.assert_equal(self.padding_0x3C, 0)

        self.meshes_offset         = rw.rw_uint64(self.meshes_offset)
        self.materials_offset      = rw.rw_uint64(self.materials_offset)

        self.lights_offset         = rw.rw_uint64(self.lights_offset)
        self.cameras_offset        = rw.rw_uint64(self.cameras_offset)

        self.ibpms_offset          = rw.rw_uint64(self.ibpms_offset)
        self.padding_0x58          = rw.rw_uint64(self.padding_0x58)
        rw.assert_equal(self.padding_0x58, 0)

        self.textures_offset       = rw.rw_uint64(self.textures_offset)
        self.extra_clut_offset     = rw.rw_uint64(self.extra_clut_offset)

        # Meshes
        if rw.section_exists(self.meshes_offset, self.mesh_count):
            rw.verify_stream_offset(self.meshes_offset, "Meshes", HEX32_formatter, self.meshes_marker)
            self.meshes = rw.rw_dynamic_objs(self.meshes, self.MESH_TYPE, self.mesh_count)
            for mesh in self.meshes:
                mesh.rw_contents(rw)
        
        # Materials
        if rw.section_exists(self.materials_offset, self.material_count):
            rw.verify_stream_offset(self.materials_offset, "Materials", HEX32_formatter, self.materials_marker)
            self.materials = rw.rw_dynamic_objs(self.materials, MaterialBinary, self.material_count)

        # Textures
        if rw.section_exists(self.textures_offset, self.texture_section_size):
            rw.verify_stream_offset(self.textures_offset, "Textures", HEX32_formatter, self.textures_marker)
            self.textures = rw.rw_bytestrings(self.textures, (0x20 for _ in range (self.texture_section_size // 0x20)))
        
        # Lights
        if rw.section_exists(self.lights_offset, self.light_count):
            rw.verify_stream_offset(self.lights_offset, "Lights", HEX32_formatter, self.lights_marker)
            self.lights = rw.rw_dynamic_objs(self.lights, LightBinary, self.light_count)
            
        # Cameras
        if rw.section_exists(self.cameras_offset, self.camera_count):
            rw.verify_stream_offset(self.cameras_offset, "Cameras", HEX32_formatter, self.cameras_marker)
            self.cameras = rw.rw_dynamic_objs(self.cameras, CameraBinary, self.camera_count)
            
        rw.align(rw.tell(), 0x10)

        # IBPMs
        if rw.section_exists(self.ibpms_offset, self.ibpm_count):
            rw.verify_stream_offset(self.ibpms_offset, "IBPMs", HEX32_formatter, self.ibpms_marker)
            self.ibpms = rw.rw_float32s(self.ibpms, (self.ibpm_count, 12))

        # Extra CLUT
        if rw.section_exists(self.extra_clut_offset, len(self.extra_clut)):
            rw.verify_stream_offset(self.extra_clut_offset, "Extra CLUT", HEX32_formatter, self.clut_marker)
            self.extra_clut = rw.rw_bytestring(self.extra_clut, 1052)
            assert len(self.extra_clut) == 1052, len(self.extra_clut)
        
        rw.assert_eof()
