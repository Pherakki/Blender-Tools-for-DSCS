import array

from ...serialization.Serializable import Serializable


class PhysBinary(Serializable):

    def __init__(self):
        super().__init__()
        self.context.endianness = '<'

        # Variables that appear in the file header
        self.filetype = b'PHYS'[::-1]
        self.version          = 2
        self.ragdoll_count    = 0
        self.collider_count   = 0
        self.material_count   = 0
        self.bone_count       = 0

        self.ragdolls_offset  = 0
        self.colliders_offset = 0
        self.materials_offset = 0
        self.bones_offset     = 0

        # Data
        self.ragdolls       = []
        self.collider_ptrs  = []
        self.colliders      = []
        self.materials      = None
        self.bones          = None
    
    def read_write(self, rw):
        rw.assert_file_pointer_now_at("File start", 0)

        self.filetype = rw.rw_bytestring(self.filetype, 4)
        self.version  = rw.rw_uint32(self.version)
        rw.assert_equal(self.filetype, b'PHYS'[::-1])
        rw.assert_equal(self.version, 2)
        
        self.ragdoll_count  = rw.rw_uint32(self.ragdoll_count)
        self.collider_count = rw.rw_uint32(self.collider_count)
        self.material_count = rw.rw_uint32(self.material_count)
        self.bone_count     = rw.rw_uint32(self.bone_count)

        self.ragdolls_offset  = rw.rw_uint64(self.ragdolls_offset)
        self.colliders_offset = rw.rw_uint64(self.colliders_offset)
        self.materials_offset = rw.rw_uint64(self.materials_offset)
        self.bones_offset     = rw.rw_uint64(self.bones_offset)

        # Ragdolls
        rw.assert_file_pointer_now_at("Ragdolls", self.ragdolls_offset)
        self.ragdolls = rw.rw_obj_array(self.ragdolls, Ragdoll, self.ragdoll_count)
        rw.align(rw.tell(), 0x08)
        
        # Colliders
        rw.assert_file_pointer_now_at("Colliders", self.colliders_offset)
        self.collider_ptrs = rw.rw_uint64s(self.collider_ptrs, self.collider_count)
        rw.align(rw.tell(), 0x08)
        
        if rw.mode() == "read":
            self.colliders = [Collider() for _ in range(self.collider_count)]
        for ptr, col in zip(self.collider_ptrs, self.colliders):
            rw.assert_file_pointer_now_at("Collider", ptr)
            rw.rw_obj(col)

        # Materials
        rw.assert_file_pointer_now_at("Materials", self.materials_offset)
        self.materials = rw.rw_bytestrings(self.materials, 0x40, self.material_count)
        rw.assert_file_pointer_now_at("Bones", self.bones_offset)
        self.bones = rw.rw_bytestrings(self.bones, 0x40, self.bone_count)
        

class Ragdoll(Serializable):
    def __init__(self):
        super().__init__()
        self.context.endianness = '<'

        # Variables that appear in the file header
        # Get the scaled quaternion by doing:
        #  1) Convert bone quaternion to rotation matrix
        #  2) Multiply rotation matrix by scale matrix
        #  3) Covert back to quaternion without normalising
        self.position = None
        self.scaled_quaternion = None
        self.unknown_vec3 = (0.20000000298023224, 0.20000000298023224, 0.6000000238418579)
        self.unknown_float = 0
        self.collider_id = 0
        self.unknown_flag = 0
        self.ragdoll_name = None

    def read_write(self, rw):
        self.position          = rw.rw_float32s(self.position, 3)
        self.scaled_quaternion = rw.rw_float32s(self.scaled_quaternion, 4)
        self.unknown_vec3      = rw.rw_float32s(self.unknown_vec3, 3)
        self.unknown_float     = rw.rw_float32(self.unknown_float)
        self.collider_id       = rw.rw_uint32(self.collider_id)
        self.unknown_flag      = rw.rw_uint32(self.unknown_flag)
        self.ragdoll_name      = rw.rw_bytestring(self.ragdoll_name, 0x18)


class Collider(Serializable):
    def __init__(self):
        super().__init__()
        self.context.endianness = '<'

        # Variables that appear in the file header
        self.filetype = None
        self.data = None


    def read_write(self, rw):
        self.filetype = rw.rw_uint64(self.filetype)
        
        if rw.mode() == "read":
            if   self.filetype == 0: self.data = BoxCollider()
            elif self.filetype == 2: self.data = ComplexCollider()
            else:                    raise NotImplementedError(f"Unknown collider type '{self.filetype}'")
        
        if   self.filetype == 0:          assert type(self.data) == BoxCollider
        # Type 1 appears similar to type 0 in struct size...
        elif self.filetype == 2:          assert type(self.data) == ComplexCollider
        elif self.filetype not in [0, 2]: raise NotImplementedError(f"Unknown collider type '{self.filetype}'")
        else:                             raise NotImplementedError(f"Invalid collider object type '{type(self.data)}'")

        rw.rw_obj(self.data)


class BoxCollider(Serializable):
    """
    A simple cuboid collider, defined only by its half-lengths.
    Sits at the position dictated by the Ragdoll entry it is attached to.
    """
    def __init__(self):
        super().__init__()
        self.context.endianness = '<'
        
        self.half_lengths = [0., 0., 0.]
        self.flag = 0

    def read_write(self, rw):
        self.half_lengths = rw.rw_float32s(self.half_lengths, 3)
        self.flag         = rw.rw_uint32(self.flag)


class ComplexCollider(Serializable):
    def __init__(self):
        super().__init__()
        self.context.endianness = '<'
        
        # Header
        self.vertex_count   = 0
        self.triangle_count = 0
        self.first_vertex_copy_1 = 0
        self.first_vertex_copy_2 = 0

        self.triangles_offset        = 0
        self.vertex_positions_offset = 0
        self.submesh_material_indices_offset = 0
        self.submesh_bone_indices_offset     = 0

        # Data
        self.triangle_indices = None
        self.vertex_positions = None
        self.submesh_material_indices = None
        self.submesh_bone_indices     = None

    def read_write(self, rw):
        # Header
        self.vertex_count                    = rw.rw_uint32(self.vertex_count)
        self.triangle_count                  = rw.rw_uint32(self.triangle_count)
        self.first_vertex_copy_1             = rw.rw_float32s(self.first_vertex_copy_1, 3)
        self.first_vertex_copy_2             = rw.rw_float32s(self.first_vertex_copy_2, 3)
        
        self.triangles_offset                = rw.rw_uint64(self.triangles_offset)
        self.vertex_positions_offset         = rw.rw_uint64(self.vertex_positions_offset)
        self.submesh_material_indices_offset = rw.rw_uint64(self.submesh_material_indices_offset)
        self.submesh_bone_indices_offset     = rw.rw_uint64(self.submesh_bone_indices_offset)

        # Data
        rw.assert_file_pointer_now_at("Triangles", self.triangles_offset)
        self.triangle_indices = rw.rw_uint32s(self.triangle_indices, (self.triangle_count, 3))
        
        rw.assert_file_pointer_now_at("Vertices", self.vertex_positions_offset)
        self.vertex_positions = rw.rw_float32s(self.vertex_positions, (self.vertex_count, 3))
        
        rw.assert_file_pointer_now_at("Material Indices", self.submesh_material_indices_offset)   
        self.submesh_material_indices = rw.rw_int16s(self.submesh_material_indices, self.triangle_count)
        rw.align(rw.tell(), 0x04)
        
        rw.assert_file_pointer_now_at("Bone Indices", self.submesh_bone_indices_offset)   
        self.submesh_bone_indices = rw.rw_int16s(self.submesh_bone_indices, self.triangle_count)
        rw.align(rw.tell(), 0x04)
