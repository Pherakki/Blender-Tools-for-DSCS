import bpy


class BoneProperties(bpy.types.PropertyGroup):
    flag: bpy.props.BoolProperty(name="Flag", default=False)
