from mathutils import Matrix, Vector


def freeze(transforms):
    transforms.vector.freeze()
    transforms.matrix4x4.freeze()
    transforms.matrix4x4_inv.freeze()
    
class TranslationTransforms:
    """
    A class containing multiple pre-computed representations of a translation.
    
    This class can currently only be initialised from a data structure 
    interpretable as a 4x4 matrix.
    """
    
    __slots__ = ("vector",    "vector_inv",
                 "matrix4x4", "matrix4x4_inv")
    
    def __init__(self):
        self.set_vector([0.,0.,0.])
    
    @classmethod
    def from_dynamic(cls, value):
        instance = cls()
        instance.set_dynamic(value)
        return instance
    
    def set_dynamic(self, value):
        if isinstance(value, Matrix) and len(value) == 4:
            self.set_mat4x4(value)
        elif isinstance(value, Vector):
            self.set_vector(value)
        elif hasattr(value, "__len__") and len(value) == 4 and all(hasattr(e, "__len__") and len(e)==4 for e in value):
            self.set_mat4x4(Matrix(value))
        elif hasattr(value, "__len__") and len(value) >= 3 and all((not hasattr(e, "__len__")) for e in value):
            self.set_vector(Vector(value[:3]))
        else:
            raise ValueError(f"Invalid dynamic initializer for TranslationTransforms: {value}")
    
    @classmethod
    def from_vector(cls, vector):
        instance = cls()
        instance.set_vector(vector)
        return instance
    
    def set_vector(self, vector):
        self.vector        = Vector(vector[:3])
        self.vector_inv    = -self.vector
        self.matrix4x4     = Matrix.Translation(self.vector)
        self.matrix4x4_inv = self.matrix4x4.inverted()
        freeze(self)
        
    @classmethod
    def from_mat4x4(cls, matrix4x4):
        instance = cls()
        instance.set_mat4x4(matrix4x4)
        return instance
    
    def set_mat4x4(self, matrix4x4):
        self.vector        = Matrix(matrix4x4).to_translation()
        self.vector_inv    = -self.vector
        self.matrix4x4     = Matrix.Translation(self.vector)
        self.matrix4x4_inv = self.matrix4x4.inverted()
        freeze(self)
        
