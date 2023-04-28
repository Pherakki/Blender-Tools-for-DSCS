import bpy


class DSCSKeyframe(bpy.types.PropertyGroup):
    frame: bpy.props.IntProperty(name="Frame", default=0, min=0)
    value: bpy.props.FloatProperty(name="Value", default=0.)


class DSCSAnimFloatChannel(bpy.types.PropertyGroup):
    channel_idx:         bpy.props.IntProperty(name="Channel", subtype="UNSIGNED")
    keyframes:           bpy.props.CollectionProperty(type=DSCSKeyframe, name="Keyframes")
    active_keyframe_idx: bpy.props.IntProperty(name="", default=0, min=0)


class AnimationProperties(bpy.types.PropertyGroup):
    float_channels: bpy.props.CollectionProperty(type=DSCSAnimFloatChannel, name="Float Channels")
    active_float_channel_idx: bpy.props.IntProperty(name="", default=0, min=0)
