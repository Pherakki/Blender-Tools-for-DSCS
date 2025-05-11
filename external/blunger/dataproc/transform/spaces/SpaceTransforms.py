from mathutils import Matrix
from ..primitives import RotationTransforms


class ModelTransforms:
    __slots__ = ("_world_axis_rotation",
                 "_bone_axis_permutation")
    
    def __init__(self, world_axis, bone_axis):
        self._world_axis_rotation   = RotationTransforms.from_dynamic(world_axis)
        self._bone_axis_permutation = RotationTransforms.from_dynamic(bone_axis)

    @property
    def world_axis_rotation(self):
        return self._world_axis_rotation
    
    @world_axis_rotation.setter
    def world_axis_rotation(self, value):
        self._world_axis_rotation.set_dynamic(value)
    
    @property
    def bone_axis_permutation(self):
        return self._bone_axis_permutation
    
    @bone_axis_permutation.setter
    def bone_axis_permutation(self, value):
        self._bone_axis_permutation.set_dynamic(value)
        
    def transform_bone_matrix4x4(self, matrix):
        return self.world_axis_rotation.matrix4x4 @ matrix @ self.bone_axis_permutation.matrix4x4
    
    def transform_object_matrix3x3(self, matrix):
        return self.world_axis_rotation.matrix3x3 @ matrix
    
    def transform_object_matrix4x4(self, matrix):
        return self.world_axis_rotation.matrix4x4 @ matrix


NULL_TRANSFORM = ModelTransforms(Matrix.Identity(4), Matrix.Identity(4))
