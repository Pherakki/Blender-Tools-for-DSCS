import bpy
import functools
import traceback

from ..Utilities.ActionDataRetrieval import get_action_data, get_bone_name_from_fcurve, get_fcurve_type
from ..Utilities.Matrices import generate_transform_matrix


class ReportableException(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


class MessagePopup(bpy.types.Operator):
    bl_idname = "dscsblendertools.errorpopup"
    bl_label = "DSCS Blender Tools: Error Detected"
    bl_options = {'REGISTER'}

    message: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=512)

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        for substr in self.chunk_string(self.message, 80):
            col.label(text=substr)

    def chunk_string(self, string_, size):
        lines = []
        for marked_line in string_.split('\n'):
            current_length = 0
            current_bit = ""
            for word in marked_line.split(" "):
                current_length += len(word) + 1
                if (current_length) > size:
                    lines.append(current_bit)
                    current_length = len(word) + 1
                    current_bit = word + " "
                else:
                    current_bit += word + " "
            if len(current_bit):
                lines.append(current_bit)
        return lines


def handle_errors(function):
    """
    The mode of operation for this function is heavily derived from the Google-forms reporter at
    https://github.com/TheDuckCow/user-report-wrapper
    """
    @functools.wraps(function)
    def handled_execute(operator, context):
        try:
            return function(operator, context)
        except ReportableException as e:
            operator.report({'ERROR'}, "Error popup invoked: Full details printed to console.")
            print(f'Error popup invoked. Popup message:\n{e.message}\n{traceback.format_exc()}')
            bpy.ops.dscsblendertools.errorpopup('INVOKE_DEFAULT', message=e.message)
            return {'CANCELLED'}
        except Exception as e:
            raise e

    return handled_execute


def find_selected_model():
    try:
        parent_obj = bpy.context.selected_objects[0]
    except IndexError as e:
        raise ReportableException("You must select some part of the model you wish to export in Object Mode before attempting to export it. No model is currently selected.") from e
    except Exception as e:
        raise e

    # current_mode = bpy.context.object.mode
    # bpy.ops.object.mode_set("OBJECT")
    sel_obj = None
    while parent_obj is not None:
        sel_obj = parent_obj
        parent_obj = sel_obj.parent
    parent_obj = sel_obj
    if parent_obj.type != "EMPTY":
        raise ReportableException(f"An object is selected, but the top-level object \'{parent_obj.name}\' is not an Empty Axis object - has type {parent_obj.type}.")
    return parent_obj


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
    return get_first_frame_of_pose("restpose")


def get_prev_rest_pose_from_poselib():
    return get_first_frame_of_pose("prevrestpose")


def get_first_frame_of_pose(suffix):
    selected_obj = find_selected_model()
    model_armature = find_armature(selected_obj)
    obj_name = selected_obj.name
    pose_name = f"{obj_name}_{suffix}"
    rest_pose_action = bpy.data.actions[pose_name]
    model_armature.pose_library = rest_pose_action
    data = get_action_data(rest_pose_action, {'rotation_quaternion': [None, None, None, None],
                                               'location':           [None, None, None],
                                               'scale':              [None, None, None],
                                               'rotation_euler':     [None, None, None]})
    return {bone_name: generate_transform_matrix(transform['rotation_quaternion'][0.],
                                                 transform['location'][0.],
                                                 transform['scale'][0.],
                                                 WXYZ=True)
            for bone_name, transform in data.items()}


def get_all_nla_strips_for_armature(armature):
    out = []
    for nla_track in armature.animation_data.nla_tracks:
        strips = nla_track.strips
        if len(strips) != 1:
            print(f"NLA track \'{nla_track.name}\' has {len(strips)} strips; must have one strip ONLY to export.")
            continue

        nla_strip = strips[0]
        out.append(nla_strip)
    return out


def overwrite_action_data(action, fcurve_groups, animation_data):
    for bone_name, fcurve_subgroups in fcurve_groups.items():
        for curve_type, vector_fcurves in fcurve_subgroups.items():
            fcs = []
            for i, fcurve in enumerate(vector_fcurves):
                if fcurve is None:
                    # required_frames = [1.]
                    continue
                else:
                    required_frames = [kfp.co[0] for kfp in fcurve.keyframe_points]
                    assert i == fcurve.array_index
                    action.fcurves.remove(fcurve)

                local_animation_data = animation_data[bone_name][curve_type]
                fc = action.fcurves.new(f'pose.bones["{bone_name}"].{curve_type}', index=i)
                fcs.append(fc)
                fc.keyframe_points.add(count=len(required_frames))
                fc.keyframe_points.foreach_set("co",
                                               [x for co in
                                                zip([float(elem) for elem in required_frames],
                                                    [local_animation_data[elem - 1][i] for elem in required_frames]) for x in
                                                co])
                fc.lock = True
            for fc in fcs:
                fc.update()
            for fc in fcs:
                fc.lock = False

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

