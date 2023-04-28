import bpy

from ..Context import get_active_obj, set_active_obj

class ReportableError:
    __slots__ = ("msg",)
    
    HAS_DISPLAYABLE_ERROR = False
    
    def __init__(self, msg):
        self.msg = msg
    
    def showErrorData(self):
        pass
    
    def hideErrorData(self):
        pass


class DisplayableGeometryError(ReportableError):
    __slots__ = ("bpy_mesh_obj", "prev_obj")
    
    HAS_DISPLAYABLE_ERROR = True
    
    def __init__(self, msg, bpy_mesh_obj):
        super().__init__(msg)
        self.bpy_mesh_obj = bpy_mesh_obj
        self.prev_obj = None
        
    def showErrorData(self):
        self.prev_obj = get_active_obj()
        set_active_obj(self.mesh)
        bpy.ops.object.mode_set(mode="OBJECT")
        
        bpy_mesh = self.bpy_mesh_obj.data
        
        bpy_mesh.polygons.foreach_set("select", (False,) * len(bpy_mesh.polygons))
        bpy_mesh.edges   .foreach_set("select", (False,) * len(bpy_mesh.edges))
        bpy_mesh.vertices.foreach_set("select", (False,) * len(bpy_mesh.vertices))
        
        for vidx in self.indices:
            bpy_mesh.vertices[vidx].select = True
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
        
    def hideErrorData(self):
        set_active_obj(self.bpy_mesh_obj)
        bpy.ops.object.mode_set(mode="OBJECT")
        
        bpy_mesh = self.bpy_mesh_obj.data
        
        bpy_mesh.polygons.foreach_set("select", (False,) * len(bpy_mesh.polygons))
        bpy_mesh.edges   .foreach_set("select", (False,) * len(bpy_mesh.edges))
        bpy_mesh.vertices.foreach_set("select", (False,) * len(bpy_mesh.vertices))
        
        if self.prev_obj is not None:
            set_active_obj(self.prev_obj)

class DisplayableVerticesError(DisplayableGeometryError):
    __slots__ = ("vertex_indices",)
    
    HAS_DISPLAYABLE_ERROR = True
    
    def __init__(self, msg, bpy_mesh_obj, vertex_indices):
        super().__init__(msg, bpy_mesh_obj)
        self.vertex_indices = vertex_indices
        
    def showErrorData(self):
        super().showErrorData()
        
        bpy_mesh = self.bpy_mesh_obj.data
        for vidx in self.vertex_indices:
            bpy_mesh.vertices[vidx].select = True
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")


class DisplayablePolygonsError(DisplayableGeometryError):
    __slots__ = ("polygon_indices",)
    
    HAS_DISPLAYABLE_ERROR = True
    
    def __init__(self, msg, bpy_mesh_obj, polygon_indices):
        super().__init__(msg, bpy_mesh_obj)
        self.polygon_indices = polygon_indices
        
    def showErrorData(self):
        super().showErrorData()
        
        bpy_mesh = self.bpy_mesh_obj.data
        for pidx in self.polygon_indices:
            bpy_mesh.polygons[pidx].select = True
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")


class DisplayableMeshesError(ReportableError):
    __slots__ = ("bpy_mesh_objs",)
    
    HAS_DISPLAYABLE_ERROR = True
    
    def __init__(self, msg, bpy_mesh_objs):
        super().__init__(msg)
        self.bpy_mesh_objs = bpy_mesh_objs
        
    def showErrorData(self):
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in self.bpy_mesh_objs:
            mesh.select_set(True)
        
    def hideErrorData(self):
        pass
