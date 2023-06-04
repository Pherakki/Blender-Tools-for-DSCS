import bpy


class SceneProperties(bpy.types.PropertyGroup):
    dir_light_direction: bpy.props.FloatVectorProperty(name="Directional Light Direction", size=3, default=(1., -1., 1.), min=-1, max=1)
    dir_light_color:     bpy.props.FloatVectorProperty(name="Directional Light Color",     size=4, default=(1., 1., 1., 1), subtype="COLOR", min=0, max=1)
    
    ambient_color: bpy.props.FloatVectorProperty(name="Ambient Light Color", size=3, default=(1., 1., 1.), subtype="COLOR", min=0, max=1)
    ground_color:  bpy.props.FloatVectorProperty(name="Ground Light Color",  size=3, default=(1., 1., 1.), subtype="COLOR", min=0, max=1)
    sky_direction: bpy.props.FloatVectorProperty(name="Sky Direction",       size=3, default=(0., 0., 1.), min=-1, max=1)
