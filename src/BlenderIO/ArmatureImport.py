import bpy
import math
from mathutils import Vector, Matrix


def vec_roll_to_mat3(vec, roll):
    """
    https://blender.stackexchange.com/a/38337
    """
    target = Vector((0, 0.1, 0))
    nor = vec.normalized()
    axis = target.cross(nor)
    if axis.dot(axis) > 10**-10:
        axis.normalize()
        theta = target.angle(nor)
        bMatrix = Matrix.Rotation(theta, 3, axis)
    else:
        updown = 1 if target.dot(nor) > 0 else -1
        bMatrix = Matrix.Scale(updown, 3)
        bMatrix[2][2] = 1.0

    rMatrix = Matrix.Rotation(roll, 3, nor)
    mat = rMatrix @ bMatrix
    return mat


def mat3_to_vec_roll(mat):
    """
    https://blender.stackexchange.com/a/38337
    """
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv @ mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll


def import_skeleton(parent_obj, armature_name, ni, si, gi):
    armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    bpy.context.collection.objects.link(armature)
    armature.parent = parent_obj

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    # Rig
    bone_length = 0.2
    list_of_bones = {}
    bpms = [Matrix([[m[0], m[1],  m[2],  m[3]],
                    [m[4], m[5],  m[6],  m[7]],
                    [m[8], m[9], m[10], m[11]],
                    [  0.,   0.,    0.,    1.]]).inverted() for m in gi.ibpms]
    for i, bone in enumerate(si.bones):
        bone_name = ni.bone_names[i]
        if bone_name in list_of_bones:
            continue

        bpy_bone = armature.data.edit_bones.new(bone_name)

        list_of_bones[i] = bpy_bone
        tail, roll = mat3_to_vec_roll(bpms[i].to_3x3())
        tail *= bone_length

        pos_vector = bpms[i].to_translation()
        bpy_bone.head = pos_vector
        bpy_bone.tail = pos_vector + tail
        bpy_bone.roll = roll

        if bone.parent != -1:
            bone.parent = list_of_bones[bone.parent]

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = parent_obj

    return armature
