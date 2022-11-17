from .Base import GeomBinaryBase
from .MeshBinary.CyberSleuthOpenGL import MeshBinaryDSCSOpenGL
from .MeshBinary.CyberSleuthPS import MeshBinaryDSCSPS
from .MeshBinary.Megido72 import MeshBinaryMegido72


class GeomBinaryDSCSOpenGL(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryDSCSOpenGL

    @property
    def _CLASSTAG(self):
        return "DSCS CgGL GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY


class GeomBinaryDSCSPS(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryDSCSPS

    @property
    def _CLASSTAG(self):
        return "DSCS PS GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY


class GeomBinaryMegido72(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryMegido72

    @property
    def _CLASSTAG(self):
        return "Megido72 GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY
