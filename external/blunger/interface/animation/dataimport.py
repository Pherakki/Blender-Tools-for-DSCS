def create_fcurves(action, actiongroup, fcurve_name, interpolation_method, frames, values, transform_indices):
    fcs = []
    if len(frames) != 0:
        for i, t_idx in enumerate(transform_indices):
            fc = action.fcurves.new(fcurve_name, index=i)
            fc.keyframe_points.add(count=len(frames))
            fc.keyframe_points.foreach_set("co",
                                           [x for co in zip(frames,
                                                            [value[t_idx]         for value in values]) 
                                            for x in co])
            for k in fc.keyframe_points:
                k.interpolation = interpolation_method
            fc.group = actiongroup
            fc.lock = True
            fcs.append(fc)
        for fc in fcs:
            fc.update()
        for fc in fcs:
            fc.lock = False
    return fcs


def create_fcurve(action, actiongroup, fcurve_name, index, interpolation_method, frames, values):
    fc = action.fcurves.new(fcurve_name, index=index)
    fc.keyframe_points.add(count=len(frames))
    fc.keyframe_points.foreach_set("co", [x for co in zip(frames, values) for x in co])
    for k in fc.keyframe_points:
        k.interpolation = interpolation_method
        fc.group = actiongroup

def create_nla_track(action, armature, blend_type):
    armature.animation_data.action = action
    track = armature.animation_data.nla_tracks.new()
    track.name = action.name
    track.mute = True
    strip = track.strips.new(action.name, 1, action)
    strip.blend_type = blend_type
    armature.animation_data.action = None
