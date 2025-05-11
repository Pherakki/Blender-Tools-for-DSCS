import array
from ..Binary.HundredLine import GeomFileBinaryHundredLine
from ..Binary.HundredLine import MeshBinaryHundredLine, UnknownMeshData
from ..Binary.HundredLine import MaterialBinaryHundredLine
from ..Binary.HundredLine import NameOffsets, SkelFileBinaryHundredLine
from ..Binary.HundredLine import BoneTransforms
from ....utilities.Hash import dscs_hash
from .IndexTypes import create_index_interface, Triangles


def find_leaf_bones(parent_bones):
    leaves = set(range(len(parent_bones)))
    for p in parent_bones:
        if p in leaves:
            leaves.remove(p)
    return sorted(leaves)

def walk_bone_chain(bone_idx, parent_bones):
    out = [bone_idx]
    parent = parent_bones[bone_idx]
    while parent < 0x7FFF:
        out.append(parent)
        parent = parent_bones[parent]
    out.append(parent)
    return out[::-1]

def chains_containing(bone_idx, bone_chains):
    out = {}
    for c in bone_chains:
        if bone_idx in c:
            idx = c.index(bone_idx)
            
            if idx == (len(c) - 1):
                continue
            child_idx = c[idx+1]
            remaining_length = len(c[idx+1:])
            if child_idx not in out:
                out[child_idx] = remaining_length
            out[child_idx] = max(remaining_length, out[child_idx])
    return [(k,v) for k,v in out.items()]

def build_bone_parent_vector(input_parent_bones):
    parent_bones = [b & 0x7FFF for b in input_parent_bones]
    bone_chains = [walk_bone_chain(bone_idx, parent_bones) for bone_idx in find_leaf_bones(parent_bones)]
    vector_indices = [None for _ in range(len(parent_bones))]
    
    active_chains = chains_containing(0x7FFF, bone_chains)
    out = []
    while len(active_chains):
        active_chains = sorted(active_chains, key=lambda p: (p[1], -p[0]))
        new_chains = []
        
        num_to_parse = min(len(active_chains), 4)
        for _ in range(num_to_parse):
            bone_index, count = active_chains.pop()
            vector_indices[bone_index] = len(out)
            out.append((bone_index, input_parent_bones[bone_index]))
            new_chains.extend(chains_containing(bone_index, bone_chains))
            
        for _ in range(4-num_to_parse):
            out.append((bone_index, input_parent_bones[bone_index]))
        
        active_chains.extend(new_chains)
        
    return out, vector_indices

class BoneHundredLine:
    def __init__(self):
        self._name_bytes = None
        self.flag      = None
        self.parent    = None
        self.quat      = None
        self.pos       = None
        self.scale     = None
    
    @property
    def name(self):
        return self._name_bytes.decode('ascii')
    @name.setter
    def name(self, value):
        self._name_bytes = value.encode('ascii')
        
    def __repr__(self):
        return f"Bone({self.name}, {self.flag}, {self.parent}, {self.quat}, {self.pos}, {self.scale})"


class FloatChannelHundredLine:
    def __init__(self):
        self.name_hash   = None
        self.flags       = None
        self.array_index = None


class SkelFileHundredLine:
    def __init__(self):
        self.bones = []
        self.float_channels = []

    @property
    def bone_count(self):
        return len(self.bones)

    @property
    def float_channel_count(self):
        return len(self.float_channels)

    def add_bone(self, name_bytes, parent, flag, pos, quat, scale):
        b = BoneHundredLine()
        b._name_bytes = name_bytes
        b.parent = parent
        b.flag   = flag
        b.pos    = pos
        b.quat   = quat
        b.scale  = scale
        self.bones.append(b)

    def add_float_channel(self, name_hash, flags, array_index):
        fc = FloatChannelHundredLine()
        fc.name_hash = name_hash
        fc.flags = flags
        fc.array_index = array_index
        self.float_channels.append(fc)
        
    @classmethod
    def from_file(cls, path):
        sb = SkelFileBinaryHundredLine()
        sb.read(path)
        return cls.from_binary(sb)

    @classmethod
    def from_binary(cls, sb, name_lookup):
        instance = cls()
        instance.bones = []
        for name_hash, vector_index, transforms in zip(sb.bone_name_hashes, sb.bone_parents, sb.bone_transforms):
            parent_item = sb.bone_parent_vectors[vector_index][1]
            flag = (parent_item & 0x8000) >> 15
            parent_bone = parent_item & 0x7FFF
            if parent_bone == 0x7FFF:
                parent_bone = -1
            instance.add_bone(name_lookup[name_hash], parent_bone, flag, transforms.pos, transforms.quat.data, transforms.scale)

        for name_hash, flags, index in zip(sb.float_channel_object_name_hashes, sb.float_channel_flags, sb.float_channel_array_indices):
            instance.add_float_channel(name_hash, flags, index)

        return instance

    def to_file(self, path):
        sb = self.to_binary()
        sb.write(path)

    def to_binary(self):
        binary = SkelFileBinaryHundredLine()
        binary.bone_count          = len(self.bones)
        binary.float_channel_count = len(self.float_channels)
        
        binary.bone_name_hashes = [dscs_hash(b._name_bytes) for b in self.bones]
        binary.bone_transforms = [BoneTransforms.from_transforms(b.quat, b.pos, b.scale) for b in self.bones]
        
        parent_bones = [(b.parent if b.parent > -1 else 0x7FFF) | (b.flag << 15) for b in self.bones]
        binary.bone_parent_vectors, binary.bone_parents = build_bone_parent_vector(parent_bones)
        binary.bone_parent_pairs_count = len(binary.bone_parent_vectors)
        
        binary.float_channel_flags = [fc.flags for fc in self.float_channels]
        binary.float_channel_array_indices = [fc.array_index for fc in self.float_channels]
        binary.float_channel_object_name_hashes = [fc.name_hash for fc in self.float_channels]
        
        binary.calculate_offsets()
        
        return binary

class MeshHundredLine:
    def __init__(self):
        self._name_bytes = b""
        self.flags             = 0
        self.material_idx      = 0
        self.vertices          = []
        self.indices           = []
        self.attributes        = []
        self.unknown_mesh_data = None
        
        # Remove later
        self.bounding_sphere_radius = 0
        self.centre_point           = 0
        self.bounding_box_diagonal  = 0
        
        self.name_offset = 0
        self._name_hash   = 0
        self.matrix_palette = []
        
        
        # self._name_bytes = None
        # self.flags       = None
        # self.material_id = None
        # self.vertices    = None
        # self.indices     = None
        # self.vertex_attributes = []

    @property
    def name(self):
        return self._name_bytes.decode('ascii')
    
    @name.setter
    def name(self, value):
        self._name_bytes = value.encode('ascii')

    @classmethod
    def from_binary(cls, binary, name_bytes):
        instance = cls()
        instance._name_bytes = name_bytes
        
        instance.flags                    = binary.flags
        instance._name_hash               = binary.name_hash
        instance.name_offset              = binary.name_offset

        instance.material_idx           = binary.material_idx
        instance.bounding_sphere_radius = binary.bounding_sphere_radius
        instance.centre_point           = binary.centre_point
        instance.bounding_box_diagonal  = binary.bounding_box_diagonal
        
        
        ptype = binary.PRIMITIVE_TYPES[binary.primitive_type]
        dtype = 'H'#binary.DATA_TYPES[binary.index_type]
        instance.indices = create_index_interface(ptype, dtype, binary.index_buffer)
        
        instance.vertices          = binary.unpack_vertices()
        instance.matrix_palette    = binary.matrix_palette
        instance.attributes        = binary.attributes
        instance.unknown_mesh_data = binary.unknown_mesh_data
        
        return instance
    
    def apply_shader_transforms(self):
        if len(self.vertices[0].position) == 4:
            for v in self.vertices:
                v.indices = [int(v.position[3])]
                v.weights = [1.]
                v.position = v.position[:3]
    
    def unapply_shader_transforms(self):
        if len(self.matrix_palette) > 1 and max(len(v.indices) for v in self.vertices) == 1:
            for v in self.vertices:
                v.position = array.array('f', [*v.position, float(v.indices[0])])
                v.indices = None
                v.weights = None
    
    def calculate_bounding_volumes(self):
        # Calculate geometry variables
        # This probably needs to be done in rest-space, not bind-space.
        if len(self.vertices):
            maximum_dims = [self.vertices[0].position[0], self.vertices[0].position[1], self.vertices[0].position[2]]
            minimum_dims = [self.vertices[0].position[0], self.vertices[0].position[1], self.vertices[0].position[2]]
            for v in self.vertices[1:]:
                for idx in range(3):
                    maximum_dims[idx] = max(maximum_dims[idx], v.position[idx])
                    minimum_dims[idx] = min(minimum_dims[idx], v.position[idx])
            bounding_box_diagonal = [(mx - mn) / 2 for mx, mn in zip(maximum_dims, minimum_dims)]
            centre_point          = [(mx + mn) / 2 for mx, mn in zip(maximum_dims, minimum_dims)]

            maximum_distance = 0.
            centre = centre_point
            for v in self.vertices:
                pos = v.position
                radial_distance = sum([(p - c)**2 for p, c in zip(pos, centre)])
                maximum_distance = max(maximum_distance, radial_distance)
            bounding_sphere_radius = maximum_distance**.5
        else:
            centre_point           = [0., 0., 0.]
            bounding_box_diagonal  = [0., 0., 0.]
            bounding_sphere_radius = 0.
        
        return bounding_sphere_radius, centre_point, bounding_box_diagonal

    
    def to_binary(self):
        binary = MeshBinaryHundredLine()
        
        binary.index_buffer      = self.indices.buffer
        binary.matrix_palette    = self.matrix_palette
        binary.attributes        = [va for va in binary.get_default_vertex_attributes(self.vertices[0]).values()] if self.attributes is None else self.attributes
        binary.unknown_mesh_data = self.unknown_mesh_data
        binary.pack_vertices(self.vertices)
        
        binary.unknown_0x18             = 0
        binary.matrix_palette_count     = len(self.matrix_palette)
        binary.attribute_count          = len(self.attributes)
        binary.index_type               = 0  # Not sure if this can be changed yet
        
        if len(self.vertices):
            if len(self.vertices[0].position) == 4:
                binary.vertex_groups_per_vertex = 1
            elif self.vertices[0].indices is None:
                binary.vertex_groups_per_vertex = 0
            else:        
                binary.vertex_groups_per_vertex = max(len(v.indices) for v in self.vertices)
        
        binary.flags                    = self.flags
        binary.primitive_type           = binary.INVERSE_PRIMITIVE_TYPES[self.indices.primitive_type]
        if len(self._name_bytes) == 0: binary.name_hash = self._name_hash
        else:                          binary.name_hash = dscs_hash(self._name_bytes)
        binary.name_offset              = self.name_offset # Need to figure out the markers for these...
        binary.unknown_0x3C             = 0

        binary.material_idx = self.material_idx
        binary.vertex_count = len(self.vertices)
        binary.index_count  = len(binary.index_buffer)
        binary.unknown_0x4C = 0
        
        binary.unknown_0x50           = 0
        # Probably need to be calculated in bind-space
        binary.bounding_sphere_radius = self.bounding_sphere_radius
        binary.centre_point           = self.centre_point
        binary.bounding_box_diagonal  = self.bounding_box_diagonal
        
        return binary


class MaterialHundredLine:
    def __init__(self):
        self._name_bytes = b""
        self.line_0 = b"\x00"*56
        self.line_1 = b"\x00"*56
        self.line_2 = b"\x00"*56
        self.line_3 = b"\x00"*56
        self.line_4 = b"\x00"*56
        self.line_5 = b"\x00"*56
        self.line_6 = b"\x00"*56
        self.line_7 = b"\x00"*56
        self.line_8 = b"\x00"*56
        self.line_9 = b"\x00"*56
        self.line_10 = b"\x00"*56
        self.line_11 = b"\x00"*56
        self.line_12 = b"\x00"*56
        self.line_13 = b"\x00"*56
        
        self.unknown_0x314 = 0
        self.unknown_0x318 = 0
        self.unknown_0x31C = 0
        
        self.unknown_0x324 = 0x5A1
        self.unknown_0x326 = 0x500
        
        self.uniforms = []
        self.settings = []
    
    @property
    def name(self):
        return self._name_bytes.decode('ascii')
    
    @name.setter
    def name(self, value):
        self._name_bytes = value.encode('ascii')
    
    @classmethod
    def from_binary(cls, binary, name_bytes):
        instance = cls()
        
        instance._name_bytes = name_bytes
        instance.line_0  = binary.line_0
        instance.line_1  = binary.line_1
        instance.line_2  = binary.line_2
        instance.line_3  = binary.line_3
        instance.line_4  = binary.line_4
        instance.line_5  = binary.line_5
        instance.line_6  = binary.line_6
        instance.line_7  = binary.line_7
        instance.line_8  = binary.line_8
        instance.line_9  = binary.line_9
        instance.line_10 = binary.line_10
        instance.line_11 = binary.line_11
        instance.line_12 = binary.line_12
        instance.line_13 = binary.line_13
        
        instance.unknown_0x314 = binary.unknown_0x314
        instance.unknown_0x318 = binary.unknown_0x318 
        instance.unknown_0x31C = binary.unknown_0x31C
        
        instance.unknown_0x324 = binary.unknown_0x324
        instance.unknown_0x326 = binary.unknown_0x326
        
        instance.uniforms = binary.uniforms
        instance.settings = binary.settings
        
        return instance
    
    def to_binary(self):
        binary = MaterialBinaryHundredLine()
        
        binary.name_hash     = dscs_hash(self._name_bytes)
        binary.line_0        = self.line_0
        binary.line_1        = self.line_1
        binary.line_2        = self.line_2
        binary.line_3        = self.line_3
        binary.line_4        = self.line_4
        binary.line_5        = self.line_5
        binary.line_6        = self.line_6
        binary.line_7        = self.line_7
        binary.line_8        = self.line_8
        binary.line_9        = self.line_9
        binary.line_10       = self.line_10
        binary.line_11       = self.line_11
        binary.line_12       = self.line_12
        binary.line_13       = self.line_13
        binary.unknown_0x324 = self.unknown_0x324
        binary.unknown_0x326 = self.unknown_0x326
        
        binary.unknown_0x314 = self.unknown_0x314
        binary.unknown_0x318 = self.unknown_0x318 
        binary.unknown_0x31C = self.unknown_0x31C
        
        binary.uniform_count = len(self.uniforms)
        binary.uniforms      = self.uniforms
        binary.setting_count = len(self.settings)
        binary.settings      = self.settings
        
        return binary
    
    

class GeomFileHundredLine:
    def __init__(self):
        self.centre_point          = [0,0,0]
        self.bounding_box_diagonal = [0,0,0]
        self.padding_0x3C  = 0

        self.unknown_0x40      = 0
        self.unknown_0x44      = 0
        
        self.name_offsets    = None
        self.meshes          = []
        self.materials       = []
        self.cameras         = []
        self.lights          = []
        self.ibpms           = []
        self.extra_clut      = b''
        self.string_chunk    = b''
        self.skel            = None
        
        self.bones          = []
        self.float_channels = []
        
    @classmethod
    def from_file(cls, filepath):
        binary = GeomFileBinaryHundredLine()
        binary.read(filepath)
        return cls.from_binary(binary)
    
    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        
        instance.centre_point          = binary.centre_point
        instance.bounding_box_diagonal = binary.bounding_box_diagonal
        instance.padding_0x3C          = binary.padding_0x3C

        instance.unknown_0x40      = binary.unknown_0x40
        instance.unknown_0x44      = binary.unknown_0x44
        
        # Material Name Dictionary
        mat_hash_lookup = {}
        for mat_offset in binary.name_offsets.material_name_offsets:
            matname = binary.get_string(mat_offset)
            mathash = dscs_hash(matname)
            mat_hash_lookup[mathash] = matname
            
        bone_hash_lookup = {}
        for bone_name_offset in binary.name_offsets.bone_name_offsets:
            bone_name = binary.get_string(bone_name_offset)
            bone_hash_lookup[dscs_hash(bone_name)] = bone_name
        
        instance.name_offsets    = binary.name_offsets
        instance.meshes          = [MeshHundredLine.from_binary(m, binary.get_string(m.name_offset)) for m in binary.meshes]
        instance.materials       = [MaterialHundredLine.from_binary(m, mat_hash_lookup[m.name_hash]) for m in binary.materials]
        instance.cameras         = binary.cameras
        instance.ibpms           = binary.ibpms
        instance.extra_clut      = binary.extra_clut
        instance.string_chunk    = binary.string_chunk
        
        si = SkelFileHundredLine.from_binary(binary.skel, bone_hash_lookup)
        instance.bones          = si.bones
        instance.float_channels = si.float_channels
        
        return instance
    
    def to_file(self, filepath):
        binary = self.to_binary()
        binary.write(filepath)
    
    def to_binary(self):
        binary = GeomFileBinaryHundredLine()
        
        binary.version        = 315
        binary.mesh_count     = len(self.meshes)
        binary.material_count = len(self.materials)
        binary.light_count    = len(self.lights)
        binary.camera_count   = len(self.cameras)
        binary.ibpm_count     = len(self.ibpms)
        
        binary.unknown_0x10          = 0
        binary.centre_point          = self.centre_point
        binary.bounding_box_diagonal = self.bounding_box_diagonal
        binary.padding_0x3C          = self.padding_0x3C

        binary.unknown_0x40      = self.unknown_0x40
        binary.unknown_0x44      = self.unknown_0x44
        binary.padding_0x78      = 0
        binary.padding_0x90      = 0
        binary.padding_0xA8      = 0
        
        binary.name_offsets    = self.name_offsets
        binary.meshes          = [m.to_binary() for m in self.meshes]
        binary.materials       = [m.to_binary() for m in self.materials]
        binary.cameras         = self.cameras
        binary.ibpms           = self.ibpms
        binary.extra_clut      = self.extra_clut
        binary.string_chunk    = self.string_chunk
        
        si = SkelFileHundredLine()
        si.bones          = self.bones
        si.float_channels = self.float_channels
        binary.skel = si.to_binary()
        
        binary.calculate_offsets()
        
        # Might need to be based on the actual geometry now?
        # # Geometry
        # vmeshes = [m for m in binary.meshes if m.vertex_count]
        # if len(vmeshes):
        #     maximum_coord = [c + d for c, d in zip(vmeshes[0].centre_point, vmeshes[0].bounding_box_diagonal)]
        #     minimum_coord = [c - d for c, d in zip(vmeshes[0].centre_point, vmeshes[0].bounding_box_diagonal)]
        #     for mesh in vmeshes[1:]:
        #         for idx in range(3):
        #             maximum_coord[idx] = mesh.centre_point[idx] + mesh.bounding_box_diagonal[idx]
        #             minimum_coord[idx] = mesh.centre_point[idx] - mesh.bounding_box_diagonal[idx]
        #     binary.centre_point          = [(mx + mn) / 2 for mx, mn in zip(maximum_coord, minimum_coord)]
        #     binary.bounding_box_diagonal = [(mx - mn) / 2 for mx, mn in zip(maximum_coord, minimum_coord)]
        # else:
        #     binary.centre_point = [0., 0., 0.]
        #     binary.bounding_box_diagonal = [float('-inf'), float('-inf'), float('-inf')]
        
        return binary
