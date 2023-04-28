import math

from mathutils import Matrix, Quaternion, Vector

from .Interpolation import interpolate_keyframe_dict, lerp, slerp
from ..IOHelpersLib.Animations import ModelTransforms

upY_to_upZ_matrix = Matrix([[ 1.,  0.,  0.,  0.],
                            [ 0.,  0., -1.,  0.],
                            [ 0.,  1.,  0.,  0.],
                            [ 0.,  0.,  0.,  1.]])

boneY_to_boneX_matrix = Matrix([[ 0.,  1.,  0.,  0.],
                                [-1.,  0.,  0.,  0.],
                                [ 0.,  0.,  1.,  0.],
                                [ 0.,  0.,  0.,  1.]])

boneY_to_boneX_matrix = Matrix.Identity(4)
#upY_to_upZ_matrix = Matrix.Identity(4)

MODEL_TRANSFORMS = ModelTransforms()
MODEL_TRANSFORMS.world_rotation = upY_to_upZ_matrix
MODEL_TRANSFORMS.bone_axis_permutation = Matrix.Identity(4)

def convert_XDirBone_to_YDirBone(matrix):
    return matrix @ boneY_to_boneX_matrix

def convert_YDirBone_to_XDirBone(matrix):
    return matrix @ boneY_to_boneX_matrix.inverted()

def convert_Yup_to_Zup(matrix):
    return upY_to_upZ_matrix @ matrix

def convert_Zup_to_Yup(matrix):
    return upY_to_upZ_matrix.inverted() @ matrix

def MayaBoneToBlenderBone(matrix):
    return convert_Yup_to_Zup(convert_XDirBone_to_YDirBone(matrix))

def BlenderBoneToMayaBone(matrix):
    return convert_YDirBone_to_XDirBone(convert_Zup_to_Yup(matrix))

def decomposableToTRS(matrix, tol=0.001):
    shear_factor = abs(matrix.col[1].dot(matrix.col[2]))
    return shear_factor <= tol
