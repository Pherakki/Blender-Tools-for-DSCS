import bpy


class MaterialProperties(bpy.types.PropertyGroup):
    flag_0:      bpy.props.BoolProperty(name="Unknown Flag 0", default=False )
    cast_shadow: bpy.props.BoolProperty(name="Cast Shadow",    default=False )
    flag_2:      bpy.props.BoolProperty(name="Unknown Flag 2", default=False )
    flag_3:      bpy.props.BoolProperty(name="Unknown Flag 3", default=False )
    flag_4:      bpy.props.BoolProperty(name="Unknown Flag 4", default=False )
    flag_5:      bpy.props.BoolProperty(name="Unknown Flag 5", default=False )
    flag_6:      bpy.props.BoolProperty(name="Unknown Flag 6", default=False )
    flag_7:      bpy.props.BoolProperty(name="Unknown Flag 7", default=False )
    flag_8:      bpy.props.BoolProperty(name="Unknown Flag 8", default=False )
    flag_9:      bpy.props.BoolProperty(name="Unknown Flag 9", default=False )
    flag_10:     bpy.props.BoolProperty(name="Unknown Flag 10", default=False )
    flag_11:     bpy.props.BoolProperty(name="Unknown Flag 11", default=False )
    flag_12:     bpy.props.BoolProperty(name="Unknown Flag 12", default=False )
    flag_13:     bpy.props.BoolProperty(name="Unknown Flag 13", default=False )
    flag_14:     bpy.props.BoolProperty(name="Unknown Flag 14", default=False )
    flag_15:     bpy.props.BoolProperty(name="Unknown Flag 15", default=False )

    # Should be able to remove this later...
    shader_name = bpy.props.StringProperty(name="Shader Name", default="")
