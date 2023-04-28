import bpy

from .Operator import ExportDSCS


class MVExportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_MediaVision_export_submenu"
    bl_label = "Media.Vision"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExportDSCS.bl_idname, text="DSCS Model (.name)")
        # layout.operator(ExportMegido.bl_idname, text="Megido 72 Model (.name)")


def menu_func_export(self, context):
    self.layout.menu(MVExportSubmenu.bl_idname)
