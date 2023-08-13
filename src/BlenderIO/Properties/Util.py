import struct
import bpy


class UtilProperties(bpy.types.PropertyGroup):
    is_editmode: bpy.props.BoolProperty(name="Is Editmode", get=lambda self: self.id_data.mode == "EDIT")
