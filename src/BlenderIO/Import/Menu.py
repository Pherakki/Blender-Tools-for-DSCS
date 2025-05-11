import bpy
from .Operator import ImportDSCSOpenGL, ImportDSCSPS, ImportDSCSAnim
from .Operator import ImportMegido72, ImportMegido72Anim
from .Operator import ImportHundredLine, ImportHundredLineAnim

class DSCSImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_CyberSleuth_import_submenu"
    bl_label = "Cyber Sleuth"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportDSCSOpenGL.bl_idname, text="DSCS Model [PC/Switch] (.geom)")
        layout.operator(ImportDSCSPS.bl_idname, text="DSCS Model [PS4/Vita] (.geom)")
        layout.operator(ImportDSCSAnim.bl_idname, text="DSCS Animation (.anim)")

class Megido72ImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_Megido72_import_submenu"
    bl_label = "Megido72"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportMegido72.bl_idname, text="Megido 72 Model (.geom)")
        layout.operator(ImportMegido72Anim.bl_idname, text="Megido 72 Animation (.anim)")

class HundredLineImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_LDAHundredLine_import_submenu"
    bl_label = "Hundred Line"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportHundredLine.bl_idname, text="Hundred Line Model (.geom)")
        layout.operator(ImportHundredLineAnim.bl_idname, text="Hundred Line Animation (.anim)")


class MVImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_MVGL_import_submenu"
    bl_label = "MVGL (.geom/.anim)"

    def draw(self, context):
        layout = self.layout
        layout.menu(DSCSImportSubmenu.bl_idname)
        layout.menu(Megido72ImportSubmenu.bl_idname)
        layout.menu(HundredLineImportSubmenu.bl_idname)
    
    @classmethod
    def register(cls):
        bpy.utils.register_class(DSCSImportSubmenu)
        bpy.utils.register_class(Megido72ImportSubmenu)
        bpy.utils.register_class(HundredLineImportSubmenu)
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(DSCSImportSubmenu)
        bpy.utils.unregister_class(Megido72ImportSubmenu)
        bpy.utils.unregister_class(HundredLineImportSubmenu)

def menu_func_import(self, context):
    self.layout.menu(MVImportSubmenu.bl_idname)
