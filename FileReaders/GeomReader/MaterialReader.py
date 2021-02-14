from ..BaseRW import BaseRW
import struct
from ...FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_defn


class MaterialReader(BaseRW):
    """
    A class to read material data within geom files. These files are split into three main sections:
        1. The header, which is mostly unknown, but does contain counts of further data.
        2. A section of what appears to be sub-components of the material.
        3. A section of completely unknown material data.

    Completion status
    ------
    (o) MaterialReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (x) MaterialReader cannot yet fully interpret all material data in geom files in DSDB archive.
    (o) MaterialReader can write data to geom files.

    Current hypotheses and observations
    ------
    1. Some materials are listed as being e.g. 'specular' materials in the name file - so information of this type may
       exist in the material definitions.
    2. acc129's 2nd material appears to be a Lambert shader - look into this.
    3. '65280' == \x00\xff - looks like a stop code to me
    4. Material data may related to that in the shader files --- they are plaintext, so fully readable..! 1398 of them. See if you can match this up with any material data...
    """
    shader_uniform_from_ids = {
                        #        Name              numfloats
                        50: 'DiffuseTextureID',      # 0,  # Texture ID
                        51: 'DiffuseColour',         # 4,  # FP uniform, half-floats?
                        53: 'NormalMapTextureID',    # 0,  # Texture ID
                        54: 'Bumpiness',             # 1,  # FP Uniform, half-float?
                        56: 'SpecularStrength',      # 1,  # FP Uniform, half-float?
                        57: 'SpecularPower',         # 1,  # FP Uniform, half-float?
                        58: 'CubeMapTextureID',      # 0,  # Texture ID
                        59: 'ReflectionStrength',    # 1,  # FP Uniform, half-float? Works with cube map
                        60: 'FresnelExp',            # 1,  # FP Uniform, half-float?  ### COULD BE MIXED UP WTH BELOW ####
                        61: 'FresnelMin',            # 1,  # FP Uniform, half-float?
                        62: 'FuzzySpecColor',        # 3,  # FP uniform Only appears in chr435, chr912  ### COULD BE MIXED UP WTH TWO BELOW ####
                        63: 'SubColor',              # 3,  # FP uniform Only appears in chr435, chr912
                        64: 'SurfaceColor',          # 3,  # FP uniform Only appears in chr435, chr912
                        65: 'Rolloff',               # 1,  # FP uniform Only appears in chr435, chr912   ### COULD BE MIXED UP WTH BELOW ####
                        66: 'VelvetStrength',        # 1,  # FP uniform Only appears in chr435, chr912
                        67: 'UnknownTextureSlot1',   # 0,  # Texture ID
                        68: 'OverlayTextureID',      # 0,  # Texture ID Always appears with 71.
                        69: 'UnknownTextureSlot2',   # 0,  # Texture ID Overlay normal texture ID? # only appears in d13001f.geom, d13002f.geom, d13003f.geom, d13051b.geom, d13090f.geom, d15008f.geom, d15115f.geom
                        70: 'OverlayBumpiness',      # 1,  # FP Uniform, half-float?
                        71: 'OverlayStrength',       # 1,  # FP Uniform, half-float? Blend ratio of 1st and 2nd texture
                        72: 'ToonTextureID',         # 0,  # Texture UD
                        75: 'Curvature',             # 1,  # FP uniform d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom  ### COULD BE MIXED UP WTH TWO BELOW ####
                        76: 'GlassStrength',         # 1,  # FP uniform d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
                        77: 'UpsideDown',            # 1,  # FP uniform d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
                        79: 'ParallaxBiasX',         # 1,  # FP uniform d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom  ### COULD BE MIXED UP WTH BELOW ####
                        80: 'ParallaxBiasY',         # 1,  # FP uniform d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom
                        84: 'Time',                  # 1,  # VP uniform
                        85: 'ScrollSpeedSet1',       # 2,  # VP uniform
                        88: 'ScrollSpeedSet2',       # 2,  # VP uniform
                        91: 'ScrollSpeedSet3',       # 2,  # VP uniform
                        94: 'OffsetSet1',            # 2,  # VP uniform
                        97: 'OffsetSet2',            # 2,  # VP uniform # c.f. Meramon
                        100: 'DistortionStrength',   # 1,  # FP uniform, half-float?
                        113: 'LightMapStrength',     # 1,  # FP Uniform, half-float?  ### COULD BE MIXED UP WTH BELOW ####
                        114: 'LightMapPower',        # 1,  # FP Uniform, half-float?
                        116: 'OffsetSet3',           # 2,  # VP uniform
                        119: 'Fat',                  # 1,  # VP uniform
                        120: 'RotationSet1',         # 1,  # VP uniform # eff_bts_chr429_swarhead.geom, eff_bts_chr590_hdr.geom
                        123: 'RotationSet2',         # 1,  # VP uniform # chr803.geom, chr805.geom, eff_bts_chr803_s02.geom
                        129: 'ScaleSet1',            # 2,  # VP uniform # eff_bts_chr802_s01.geom
                        141: 'ZBias',                # 1,  # VP uniform, half-float?
                        142: 'UnknownTextureSlot3',  # 0   # Texture ID # eff_bts_chr032_c_revolution.geom
                      }
    shader_uniform_from_names = dict([reversed(i) for i in shader_uniform_from_ids.items()])

    def __init__(self, io_stream):
        super().__init__(io_stream)

        # Header variables
        self.unknown_0x00 = None
        self.unknown_0x02 = None
        self.shader_hex = None
        self.num_shader_uniforms = None
        self.num_unknown_data = None
        self.unknown_0x16 = None

        # Data variables
        self.shader_uniforms = []
        self.unknown_data = []

        self.subreaders = [self.unknown_data]

    def read(self):
        self.read_write(self.read_buffer, 'read', self.read_raw, self.prepare_material_read)
        self.interpret_material()

    def write(self):
        self.reinterpret_material()
        self.read_write(self.write_buffer, 'write', self.write_raw, lambda: None)

    def read_write(self, rw_operator, rw_method_name, rw_operator_raw, preparation_operator):
        self.rw_header(rw_operator, rw_operator_raw)
        preparation_operator()
        self.rw_material_components(rw_operator_raw)
        self.rw_unknown_data(rw_method_name)

    def rw_header(self, rw_operator, rw_operator_raw):
        rw_operator('unknown_0x00', 'H')
        #rw_operator('unknown_0x01', 'B')
        rw_operator('unknown_0x02', 'H')
        #rw_operator('unknown_0x03', 'B')
        rw_operator_raw('shader_hex', 16)
        rw_operator('num_shader_uniforms', 'B')  # Known
        rw_operator('num_unknown_data', 'B')  # Known
        rw_operator('unknown_0x16', 'H')  # 1, 3, or 5... has a 1:1 correspondence with the shader hex

    def rw_material_components(self, rw_operator_raw):
        rw_operator_raw("shader_uniforms", 24 * self.num_shader_uniforms)

    def rw_unknown_data(self, rw_method_name):
        for component_reader in self.unknown_data:
            getattr(component_reader, rw_method_name)()

    def prepare_material_read(self):
        self.unknown_data = [UnknownMaterialData(self.bytestream) for _ in range(self.num_unknown_data)]

    def interpret_material(self):
        self.shader_hex: bytes
        shader_hex_pt_1 = self.shader_hex[0:4][::-1].hex()
        shader_hex_pt_2 = self.shader_hex[4:8][::-1].hex()
        shader_hex_pt_3 = self.shader_hex[8:12][::-1].hex()
        shader_hex_pt_4 = self.shader_hex[12:16][::-1].hex()

        self.shader_hex = '_'.join((shader_hex_pt_1, shader_hex_pt_2, shader_hex_pt_3, shader_hex_pt_4))

        self.shader_uniforms = [self.shader_uniform_factory(data) for data in self.chunk_list(self.shader_uniforms, 24)]
        self.shader_uniforms = {elem[0]: elem[1] for elem in self.shader_uniforms}

    def reinterpret_material(self):
        self.shader_hex: str
        hex_parts = self.shader_hex.split('_')
        shader_hex_pt_1 = bytes.fromhex(hex_parts[0])[::-1]
        shader_hex_pt_2 = bytes.fromhex(hex_parts[1])[::-1]
        shader_hex_pt_3 = bytes.fromhex(hex_parts[2])[::-1]
        shader_hex_pt_4 = bytes.fromhex(hex_parts[3])[::-1]

        self.shader_hex = b''.join((shader_hex_pt_1, shader_hex_pt_2, shader_hex_pt_3, shader_hex_pt_4))
        self.shader_uniforms = b''.join([self.shader_uniform_data_factory(uniform_name, uniform) for uniform_name, uniform in self.shader_uniforms.items()])

    def shader_uniform_factory(self, data):
        payload = data[:16]
        uniform_type = MaterialReader.shader_uniform_from_ids[data[16]]
        num_floats = data[17]
        always_65280 = struct.unpack('H', data[18:20])[0]
        padding_0x14 = struct.unpack('I', data[20:])[0]

        assert always_65280 == 65280, f"Shader uniform variable always_65280 was {always_65280}, not 65280."
        assert padding_0x14 == 0, f"Shader padding_0x14 was {padding_0x14}, not 0."

        if num_floats == 0:
            payload = struct.unpack('H'*8, payload)
            for i, datum in enumerate(payload[1:6]):
                assert datum == 0, f"Element {i + num_floats} is not pad bytes!"
            payload = [payload[0], *payload[6:]]
        else:
            payload = struct.unpack('f'*num_floats, payload[:num_floats*4])
            for i, datum in enumerate(payload[num_floats:]):
                assert datum == 0, f"Element {i+num_floats} is not pad bytes!"
            payload = payload[:num_floats]

        return uniform_type, shader_uniforms_from_defn[(uniform_type, num_floats)](payload)

    def shader_uniform_data_factory(self, uniform_type, shader_uniform):
        if shader_uniform.num_floats == 0:
            data = struct.pack('H', shader_uniform.data[0]) + 10*self.pad_byte + struct.pack('HH', *shader_uniform.data[1:])
        else:
            data = struct.pack(f'{shader_uniform.num_floats}f', *shader_uniform.data)
            data += 4*self.pad_byte*(4 - shader_uniform.num_floats)

        data += struct.pack('B', self.shader_uniform_from_names[uniform_type])
        data += struct.pack('B', shader_uniform.num_floats)
        data += struct.pack('H', 65280)
        data += struct.pack('I', 0)

        return data


class UnknownMaterialData(BaseRW):
    """
    A class holding unknown data that only occurs in some materials.

    Current hypotheses and observations
    ------
    None
    """

    possibly_types = {160: 'If',  # 516, then one of eight float values between 0 and 0.5..?
                      161: 'II',  # Always (1, 0)
                      162: 'II',  # (0, 768) or (770, 1)
                      163: 'HHI',  # (32779, 0) or (32774, 0)
                      164: 'II',  # Always (1, 0)
                      166: 'II',  # Always (0, 0)
                      167: 'II',  # Always (516, 0)
                      168: 'II',  # Always (0, 0)
                      169: 'II',  # Always (0, 0)
                      172: 'II',  # Always (0, 0)
                      }

    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.data = None
        self.padding_0x08 = None
        self.padding_0x0A = None
        self.padding_0x0C = None
        self.padding_0x0E = None
        self.maybe_component_type = None
        self.always_100 = None
        self.always_65280 = None
        self.padding_0x14 = None

    def read(self):
        args = self.bytestream.read(24)

        self.data = args[:8]

        data = struct.unpack('HHHHBBHI', args[8:])
        self.padding_0x08 = data[0]  # Always 0
        assert self.padding_0x08 == 0, f"padding_0x08 is {self.padding_0x08}, not 0"
        self.padding_0x0A = data[1]  # Always 0
        assert self.padding_0x0A == 0, f"padding_0x0A is {self.padding_0x0A}, not 0"
        self.padding_0x0C = data[2]  # Always 0
        assert self.padding_0x0C == 0, f"padding_0x0C is {self.padding_0x0C}, not 0"
        self.padding_0x0E = data[3]  # Always 0
        assert self.padding_0x0E == 0, f"padding_0x0E is {self.padding_0x0E}, not 0"

        self.maybe_component_type = data[4]  # Few values, 160 - 169 + 172 # Presumably the component type?

        self.always_100 = data[5]  # Always 100
        assert self.always_100 == 100, f"always_100 is {self.always_100}, not 100"
        self.always_65280 = data[6]  # Always 65280
        assert self.always_65280 == 65280, f"always_65280 is {self.always_65280}, not 65280"
        self.padding_0x14 = data[7]  # Always 0
        assert self.padding_0x14 == 0, f"padding_0x14 is {self.padding_0x14}, not 0"

        self.data = struct.unpack(UnknownMaterialData.possibly_types[self.maybe_component_type], self.data)

        self.header = (*self.data, self.maybe_component_type, self.always_100, self.always_65280, self.padding_0x14)

    def write(self):
        data = struct.pack(UnknownMaterialData.possibly_types[self.maybe_component_type], *self.data)
        data += struct.pack('H', self.padding_0x08)
        data += struct.pack('H', self.padding_0x0A)
        data += struct.pack('H', self.padding_0x0C)
        data += struct.pack('H', self.padding_0x0E)
        data += struct.pack('B', self.maybe_component_type)
        data += struct.pack('B', self.always_100)
        data += struct.pack('H', self.always_65280)
        data += struct.pack('I', self.padding_0x14)
        assert len(data) == 24
        self.bytestream.write(data)
