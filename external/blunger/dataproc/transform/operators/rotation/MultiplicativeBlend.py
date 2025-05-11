from mathutils import Quaternion
from ..BaseOperator import BaseTransformOperator


# Parent-relative -> Bind-pose-relative
def parentspace_to_bindspace_rotation_multblend_quaternion(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv           = model_transforms.bone_axis_permutation.quat_inv
    ba               = model_transforms.bone_axis_permutation.quat
    return [ba_inv @ Quaternion(v) @ ba for v in rotations]


def parentspace_to_bindspace_rotation_multblend_matrix3x3(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv           = model_transforms.bone_axis_permutation.matrix3x3_inv
    ba               = model_transforms.bone_axis_permutation.matrix3x3
    return [ba_inv @ v @ ba for v in rotations]

def parentspace_to_bindspace_rotation_multblend_matrix4x4(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv           = model_transforms.bone_axis_permutation.matrix4x4_inv
    ba               = model_transforms.bone_axis_permutation.matrix4x4
    return [ba_inv @ v @ ba for v in rotations]


parentspace_to_bindspace_rotation_multblend = BaseTransformOperator(
    matrix3x3=parentspace_to_bindspace_rotation_multblend_matrix3x3,
    matrix4x4=parentspace_to_bindspace_rotation_multblend_matrix4x4,
    quat     =parentspace_to_bindspace_rotation_multblend_quaternion
)


# Bind-pose-relative -> Parent-relative
def bindspace_to_parentspace_rotation_multblend_quaternion(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv           = model_transforms.bone_axis_permutation.quat_inv
    ba               = model_transforms.bone_axis_permutation.quat
    return [ba @ Quaternion(v) @ ba_inv for v in rotations]


def bindspace_to_parentspace_rotation_multblend_matrix3x3(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix3x3_inv
    ba     = model_transforms.bone_axis_permutation.matrix3x3
    return [ba @ v @ ba_inv for v in rotations]


def bindspace_to_parentspace_rotation_multblend_matrix4x4(rotations, bone_transforms):
    model_transforms = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix4x4_inv
    ba     = model_transforms.bone_axis_permutation.matrix4x4
    return [ba @ v @ ba_inv for v in rotations]


bindspace_to_parentspace_rotation_multblend = BaseTransformOperator(
    matrix3x3=bindspace_to_parentspace_rotation_multblend_matrix3x3,
    matrix4x4=bindspace_to_parentspace_rotation_multblend_matrix4x4,
    quat     =bindspace_to_parentspace_rotation_multblend_quaternion
)
