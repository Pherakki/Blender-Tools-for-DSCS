from ....serialization.Serializable import Serializable


class LightBinary(Serializable):
    def __init__(self):
        super().__init__()

        self.bone_name_hash    = None
        self.mode              = None
        self.light_id          = None
        self.intensity         = None
        self.unknown_fog_param = None
        self.red               = None
        self.green             = None
        self.blue              = None
        self.alpha             = None
        self.unknown_0x20      = None
        self.unknown_0x24      = None
        self.unknown_0x28      = None
        self.unknown_0x2C      = None

    def read_write(self, rw):
        self.bone_name_hash = rw.rw_uint32(self.bone_name_hash)
        self.mode           = rw.rw_uint16(self.mode) # 0 = POINT, 2 = AMBIENT, 3 = DIRECTIONAL, 4 = UNKNOWN: Fog?
        self.light_id       = rw.rw_uint16(self.light_id) # Runs from 0 - 4

        self.intensity      = rw.rw_float32(self.intensity)
        self.unknown_fog_param = rw.rw_float32(self.unknown_fog_param)  # Fog height?

        self.red   = rw.rw_float32(self.red)
        self.green = rw.rw_float32(self.green)
        self.blue  = rw.rw_float32(self.blue)
        self.alpha = rw.rw_float32(self.alpha)

        # Not sure.
        self.unknown_0x20 = rw.rw_int32(self.unknown_0x20)
        self.unknown_0x24 = rw.rw_int32(self.unknown_0x24)
        self.unknown_0x28 = rw.rw_int32(self.unknown_0x28)
        self.unknown_0x2C = rw.rw_float32(self.unknown_0x2C)
        
        rw.align(0x30, 0x40)
