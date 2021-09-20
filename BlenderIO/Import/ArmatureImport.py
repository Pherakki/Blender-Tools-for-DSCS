import bpy
import copy
from mathutils import Matrix
import numpy as np

from ...Utilities.Matrices import decompose_matrix


def import_skeleton(parent_obj, armature_name, model_data):
    model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    bpy.context.collection.objects.link(model_armature)
    model_armature.parent = parent_obj

    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode='EDIT')

    # Rig
    list_of_bones = {}
    bone_matrices = model_data.skeleton.inverse_bind_pose_matrices
    for i, relation in enumerate(model_data.skeleton.bone_relations):
        child, parent = relation
        child_name = model_data.skeleton.bone_names[child]
        if child_name in list_of_bones:
            continue

        # This is just a complicated way of inverting the bone matrix...
        # Using bone_matrix = np.linalg.inv(bone_matrices[child]) results in an incorrect bone roll.
        # Should investigate this to do this properly, but... well, this works...
        bm = bone_matrices[child]
        pos = bm[:3, 3]
        pos *= -1
        rotation = bm[:3, :3]
        pos = np.dot(rotation.T, pos)
        bone_matrix = np.zeros((4, 4))
        bone_matrix[3, :3] = pos
        bone_matrix[:3, :3] = rotation.T
        bone_matrix[3, 3] = 1

        child_pos = pos

        bone = model_armature.data.edit_bones.new(child_name)

        list_of_bones[child_name] = bone
        bone.head = np.array([0., 0., 0.])
        bone.tail = np.array([0., 0.2, 0.])  # Make this scale with the model size in the future, for convenience
        bone.transform(Matrix(bone_matrix.tolist()))

        bone.head = np.array([0., 0., 0.]) + child_pos
        bone.tail = np.array(bone.tail) + child_pos

        if parent != -1:
            bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

    # Add the unknown data
    model_armature['unknown_0x0C'] = model_data.skeleton.unknown_data['unknown_0x0C']
    model_armature['unknown_data_1'] = model_data.skeleton.unknown_data['unknown_data_1']
    model_armature['unknown_data_3'] = model_data.skeleton.unknown_data['unknown_data_3']
    model_armature['unknown_data_4'] = model_data.skeleton.unknown_data['unknown_data_4']

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = parent_obj


def import_rest_pose_to_poselib(parent_obj, armature_name, model_data):
    model_armature = bpy.data.objects[armature_name]

    rest_pose_delta = model_data.skeleton.rest_pose_delta
    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode='POSE')

    model_armature.animation_data_create()
    model_name = armature_name[:-9]  # Cut off the letters "_armature"
    rest_pose_action = bpy.data.actions.new(model_name + "_restpose")

    for j, (bone_name, rpd) in enumerate(zip(model_data.skeleton.bone_names, rest_pose_delta)):
        actiongroup = rest_pose_action.groups.new(bone_name)
        transform = copy.deepcopy(rpd)
        transform[0] = np.roll(transform[0], 1)
        for translation_element, string_element in zip(transform,
                                                       ["rotation_quaternion", "location", "scale"]):
            fcs = []
            for i, component in enumerate(translation_element):
                fc = rest_pose_action.fcurves.new(f'pose.bones["{bone_name}"].{string_element}', index=i)
                fc.keyframe_points.insert(1, component)
                fc.group = actiongroup
                fc.lock = True
                fcs.append(fc)
            for fc in fcs:
                fc.update()
            for fc in fcs:
                fc.lock = False

    # Set the rest pose on the armature
    set_rest_pose_on_object(rest_pose_action, model_armature)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = parent_obj


def set_rest_pose_on_object(rest_pose_action, model_armature):
    model_armature.pose_library = rest_pose_action
    bpy.ops.poselib.action_sanitize()
    model_armature.pose_library.pose_markers.active_index = 0
    bpy.ops.poselib.apply_pose(0)
