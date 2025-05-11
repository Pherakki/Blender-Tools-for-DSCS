from ..primitives import TRTransforms


def local_bind_matrix(bpy_bone, model_transforms):
    if bpy_bone.parent is not None:
        # Undo the bone axis rotation to transform the local bind pose from the
        # Blender coordinate system to that of the input data
        pre_transform = model_transforms.bone_axis_permutation.matrix4x4 @ bpy_bone.parent.matrix_local.inverted()
    else:
        # Undo the world rotation to transform the local bind pose from the
        # Blender coordinate system to that of the input data
        pre_transform = model_transforms.world_axis_rotation.matrix4x4_inv
    return pre_transform @ bpy_bone.matrix_local


class BoneTransform(TRTransforms):
    def __init__(self, bpy_bone, model_transforms):
        local_bind = local_bind_matrix(bpy_bone, model_transforms)
        t, r, s = local_bind.decompose()
        super().__init__(translation=t, rotation=r)
        self.model_transforms = model_transforms
