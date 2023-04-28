import bpy


class CameraProperties(bpy.types.PropertyGroup):
    aspect_ratio: bpy.props.FloatProperty(name="Aspect Ratio", default=4/3)
