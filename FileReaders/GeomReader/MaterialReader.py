from ..BaseRW import BaseRW
import struct


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
    (x) MaterialReader cannot yet write data to geom files.

    Current hypotheses and observations
    ------
    1. Some materials are listed as being e.g. 'specular' materials in the name file - so information of this type may
       exist in the material definitions.
    2. acc129's 2nd material appears to be a Lambert shader - look into this.
    """

    def __init__(self, io_stream):
        super().__init__(io_stream)

        # Header variables
        self.unknown_0x00 = None
        self.unknown_0x02 = None
        self.unknown_0x04 = None
        self.unknown_0x06 = None
        self.unknown_0x08 = None
        self.unknown_0x0A = None
        self.unknown_0x0C = None
        self.unknown_0x0E = None
        self.unknown_0x10 = None
        self.unknown_0x11 = None
        self.unknown_0x12 = None
        self.num_material_components = None
        self.num_unknown_data = None
        self.unknown_0x16 = None

        # Data variables
        self.material_components = []
        self.unknown_data_2 = []

    def read_header(self):
        # Changing 0x04 - 0x0E to random values results in no material drawn
        # unknown_0x12 must be exactly correct - might be a data type or material type
        # changing 0x16 to the other values seems to have no effect
        self.unknown_0x00 = self.bytestream.read(16) #self.unpack('e')
        #self.unknown_0x02 = self.unpack('e')
        #self.unknown_0x04 = self.unpack('H')
        #self.unknown_0x06 = self.unpack('H')
        #self.unknown_0x08 = self.unpack('H')
        #self.unknown_0x0A = self.unpack('H')
        #self.unknown_0x0C = self.unpack('H'
        #self.unknown_0x0E = self.unpack('H')  # These are all multiples of 4. Highly suggestive.
        self.unknown_0x10 = self.unpack('B')  # 0, except for one file, where it is 1
        self.unknown_0x11 = self.unpack('B')  # 0 or 128.
        self.unknown_0x12 = self.unpack('H')  # 0, 3, 4, 5, 6... possibly data type? No obvious pattern though...
        self.num_material_components = self.unpack('B')  # Known
        self.num_unknown_data = self.unpack('B')  # Known
        self.unknown_0x16 = self.unpack('H')  # 1, 3, or 5

        self.header = (self.unknown_0x00, *self.header)

    def read_material_components(self):
        for _ in range(self.num_material_components):
            self.material_components.append(MaterialComponent(self.bytestream))
            self.material_components[-1].read()

    def read_unknown_data(self):
        for _ in range(self.num_unknown_data):
            self.unknown_data_2.append(UnknownMaterialData(self.bytestream.read(24)))


class MaterialComponent(BaseRW):
    component_types = {
                        #      Name       numfloats
                        50: ('TextureID', 0),  # idx 0 is texture id, rest are...?
                        51: ('Colour', 4),  # RBGA? RBG at least seems to be correct, not sure about the last float
                        53: ('unknown_component_type', 0),
                        54: ('unknown_component_type', 1),
                        56: ('unknown_component_type', 1),
                        57: ('unknown_component_type', 1),
                        58: ('unknown_component_type', 0),
                        59: ('unknown_component_type', 1),
                        60: ('unknown_component_type', 1),
                        61: ('unknown_component_type', 1),
                        62: ('unknown_component_type', 3),  # Only appears in chr435, chr912
                        63: ('unknown_component_type', 3),  # Only appears in chr435, chr912
                        64: ('unknown_component_type', 3),  # Only appears in chr435, chr912
                        65: ('unknown_component_type', 1),  # Only appears in chr435, chr912
                        66: ('unknown_component_type', 1),  # Only appears in chr435, chr912
                        67: ('unknown_component_type', 0),
                        68: ('unknown_component_type', 0),
                        69: ('unknown_component_type', 0),  # only appears in d13001f.geom, d13002f.geom, d13003f.geom, d13051b.geom, d13090f.geom, d15008f.geom, d15115f.geom
                        70: ('unknown_component_type', 1),  # only appears in d13001f.geom, d13002f.geom, d13003f.geom, d13051b.geom, d13090f.geom, d15008f.geom, d15115f.geom
                        71: ('unknown_component_type', 1),
                        72: ('Toon?', 0),  # idx 0 is texture id, rest are...?
                        75: ('unknown_component_type', 1),  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
                        76: ('unknown_component_type', 1),  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
                        77: ('unknown_component_type', 1),  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
                        79: ('unknown_component_type', 1),  # d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom
                        80: ('unknown_component_type', 1),  # d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom
                        84: ('unknown_component_type', 1),
                        85: ('unknown_component_type', 2),
                        88: ('unknown_component_type', 2),
                        91: ('unknown_component_type', 2),
                        94: ('unknown_component_type', 2),
                        97: ('unknown_component_type', 2),
                        100: ('unknown_component_type', 1),
                        113: ('unknown_component_type', 1),
                        114: ('unknown_component_type', 1),
                        116: ('unknown_component_type', 2),
                        119: ('unknown_component_type', 1),
                        120: ('unknown_component_type', 1),  # eff_bts_chr429_swarhead.geom, eff_bts_chr590_hdr.geom
                        123: ('unknown_component_type', 1),  # chr803.geom, chr805.geom, eff_bts_chr803_s02.geom
                        129: ('unknown_component_type', 2),  # eff_bts_chr802_s01.geom
                        141: ('unknown_component_type', 1),
                        142: ('unknown_component_type', 0)  # eff_bts_chr032_c_revolution.geom
                      }

    def __init__(self, io_stream):
        super().__init__(io_stream)

        self.data = None
        self.component_type = None
        self.num_floats_in_data = None
        self.always_65280 = None
        self.padding_0x14 = None

    def read(self):
        self.data = self.bytestream.read(16)

        self.component_type = self.unpack('B')  # Each component type has a specific number of floats attached
        self.num_floats_in_data = self.unpack('B')  # If 0, it means there's 8 uint16s

        self.always_65280 = self.unpack('H')  # Always 65280. Might be a stop code?
        self.assert_equal("always_65280", 65280)
        self.padding_0x14 = self.unpack('I')  # Always 0
        self.assert_is_zero("padding_0x14")

        if self.num_floats_in_data == 0:
            data = self.decode_data_as('H', self.data)
            for i, datum in enumerate(data[1:6]):
                assert datum == 0, f"Element {i + self.num_floats_in_data} is not pad bytes!"
            self.data = [data[0], *data[6:]]
        else:
            data = self.decode_data_as('f', self.data)
            for i, datum in enumerate(data[self.num_floats_in_data:]):
                assert datum == 0, f"Element {i+self.num_floats_in_data} is not pad bytes!"
            self.data = data[:self.num_floats_in_data]

        self.header = tuple([*self.data, self.component_type, self.num_floats_in_data, self.always_65280, self.padding_0x14])


class UnknownMaterialData:
    """
    A class holding unknown data that only occurs in some materials.

    Current hypotheses and observations
    ------
    None
    """

    possibly_types = {160: 'If',  # 516, then one of eight float values between 0 and 0.5..?
                      161: 'II',  # Always (1, 0)
                      162: 'II',  # (0, 768) or (770, 1)
                      163: 'II',  # (32779, 0) or (32774, 0)
                      164: 'II',  # Always (1, 0)
                      166: 'II',  # Always (0, 0)
                      167: 'II',  # Always (516, 0)
                      168: 'II',  # Always (0, 0)
                      169: 'II',  # Always (0, 0)
                      172: 'II',  # Always (0, 0)
                      }

    def __init__(self, args):
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
