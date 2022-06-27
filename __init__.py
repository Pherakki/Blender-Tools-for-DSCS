import bpy
from .BlenderIO.Import import ImportDSCS, ImportMegido
from .BlenderIO.Export import ExportDSCS, ExportMegido
from .BlenderIO.DSCSBlenderUtils import MessagePopup


bl_info = {
        "name": "Media.Vision Import/Export (.name)",
        "description": "Imports model and animation files from Media.Vision titles.",
        "author": "Pherakki",
        "version": (0, 2),
        "blender": (2, 80, 0),
        "location": "File > Import, File > Export",
        "warning": "",
        "wiki_url": "https://github.com/Pherakki/Blender-Tools-for-DSCS",
        "tracker_url": "https://github.com/Pherakki/Blender-Tools-for-DSCS/issues",
        "category": "Import-Export",
        }


class MVImportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_MediaVision_import_submenu"
    bl_label = "Media.Vision"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportDSCS.bl_idname, text="DSCS Model (.name)")
        layout.operator(ImportMegido.bl_idname, text="Megido 72 Model (.name)")


class MVExportSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_MediaVision_export_submenu"
    bl_label = "Media.Vision"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExportDSCS.bl_idname, text="DSCS Model (.name)")
        # layout.operator(ExportMegido.bl_idname, text="Megido 72 Model (.name)")


def menu_func_import(self, context):
    self.layout.menu(MVImportSubmenu.bl_idname)


def menu_func_export(self, context):
    self.layout.menu(MVExportSubmenu.bl_idname)


def register():
    blender_version = bpy.app.version_string  # Can use this string to switch version-dependent Blender API codes
    bpy.utils.register_class(ImportDSCS)
    bpy.utils.register_class(ImportMegido)
    bpy.utils.register_class(MVImportSubmenu)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ExportDSCS)
    # bpy.utils.register_class(ExportMegido)
    bpy.utils.register_class(MVExportSubmenu)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(MessagePopup)


def unregister():
    bpy.utils.unregister_class(ImportDSCS)
    bpy.utils.unregister_class(ImportMegido)
    bpy.utils.unregister_class(MVImportSubmenu)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ExportDSCS)
    # bpy.utils.unregister_class(ExportMegido)
    bpy.utils.unregister_class(MVExportSubmenu)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(MessagePopup)

# if __name__ == "__main__":
#     register()
