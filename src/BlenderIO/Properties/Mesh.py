import struct
import bpy

def flags_getter(self):
    v = 0
    v |= self.is_rendered  << 0
    v |= self.is_wireframe << 1
    #v |= self.flag_2 << 2
    v |= self.flag_3       << 3
    v |= self.flag_4       << 4
    v |= self.flag_5       << 5
    v |= self.flag_6       << 6
    v |= self.flag_7       << 7
    return v


class MeshProperties(bpy.types.PropertyGroup):
    name_hash: bpy.props.IntProperty(name="Name Hash", default=0)

    is_rendered:    bpy.props.BoolProperty(name="Rendered",  default=True)
    is_wireframe:   bpy.props.BoolProperty(name="Wireframe", default=False)
    #flag_2:    bpy.props.BoolProperty("Flag 2", default=False) # Consecutive mesh indices
    flag_3:    bpy.props.BoolProperty(name="Flag 3", default=False)
    flag_4:    bpy.props.BoolProperty(name="Flag 4", default=False)
    flag_5:    bpy.props.BoolProperty(name="Flag 5", default=False)
    flag_6:    bpy.props.BoolProperty(name="Flag 6", default=False)
    flag_7:    bpy.props.BoolProperty(name="Flag 7", default=False)

    flags:     bpy.props.IntProperty(name="Flags", get=flags_getter, options={'HIDDEN'})
