import math

from mathutils import Matrix, Quaternion, Vector

from .Interpolation import interpolate_keyframe_dict, lerp, slerp
from ..IOHelpersLib.Animations import ModelTransforms

upY_to_upZ_matrix = Matrix([[ 1.,  0.,  0.,  0.],
                            [ 0.,  0., -1.,  0.],
                            [ 0.,  1.,  0.,  0.],
                            [ 0.,  0.,  0.,  1.]])


MODEL_TRANSFORMS = ModelTransforms()
MODEL_TRANSFORMS.world_axis_rotation = upY_to_upZ_matrix
MODEL_TRANSFORMS.bone_axis_permutation = Matrix.Identity(4)


def decomposableToTRS(matrix, tol=0.001):
    shear_factor = abs(matrix.col[1].dot(matrix.col[2]))
    return shear_factor <= tol
