import numpy as np
from ...Utilities.SkeletalAnimation import generate_reference_frames, shift_animation_to_reference_frame


def export_animations(armature, model_data, reference_pose, base_animation_data):
    """
    Main entry point to the animation export functionality.

    This function gets called by the Export class and utilises the remaining functions in the
    BlenderIO/Export/ExportAnimation module.

    Creates an Animation instance in the input IntermediateFormat object ('model_data') for each NLA track in the
    animation data of the input armature.
    """

    curve_defaults = {'location': [0., 0., 0.],
                      'rotation_quaternion': [1., 0., 0., 0.],
                      'scale': [1., 1., 1.]}

    reference_frames = generate_reference_frames(reference_pose, base_animation_data)

    for nla_track in armature.animation_data.nla_tracks:
        strips = nla_track.strips
        if len(strips) != 1:
            print(f"NLA track \'{nla_track.name}\' has {len(strips)} strips; must have one strip ONLY to export.")
            continue

        print(nla_track.name)
        nla_strip = strips[0]
        fps = nla_strip.scale * 24

        animation_data = get_nla_strip_data(nla_strip, curve_defaults)

        shift_animation_to_reference_frame(reference_frames, animation_data)

        ad = model_data.new_anim(nla_track.name)
        ad.playback_rate = fps
        for bone_idx in range(len(model_data.skeleton.bone_names)):
            ad.add_rotation_fcurve(bone_idx, [], [])
            ad.add_location_fcurve(bone_idx, [], [])
            ad.add_scale_fcurve(bone_idx, [], [])
        for bone_name, data in animation_data['rotation_quaternion'].items():
            if bone_name in model_data.skeleton.bone_names:
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                # Overwrite the filler fcurve
                ad.add_rotation_fcurve(bone_idx, list(data.keys()), list(data.values()))
        for bone_name, data in animation_data['location'].items():
            if bone_name in model_data.skeleton.bone_names:
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                # Overwrite the filler fcurve
                ad.add_location_fcurve(bone_idx, list(data.keys()), list(data.values()))
        for bone_name, data in animation_data['scale'].items():
            if bone_name in model_data.skeleton.bone_names:
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                # Overwrite the filler fcurve
                ad.add_scale_fcurve(bone_idx, list(data.keys()), list(data.values()))

