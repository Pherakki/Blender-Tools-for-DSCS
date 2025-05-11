from mathutils import Vector

from ..BaseOperator import BaseTransformOperator


# Parent-relative -> Bind-pose-relative
def parentspace_to_bindspace_scale_vector(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    inv_bone_axis_permutation = model_transforms.bone_axis_permutation.matrix3x3Sq_inv
    return [inv_bone_axis_permutation @ Vector(s[:3]) for s in scales]


def parentspace_to_bindspace_scale_matrix3x3(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix3x3_inv
    ba     = model_transforms.bone_axis_permutation.matrix3x3
    return [ba_inv @ s @ ba for s in scales]


def parentspace_to_bindspace_scale_matrix4x4(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix4x4_inv
    ba     = model_transforms.bone_axis_permutation.matrix4x4
    return [ba_inv @ s @ ba for s in scales]


parentspace_to_bindspace_scale = BaseTransformOperator(
    vector    =parentspace_to_bindspace_scale_vector,
    matrix3x3=parentspace_to_bindspace_scale_matrix3x3,
    matrix4x4=parentspace_to_bindspace_scale_matrix4x4)


# Bind-pose-relative -> Parent-relative
def bindspace_to_parentspace_scale_vector(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    ba = model_transforms.bone_axis_permutation.matrix3x3Sq
    return [ba @ Vector(s[:3]) for s in scales]


def bindspace_to_parentspace_scale_matrix3x3(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix3x3_inv
    ba     = model_transforms.bone_axis_permutation.matrix3x3
    return [ba @ s @ ba_inv for s in scales]


def bindspace_to_parentspace_scale_matrix4x4(scales, bone_transforms):
    model_transforms      = bone_transforms.model_transforms
    ba_inv = model_transforms.bone_axis_permutation.matrix4x4_inv
    ba     = model_transforms.bone_axis_permutation.matrix4x4
    return [ba @ s @ ba_inv for s in scales]


bindspace_to_parentspace_scale = BaseTransformOperator(
    vector    =bindspace_to_parentspace_scale_vector,
    matrix3x3=bindspace_to_parentspace_scale_matrix3x3,
    matrix4x4=bindspace_to_parentspace_scale_matrix4x4
)
