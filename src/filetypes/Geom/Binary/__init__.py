from .Base import GeomBinaryBase
from .Mesh.CyberSleuthOpenGL import MeshBinaryDSCSOpenGL
from .Mesh.CyberSleuthPS import MeshBinaryDSCSPS
from .Mesh.Megido72 import MeshBinaryMegido72


class GeomFileBinaryDSCSOpenGL(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryDSCSOpenGL

    @property
    def _CLASSTAG(self):
        return "DSCS CgGL GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY


class GeomFileBinaryDSCSPS(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryDSCSPS

    @property
    def _CLASSTAG(self):
        return "DSCS PS GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY


class GeomFileBinaryMegido72(GeomBinaryBase):
    __MESH_BINARY = MeshBinaryMegido72

    @property
    def _CLASSTAG(self):
        return "Megido72 GeomBinary"

    @property
    def MESH_TYPE(self): return self.__MESH_BINARY
