import bpy

     
class LightProperties(bpy.types.PropertyGroup):
    bone_hash: bpy.props.IntProperty(name="Bone Hash", default=-1)
    
    mode: bpy.props.EnumProperty(items=[("POINT", "Point", ""),
                                        ("UNKNOWN", "Unknown", ""),
                                        ("AMBIENT", "Ambient", ""),
                                        ("DIRECTIONAL", "Directional", ""),
                                        ("FOG", "Fog", "")], name="Mode", default="DIRECTIONAL")
    light_id:     bpy.props.IntProperty(name="ID", default=0)
    intensity:    bpy.props.FloatProperty(name="Intensity", default=1.)
    fog_height:   bpy.props.FloatProperty(name="Fog Height", default=0.)
    alpha:        bpy.props.FloatProperty(name="Alpha", default=1.)
    unknown_0x20: bpy.props.IntProperty(name="Unknown 0x20", default=0)
    unknown_0x24: bpy.props.IntProperty(name="Unknown 0x24", default=0)
    unknown_0x28: bpy.props.IntProperty(name="Unknown 0x28", default=0)
    unknown_0x2C: bpy.props.FloatProperty(name="Unknown 0x2C", default=0.)
