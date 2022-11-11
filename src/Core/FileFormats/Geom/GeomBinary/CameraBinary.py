from ....serialization.Serializable import Serializable


class CameraBinary(Serializable):
    def __init__(self):
        super().__init__()

        self.bone_name_hash = None
        self.fov            = None
        self.aspect_ratio   = None
        self.zNear          = None

        self.zFar               = None
        self.orthographic_scale = None
        self.projection         = None

    def read_write(self, rw):
        self.bone_name_hash     = rw.rw_uint32(self.bone_name_hash)
        self.fov                = rw.rw_float32(self.fov)
        self.aspect_ratio       = rw.rw_float32(self.aspect_ratio)
        self.zNear              = rw.rw_float32(self.zNear)
        self.zFar               = rw.rw_float32(self.zFar)
        self.orthographic_scale = rw.rw_float32(self.orthographic_scale)
        self.projection         = rw.rw_uint32(self.projection)  # 0 = Perspective, 1 = Ortho
        rw.align(0x1C, 0x30)
