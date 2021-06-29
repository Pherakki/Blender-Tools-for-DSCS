import bpy
from ..Utilities.SkeletalAnimation import get_action_data
from ..Utilities.ExportedAnimationReposingFunctions import shift_animation_by_transforms


def find_selected_model():
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set("OBJECT")
    try:
        parent_obj = bpy.context.selected_objects[0]

        sel_obj = None
        while parent_obj is not None:
            sel_obj = parent_obj
            parent_obj = sel_obj.parent
        parent_obj = sel_obj
        assert parent_obj.type == "OBJECT", f"Top-level object \'{parent_obj.name}\' is not an axis object."
        return parent_obj
    finally:
        bpy.ops.object.mode_set(current_mode)


def find_armature(parent_object):
    armatures = [item for item in parent_object.children if item.type == "ARMATURE"]
    if len(armatures) == 1:
        model_armature = armatures[0]
    elif len(armatures) > 1:
        assert 0, f"Multiple armature objects found under the axis object \'{parent_object.name}\'."
    else:
        assert 0, f"No armature objects found under the axis object \'{parent_object.name}\'."

    return model_armature


def get_rest_pose_from_poselib():
    selected_obj = find_selected_model()
    model_armature = find_armature(selected_obj)
    obj_name = selected_obj.name
    pose_name = obj_name + "_restpose"
    rest_pose_action = bpy.data.actions[pose_name]
    model_armature.pose_library = rest_pose_action
    return get_action_data(rest_pose_action, {'rotation_quaternion': [None, None, None, None],
                                              'location': [None, None, None],
                                              'scale': [None, None, None]})


def apply_transform_to_all_nonbase_nla_tracks():
    pass


def apply_transform_to_base_nla_track():
    pass