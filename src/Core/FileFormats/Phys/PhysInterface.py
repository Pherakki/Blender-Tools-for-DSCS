from .PhysBinary import PhysBinary, Ragdoll, Collider, BoxCollider, ComplexCollider


class PhysInterface:
    def __init__(self):
        self.colliders = [] # A collider
        self.materials = []
        self.bones = []
    
    @classmethod
    def from_file(cls, filepath):
        binary = PhysBinary()
        binary.read(filepath)
        return cls.from_binary(binary)
    
    def to_file(self, filepath):
        binary = self.to_binary()
        binary.write(filepath)
    
    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        
        for collider in binary.colliders:
            if collider.type == 0:
                instance.colliders.append(BoxColliderInterface.from_binary(collider.data))
            elif collider.type == 2:
                instance.colliders.append(ComplexColliderInterface.from_binary(collider.data, binary.materials, binary.bones))
            elif collider.type not in [0, 2]: 
                raise NotImplementedError(f"Unknown collider type '{collider.type}'")
            else:                             
                raise NotImplementedError(f"Invalid collider object type '{type(collider.data)}'")

        for ragdoll in binary.ragdolls:
            ri = RagdollInterface.from_binary(ragdoll)
            ci = instance.colliders[ragdoll.collider_id]
            ci.instances.append(ri)
            
        # Hack
        instance.materials = [m.rstrip(b'\x00') for m in binary.materials]
        instance.bones     = [b.rstrip(b'\x00') for b in binary.bones]
            
        return instance
            
    def to_binary(self):
        binary = PhysBinary()
        
        material_lookup = {m.ljust(0x40, b'\x00'): m_idx for m_idx, m in enumerate(self.materials)}
        bone_lookup     = {b.ljust(0x40, b'\x00'): b_idx for b_idx, b in enumerate(self.bones)}
        binary.materials = [m.ljust(0x40, b'\x00') for m in self.materials]
        binary.bones     = [b.ljust(0x40, b'\x00') for b in self.bones]
        # Order probably doesn't matter and all colliders are 1:1 with ragdolls
        # in CS anyway...
        for i, collider in enumerate(self.colliders):
            for instance in collider.instances:
                rb = instance.to_binary(i)
                binary.ragdolls.append(rb)
            
            if collider.TYPE == 2:
                local_materials = {}
                local_bones     = {}
                
                for m_idx, material in enumerate(collider.materials):
                    material = material.ljust(0x40, b'\x00')
                    if material not in material_lookup:
                        binary.materials.append(material)
                        material_lookup[material] = len(material_lookup)
                    local_materials[m_idx] = material_lookup[material]
                for b_idx, bone in enumerate(collider.bones):
                    bone = bone.ljust(0x40, b'\x00')
                    if bone not in bone_lookup:
                        binary.bones.append(bone)
                        bone_lookup[bone] = len(bone_lookup)
                    local_bones[b_idx] = bone_lookup[bone]

                cd = (collider.to_binary(local_materials, local_bones))
            else:
                cd = (collider.to_binary())
                
            col = Collider()
            col.type = collider.TYPE
            col.data = cd
            binary.colliders.append(col)
        
        binary.ragdoll_count  = len(binary.ragdolls)
        binary.collider_count = len(binary.colliders)
        binary.material_count = len(binary.materials)
        binary.bone_count     = len(binary.bones)
        
        offset = 0x38
        
        binary.ragdolls_offset = offset
        offset += 0x4C * binary.ragdoll_count
        offset += (0x08 - (offset % 0x08)) % 0x08
        
        binary.colliders_offset = offset
        offset += 0x08 * binary.collider_count
        for cb in binary.colliders:
            binary.collider_ptrs.append(offset)
            offset = cb.data.calc_offsets(offset)
        binary.materials_offset = offset
        offset += 0x40*binary.material_count
        
        binary.bones_offset = offset
        offset += 0x40 * binary.bone_count
        
        return binary
            

class ColliderInterface:
    def __init__(self):
        self.instances = []
        
    def add_instance(self, name, position, rotation, scale, unknown_vec3=None, unknown_float=None, is_solid=None):
        instance = RagdollInterface()
        instance.name = name
        instance.position = position
        instance.rotation = rotation
        instance.scale = scale
        if unknown_vec3 is not None:
            instance.unknown_vec3 = unknown_vec3
        if unknown_float is not None:
            instance.unknown_float = unknown_float
        if is_solid is not None:
            instance.is_solid = is_solid
        self.instances.append(instance)


class Triangle:
    __slots__ = ("v1", "v2", "v3", "material", "bone")
    
    def __init__(self, v1, v2, v3, material, bone):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.material = material
        self.bone = bone


class BoxColliderInterface(ColliderInterface):
    TYPE = 0
    
    def __init__(self):
        super().__init__()
        
        self.half_width  = 0.
        self.half_height = 0.
        self.half_depth  = 0.
        self.material_idx = 0
        
    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        
        instance.half_width   = binary.half_width
        instance.half_height  = binary.half_height
        instance.half_depth   = binary.half_depth
        instance.material_idx = binary.material_idx
        
        return instance
    
    def to_binary(self):
        binary = BoxCollider()
        
        binary.half_width  = self.half_width
        binary.half_height = self.half_height
        binary.half_depth  = self.half_depth
        binary.flag        = self.flag
        
        return binary
   

class ComplexColliderInterface(ColliderInterface):
    TYPE = 2
    
    def __init__(self):
        super().__init__()
        
        self.vertices  = []
        self.triangles = []
        self.materials = []
        self.bones     = []
        
    @classmethod
    def from_binary(cls, binary, phys_material_names, phys_bone_names):
        instance = cls()
        
        used_materials = {idx: i for i, idx in enumerate(sorted(set(binary.submesh_material_indices)))}
        used_bones     = {idx: i for i, idx in enumerate(sorted(set(binary.submesh_bone_indices)))}
        
        instance.vertices = binary.vertex_positions
        for tri, mat_idx, bone_idx in zip(binary.triangle_indices, binary.submesh_material_indices, binary.submesh_bone_indices):
            instance.triangles.append(Triangle(*tri, used_materials[mat_idx], used_bones[bone_idx]))
        instance.materials = [phys_material_names[idx].rstrip(b'\x00') for idx in used_materials]
        instance.bones     = [phys_bone_names    [idx].rstrip(b'\x00') for idx in used_bones]
        
        return instance

    def to_binary(self, phys_material_names, phys_bone_names):
        binary = ComplexCollider()
        
        binary.vertex_positions         = self.vertices
        binary.triangle_indices         = [(tri.v1, tri.v2, tri.v3)          for tri in self.triangles]
        binary.submesh_material_indices = [phys_material_names[tri.material] for tri in self.triangles]
        binary.submesh_bone_indices     = [phys_bone_names[tri.bone]         for tri in self.triangles]
        
        binary.vertex_count   = len(binary.vertex_positions)
        binary.triangle_count = len(binary.triangle_indices)
        binary.first_vertex_copy_1 = binary.vertex_positions[0]
        binary.first_vertex_copy_2 = binary.vertex_positions[0]
        
        return binary
    

class RagdollInterface:
    def __init__(self):
        super().__init__()
        
        self.name_bytes = None
        self.position   = None
        self.rotation   = None
        self.scale      = None
        self.unknown_vec3 = (0.20000000298023224, 0.20000000298023224, 0.6000000238418579)
        self.unknown_float = 0
        self.is_solid   = True
        
    @property
    def name(self):
        return self.name_bytes.decode('utf8')
    @name.setter
    def name(self, value):
        self.name_bytes = value.encode('utf8')

    @classmethod
    def from_binary(cls, binary):
        quat_magnitude = sum(e**2 for e in binary.scaled_quaternion)**.5
        
        instance = cls()
        instance.name_bytes    = binary.ragdoll_name.rstrip(b'\x00')
        instance.position      = binary.position
        instance.rotation      = [e/quat_magnitude for e in binary.scaled_quaternion]
        instance.scale         = quat_magnitude
        instance.unknown_vec3  = binary.unknown_vec3
        instance.unknown_float = binary.unknown_float
        instance.is_solid      = binary.is_solid
        
        return instance
    
    def to_binary(self, collider_id):
        binary = Ragdoll()
        binary.ragdoll_name      = self.name_bytes.ljust(0x18, b'\x00')
        binary.position          = self.position
        binary.scaled_quaternion = [e*self.scale for e in self.rotation]
        binary.unknown_vec3      = self.unknown_vec3
        binary.unknown_float     = self.unknown_float
        binary.is_solid          = self.is_solid
        binary.collider_id       = collider_id
        
        return binary
