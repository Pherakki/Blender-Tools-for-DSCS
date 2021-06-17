import bpy
from mathutils import Matrix
import numpy as np


def import_skeleton(parent_obj, armature_name, model_data):
    model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    bpy.context.collection.objects.link(model_armature)
    model_armature.parent = parent_obj

    # Rig
    list_of_bones = {}

    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode='EDIT')

    bone_matrices = model_data.skeleton.inverse_bind_pose_matrices
    for i, relation in enumerate(model_data.skeleton.bone_relations):
        child, parent = relation
        child_name = model_data.skeleton.bone_names[child]
        if child_name in list_of_bones:
            continue

        bone_matrix = np.linalg.inv(bone_matrices[child])
        bone = model_armature.data.edit_bones.new(child_name)

        list_of_bones[child_name] = bone
        bone.head = np.array([0., 0., 0.])
        bone.tail = np.array([0., 0.2, 0.])  # Make this scale with the model size in the future, for convenience
        bone.transform(Matrix(bone_matrix.tolist()))

        if parent != -1:
            bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

    # Add the unknown data
    model_armature['unknown_0x0C'] = model_data.skeleton.unknown_data['unknown_0x0C']
    model_armature['unknown_data_1'] = model_data.skeleton.unknown_data['unknown_data_1']
    model_armature['unknown_data_3'] = model_data.skeleton.unknown_data['unknown_data_3']
    model_armature['unknown_data_4'] = model_data.skeleton.unknown_data['unknown_data_4']

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = parent_obj

