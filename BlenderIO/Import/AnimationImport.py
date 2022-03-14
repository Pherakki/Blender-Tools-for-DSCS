import bpy


def import_animations(name_prefix, armature_name, model_data):
    model_armature = bpy.data.objects[armature_name]
    model_armature.animation_data_create()
    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode="POSE")

    for animation_name, animation_data in list(model_data.animations.items())[::-1]:
        if animation_name == name_prefix:
            track_name = "base"
        else:
            track_name = animation_name[len(name_prefix)+1:]  # +1 to also remove the underscore
        action = bpy.data.actions.new(animation_name)

        for rotation_data, location_data, scale_data, bone_name in zip(animation_data.rotations.values(),
                                                                       animation_data.locations.values(),
                                                                       animation_data.scales.values(),
                                                                       model_data.skeleton.bone_names):
            actiongroup = action.groups.new(bone_name)
            if len(rotation_data.frames) != 0:
                fcs = []
                for i in range(4):
                    fc = action.fcurves.new(f'pose.bones["{bone_name}"].rotation_quaternion', index=i)
                    fc.keyframe_points.add(count=len(rotation_data.frames))
                    fc.keyframe_points.foreach_set("co",
                                                   [x for co in zip([float(elem + 1) for elem in rotation_data.frames],
                                                                    [elem[i] for elem in rotation_data.values]) for x in
                                                    co])
                    fc.group = actiongroup
                    fc.lock = True
                    fcs.append(fc)
                for fc in fcs:
                    fc.update()
                for fc in fcs:
                    fc.lock = False
            if len(location_data.frames) != 0:
                fcs = []
                for i in range(3):
                    fc = action.fcurves.new(f'pose.bones["{bone_name}"].location', index=i)
                    fc.keyframe_points.add(count=len(location_data.frames))
                    fc.keyframe_points.foreach_set("co",
                                                   [x for co in zip([float(elem + 1) for elem in location_data.frames],
                                                                    [elem[i] for elem in location_data.values]) for x in
                                                    co])
                    fc.group = actiongroup
                    for k in fc.keyframe_points:
                        k.interpolation = "LINEAR"
                    fc.lock = True
                    fcs.append(fc)
                for fc in fcs:
                    fc.update()
                for fc in fcs:
                    fc.lock = False
            if len(scale_data.frames) != 0:
                fcs = []
                for i in range(3):
                    fc = action.fcurves.new(f'pose.bones["{bone_name}"].scale', index=i)
                    fc.keyframe_points.add(count=len(scale_data.frames))
                    fc.keyframe_points.foreach_set("co",
                                                   [x for co in zip([float(elem + 1) for elem in scale_data.frames],
                                                                    [elem[i] for elem in scale_data.values]) for x in
                                                    co])
                    fc.group = actiongroup
                    for k in fc.keyframe_points:
                        k.interpolation = "LINEAR"
                    fc.lock = True
                    fcs.append(fc)
                for fc in fcs:
                    fc.update()
                for fc in fcs:
                    fc.lock = False

        # Do this properly later
        for idx in animation_data.uv_data:
            channel = animation_data.uv_data[idx]
            action[f"uv_data_frames_{idx}"] = list(channel.keys())
            action[f"uv_data_values_{idx}"] = list(channel.values())

        model_armature.animation_data.action = action
        track = model_armature.animation_data.nla_tracks.new()
        track.name = track_name
        track.mute = True
        nla_strip = track.strips.new(action.name, action.frame_range[0], action)
        nla_strip.scale = 24 / animation_data.playback_rate
        nla_strip.blend_type = "COMBINE"
        model_armature.animation_data.action = None

    bpy.ops.object.mode_set(mode="OBJECT")
