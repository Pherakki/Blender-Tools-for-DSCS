import struct

from ....serialization.Serializable import Serializable


class MaterialBinary(Serializable):
    """
    A class to read material data within geom files. These files are split into three main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section of shader uniforms and their values.
        3. A section containing codes for OpenGL functions and the data to pass into them.

    Completion status
    ------
    (o) MaterialReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (0) MaterialReader can fully interpret all material data in geom files in DSDB archive.
    (o) MaterialReader can write data to geom files.

    """

    def __init__(self):
        super().__init__()

        # Header variables
        self.name_hash            = None
        self.shader_hex           = None
        self.shader_uniform_count = None
        self.opengl_setting_count = None
        self.flags                = None

        # Data variables
        self.shader_uniforms = []
        self.opengl_settings = []

    def read_write(self, rw):
        self.name_hash            = rw.rw_uint32(self.name_hash)
        self.shader_hex           = rw.rw_uint32s(self.shader_hex, 4)
        self.shader_uniform_count = rw.rw_uint8(self.shader_uniform_count)
        self.opengl_setting_count = rw.rw_uint8(self.opengl_setting_count)
        self.flags                = rw.rw_uint16(self.flags)

        # Material flags:
        # 0x01 - ???
        # 0x02 - Enables shadows
        # 0x04 - ???
        # 0x08 - ???
        # 0x10 - ???
        # 0x20 - ???
        # 0x40 - ???
        # 0x80 - ???

        self.shader_uniforms = rw.rw_obj_array(self.shader_uniforms, ShaderUniform, self.shader_uniform_count)
        self.opengl_settings = rw.rw_obj_array(self.opengl_settings, OpenGLSetting, self.opengl_setting_count)


class ShaderUniform(Serializable):
    def __init__(self):
        super().__init__()
        self.payload = None
        self.index = None
        self.float_count = None
        self.unknown_0x12 = 0xFF00
        self.padding_0x14 = 0x00000000

    def read_write(self, rw):
        self.payload      = rw.rw_bytestring(self.payload, 0x10)
        self.index        = rw.rw_uint8(self.index)
        self.float_count  = rw.rw_uint8(self.float_count)
        self.unknown_0x12 = rw.rw_uint16(self.unknown_0x12)
        self.padding_0x14 = rw.rw_uint32(self.padding_0x14)

    def unpack(self):
        if self.float_count == 0:
            return struct.unpack('IIII', self.payload)
        else:
            return struct.unpack('ffff', self.payload)[:self.float_count]

    def pack(self, value):
        if self.float_count == 0:
            return struct.pack('IIII', *value)
        else:
            return struct.pack('ffff', [*value, *[0]*(4-len(value))])


class OpenGLSetting(Serializable):
    def __init__(self):
        super().__init__()
        self.payload = None
        self.index = None
        self.unknown_0x11 = 0x64
        self.unknown_0x12 = 0x00FF
        self.padding_0x14 = 0x00000000

    def read_write(self, rw):
        self.payload      = rw.rw_bytestring(self.payload, 0x10)
        self.index        = rw.rw_uint8(self.index)
        self.unknown_0x11 = rw.rw_uint8(self.unknown_0x11)
        self.unknown_0x12 = rw.rw_uint16(self.unknown_0x12)
        self.padding_0x14 = rw.rw_uint32(self.padding_0x14)

    def unpack(self):
        return struct.unpack(OPENGL_SETTING_SIGNATURES[self.index], self.payload)

    def pack(self, value):
        return struct.pack(OPENGL_SETTING_SIGNATURES[self.index], *value)


OPENGL_SETTING_SIGNATURES = {
    0xA0: 'Ifff',
    0xA1: 'IIII',
    0xA2: 'IIII',
    0xA3: 'IIII',
    0xA4: 'IIII',
    0xA6: 'IIII',
    0xA7: 'IIII',
    0xA8: 'IIII',
    0xA9: 'IIII',
    0xAA: 'ffII',
    0xAB: 'IIII',
    0xAC: 'IIII',
    0xAD: 'IiII',
    0xAE: 'IIII',
    0xAF: 'IIII',
    0xB0: 'IIII',
    0xB1: 'IIII',
    0xB2: 'IIII'
}
