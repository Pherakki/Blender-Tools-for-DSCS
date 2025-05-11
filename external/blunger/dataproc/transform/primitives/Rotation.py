import numpy as np
from mathutils import Matrix, Quaternion


basis_vector_lookup_table = {
    'X': np.array([1, 0, 0]),
    '-X': np.array([-1, 0, 0]),
    'Y': np.array([0, 1, 0]),
    '-Y': np.array([0, -1, 0]),
    'Z': np.array([0, 0, 1]),
    '-Z': np.array([0, 0, -1])
}


_valid_axis_set = set(('X', 'Y', 'Z'))

def parse_axis_string(axis_string):
    whitespace = set([" ", "_"])
    out = []
    negatives = 0
    for c in axis_string:
        if c == '-':
            negatives += 1
        elif c in whitespace:
            pass
        else:
            out.append((negatives % 2)*"-" + c)
            negatives = 0
    return out


def create_axis_permutation(right, up, forwards):
    # Validate inputs
    for varname, var in [("right", right), ("up", up), ("forwards", forwards)]:
        if var not in basis_vector_lookup_table:
            valid_keys = list(basis_vector_lookup_table.keys())
            raise ValueError(f"Invalid {varname}-axis '{var}', expected a string in {valid_keys}")
    if set((v[-1] for v in (right, up, forwards))) != _valid_axis_set:
        raise ValueError(f"Cannot construct matrix from degenerate axes '{right}', '{up}', '{forwards}' - inputs must be a (signed) permutation of 'X', 'Y', and 'Z'")
    
    # Create rotation matrix
    out = np.empty((3, 3), dtype=np.float64)
    out[:, 0] = basis_vector_lookup_table[right]
    out[:, 1] = basis_vector_lookup_table[up]
    out[:, 2] = basis_vector_lookup_table[forwards]
    return Matrix(out).to_4x4()

def freeze(transforms):
    transforms.matrix4x4.freeze()
    transforms.matrix4x4_inv.freeze()
    transforms.matrix3x3.freeze()
    transforms.matrix3x3_inv.freeze()
    transforms.matrix3x3Sq.freeze()
    transforms.matrix3x3Sq_inv.freeze()
    transforms.quat.freeze()
    transforms.quat_inv.freeze()


class RotationTransforms:
    """
    A class containing multiple pre-computed representations of a rotation to 
    prevent unnecessary work.
    """
    
    __slots__ = ("matrix3x3",   "matrix3x3_inv",
                 "matrix3x3Sq", "matrix3x3Sq_inv",
                 "matrix4x4",   "matrix4x4_inv",
                 "quat",        "quat_inv")
    
    def __init__(self):
        self.matrix4x4       = Matrix.Identity(4)
        self.matrix4x4_inv   = Matrix.Identity(4)
        self.matrix3x3       = Matrix.Identity(3)
        self.matrix3x3_inv   = Matrix.Identity(3)
        self.matrix3x3Sq     = Matrix.Identity(3)
        self.matrix3x3Sq_inv = Matrix.Identity(3)
        self.quat            = Quaternion()
        self.quat_inv        = Quaternion()
    
    @classmethod
    def from_dynamic(cls, value):
        instance = cls()
        instance.set_dynamic(value)
        return instance
    
    def set_dynamic(self, value):
        if isinstance(value, Matrix) and len(value) == 3:
            self.set_mat3x3(value)
        elif isinstance(value, Matrix) and len(value) == 4:
            self.set_mat4x4(value)
        elif isinstance(value, Quaternion):
            self.set_quat(value)
        elif isinstance(value, str):
            self.set_initializer(value)
        elif hasattr(value, "__iter__") and all(isinstance(e, str) for e in value):
            self.set_initializer(value)
        else:
            raise ValueError(f"Invalid dynamic initializer for RotationTransforms: {value}")

    @classmethod
    def from_initializer(cls, initializer):
        instance = cls()
        instance.set_initializer(initializer)
        return instance
    
    def set_initializer(self, initializer):
        initializer = parse_axis_string(initializer)
        
        if len(initializer) != 3:
            raise ValueError(f"Received an axis permutation string containing {len(initializer)} axes ({', '.join(initializer)}), expected 3 axes")
        
        self.set_mat4x4(create_axis_permutation(*initializer))
    
    @classmethod
    def from_mat3x3(cls, matrix3x3):
        instance = cls()
        instance.set_mat3x3(matrix3x3)
        return instance
    
    def set_mat3x3(self, matrix3x3):
        self.matrix4x4       = matrix3x3.to_4x4()
        self.matrix4x4_inv   = self.matrix4x4.transposed()
        self.matrix3x3       = matrix3x3
        self.matrix3x3_inv   = self.matrix3x3.transposed()
        self.matrix3x3Sq     = Matrix(np.array(self.matrix3x3)**2)
        self.matrix3x3Sq_inv = self.matrix3x3Sq.transposed()
        self.quat            = self.matrix3x3.to_quaternion()
        self.quat_inv        = self.quat.inverted()
        freeze(self)
        
    @classmethod
    def from_mat4x4(cls, matrix4x4):
        instance = cls()
        instance.set_mat4x4(matrix4x4)
        return instance
        
    def set_mat4x4(self, matrix4x4):
        self.matrix4x4       = Matrix(matrix4x4)
        self.matrix4x4_inv   = self.matrix4x4.transposed()
        self.matrix3x3       = self.matrix4x4.to_3x3()
        self.matrix3x3_inv   = self.matrix3x3.transposed()
        self.matrix3x3Sq     = Matrix(np.array(self.matrix3x3)**2)
        self.matrix3x3Sq_inv = self.matrix3x3Sq.transposed()
        self.quat            = self.matrix3x3.to_quaternion()
        self.quat_inv        = self.quat.inverted()
        freeze(self)
        
    @classmethod
    def from_quat(cls, quat):
        instance = cls()
        instance.set_quat(quat)
        return instance
    
    def set_quat(self, quat):
        self.quat            = Quaternion(quat)
        self.quat_inv        = self.quat.inverted()
        self.matrix3x3       = self.quat.to_matrix()
        self.matrix3x3_inv   = self.matrix3x3.transposed()
        self.matrix3x3Sq     = Matrix(np.array(self.matrix3x3)**2)
        self.matrix3x3Sq_inv = self.matrix3x3Sq.transposed()
        self.matrix4x4       = self.matrix3x3.to_4x4()
        self.matrix4x4_inv   = self.matrix4x4.transposed()
        freeze(self)
    
