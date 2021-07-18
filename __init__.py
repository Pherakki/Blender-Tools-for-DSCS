import bpy
from .BlenderIO.Import import ImportDSCS
from .BlenderIO.Export import ExportDSCS


bl_info = {
        "name": "Digimon Story: Cyber Sleuth (.name)",
        "description": "Imports model files from Digimon Story: Cyber Sleuth (PC)",
        "author": "Pherakki",
        "version": (0, 1),
        "blender": (2, 80, 0),
        "location": "File > Import, File > Export",
        "warning": "",
        "category": "Import-Export",
        }


def menu_func_import(self, context):
    self.layout.operator(ImportDSCS.bl_idname, text="DSCS Model (.name)")


def menu_func_export(self, context):
    self.layout.operator(ExportDSCS.bl_idname, text="DSCS Model (.name)")


def register():
    blender_version = bpy.app.version_string  # Can use this string to switch version-dependent Blender API codes
    bpy.utils.register_class(ImportDSCS)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ExportDSCS)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportDSCS)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ExportDSCS)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

# if __name__ == "__main__":
#     register()
