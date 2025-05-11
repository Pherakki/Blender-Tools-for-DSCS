from mathutils import Quaternion
from ..BaseOperator import BaseTransformOperator


# Parent-relative -> Bind-pose-relative
def parentspace_to_bindspace_rotation_quaternion(rotations, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    inv_bind_pose_rot     = bone_transforms.rotation.quat_inv
    bone_axis_permutation = model_transforms.bone_axis_permutation.quat
    return [inv_bind_pose_rot @ Quaternion(v) @ bone_axis_permutation for v in rotations]


def parentspace_to_bindspace_rotation_matrix3x3(rotations, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    inv_bind_pose_rot = bone_transforms.rotation.matrix3x3_inv
    bone_axis_permutation  = model_transforms.bone_axis_permutation.matrix3x3
    return [inv_bind_pose_rot @ v @ bone_axis_permutation for v in rotations]


def parentspace_to_bindspace_rotation_matrix4x4(rotations, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    inv_bind_pose_rot     = bone_transforms.rotation.matrix4x4_inv
    bone_axis_permutation = model_transforms.bone_axis_permutation.matrix4x4
    return [inv_bind_pose_rot @ v @ bone_axis_permutation for v in rotations]


parentspace_to_bindspace_rotation = BaseTransformOperator(
    matrix3x3=parentspace_to_bindspace_rotation_matrix3x3,
    matrix4x4=parentspace_to_bindspace_rotation_matrix4x4,
    quat     =parentspace_to_bindspace_rotation_quaternion)


# Bind-pose-relative -> Parent-relative
def bindspace_to_parentspace_rotation_quaternion(rotations, bone_transforms):
    model_transforms          = bone_transforms.model_transforms
    bind_pose_rotation        = bone_transforms.rotation.quat
    inv_bone_axis_permutation = model_transforms.bone_axis_permutation.quat_inv
    return [bind_pose_rotation @ Quaternion(v) @ inv_bone_axis_permutation for v in rotations]


def bindspace_to_parentspace_rotation_matrix3x3(rotations, bone_transforms):
    model_transforms          = bone_transforms.model_transforms
    bind_pose_rotation        = bone_transforms.rotation.matrix3x3
    inv_bone_axis_permutation = model_transforms.bone_axis_permutation.matrix3x3_inv
    return [bind_pose_rotation @ v @ inv_bone_axis_permutation for v in rotations]


def bindspace_to_parentspace_rotation_matrix4x4(rotations, bone_transforms):
    model_transforms          = bone_transforms.model_transforms
    bind_pose_rotation        = bone_transforms.rotation.matrix4x4
    inv_bone_axis_permutation = model_transforms.bone_axis_permutation.matrix4x4_inv
    return [bind_pose_rotation @ v @ inv_bone_axis_permutation for v in rotations]


bindspace_to_parentspace_rotation = BaseTransformOperator(
    matrix3x3=bindspace_to_parentspace_rotation_matrix3x3,
    matrix4x4=bindspace_to_parentspace_rotation_matrix4x4,
    quat     =bindspace_to_parentspace_rotation_quaternion
)
