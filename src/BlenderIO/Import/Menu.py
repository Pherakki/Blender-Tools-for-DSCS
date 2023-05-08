import bpy
from .Operator import ImportDSCS, ImportDSCS_PS


class MVImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_MediaVision_import_submenu"
    bl_label = "Media.Vision"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportDSCS.bl_idname, text="DSCS Model - PC/Switch (.name)")
        layout.operator(ImportDSCS_PS.bl_idname, text="DSCS Model - PS4/Vita (.name)")
        #layout.operator(ImportMegido.bl_idname, text="Megido 72 Model (.name)")

def menu_func_import(self, context):
    self.layout.menu(MVImportSubmenu.bl_idname)
