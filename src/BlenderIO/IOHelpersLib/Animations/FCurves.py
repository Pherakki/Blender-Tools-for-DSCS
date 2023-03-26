def create_fcurves(action, actiongroup, fcurve_name, interpolation_method, fps, frames, values, transform_indices):
    if len(frames) != 0:
        fcs = []
        for i, t_idx in enumerate(transform_indices):
            fc = action.fcurves.new(fcurve_name, index=i)
            fc.keyframe_points.add(count=len(frames))
            fc.keyframe_points.foreach_set("co",
                                           [x for co in zip([float(fps*frame + 1) for frame in frames],
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
