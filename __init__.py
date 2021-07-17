import bpy
from .BlenderIO.Import import ImportDSCSPC, ImportDSCSPS4
from .BlenderIO.Export import ExportDSCSPC, ExportDSCSPS4


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
    self.layout.operator(ImportDSCSPC.bl_idname, text="DSCS Model [PC] (.name)")
    self.layout.operator(ImportDSCSPS4.bl_idname, text="DSCS Model [PS4] (.name)")


def menu_func_export(self, context):
    self.layout.operator(ExportDSCSPC.bl_idname, text="DSCS Model [PC] (.name)")
    self.layout.operator(ExportDSCSPS4.bl_idname, text="DSCS Model [PS4] (.name)")


def register():
    blender_version = bpy.app.version_string  # Can use this string to switch version-dependent Blender API codes
    bpy.utils.register_class(ImportDSCSPC)
    bpy.utils.register_class(ImportDSCSPS4)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ExportDSCSPC)
    bpy.utils.register_class(ExportDSCSPS4)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportDSCSPC)
    bpy.utils.unregister_class(ImportDSCSPS4)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ExportDSCSPC)
    bpy.utils.unregister_class(ExportDSCSPS4)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

# if __name__ == "__main__":
#     register()
