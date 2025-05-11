from mathutils import Vector
from ..BaseOperator import BaseTransformOperator


# Parent-relative -> Bind-pose-relative
def parentspace_to_bindspace_translation_additiveblend_vector(positions, bone_transforms):
    inv_bind_pose_rotation = bone_transforms.rotation.matrix3x3_inv
    return [inv_bind_pose_rotation @ (Vector(v[:3])) for v in positions]

def parentspace_to_bindspace_translation_additiveblend_matrix4x4(positions, bone_transforms):
    bind_pose_rotation        = bone_transforms.rotation.matrix4x4
    inv_bind_pose_rotation    = bone_transforms.rotation.matrix4x4_inv
    return [inv_bind_pose_rotation @ p @ bind_pose_rotation for p in positions]

parentspace_to_bindspace_translation_additiveblend = BaseTransformOperator(
    vector=parentspace_to_bindspace_translation_additiveblend_vector,
    matrix4x4=parentspace_to_bindspace_translation_additiveblend_matrix4x4
)

# Bind-pose-relative -> Parent-relative
def bindspace_to_parentspace_translation_additiveblend_vector(positions, bone_transforms):
    bind_pose_rotation    = bone_transforms.rotation.matrix3x3
    return [(bind_pose_rotation @ Vector(v[:3])) for v in positions]

def bindspace_to_parentspace_translation_additiveblend_matrix4x4(positions, bone_transforms):
    bind_pose_rotation        = bone_transforms.rotation.matrix4x4
    inv_bind_pose_rotation    = bone_transforms.rotation.matrix4x4_inv
    return [bind_pose_rotation @ p @ inv_bind_pose_rotation for p in positions]

bindspace_to_parentspace_translation_additiveblend = BaseTransformOperator(
    vector=bindspace_to_parentspace_translation_additiveblend_vector,
    matrix4x4=bindspace_to_parentspace_translation_additiveblend_matrix4x4
)
