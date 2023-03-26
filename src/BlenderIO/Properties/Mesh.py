import bpy


class MeshProperties(bpy.types.PropertyGroup):
    name_hash: bpy.props.StringProperty(name="Name Hash", default="")
