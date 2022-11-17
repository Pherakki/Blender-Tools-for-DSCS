import copy
import math
import os

from ....serialization.BinaryTargets import OffsetTracker
from ..GeomBinary.MeshBinary.Base import VertexAttribute, AttributeTypes
from ..GeomBinary import GeomBinaryDSCSOpenGL, GeomBinaryDSCSPS, GeomBinaryMegido72
from ..GeomBinary.MaterialBinary import MaterialBinary
from .IndexTypes import create_index_interface


class GeomInterface:
    def __init__(self):
        self.meshes = []
        self.materials = []
        self.textures = []
        self.cameras = []
        self.lights = []
        self.ibpms = []
        self.extra_clut = None

    __KEY_MAPPING = {
        "DSCS_OpenGL": GeomBinaryDSCSOpenGL,
        "DSCS_PS":   GeomBinaryDSCSPS,
        "Megido72":  GeomBinaryMegido72
    }

    @classmethod
    def from_file(cls, path, model_type):
        if model_type in cls.__KEY_MAPPING:
            binary_class = cls.__KEY_MAPPING[model_type]
        else:
            raise ValueError(f"Cannot initialise GeomInterface with the key '{model_type}'. "
                             f"Options are: {', '.join(cls.__KEY_MAPPING.keys())}")
            
        binary = binary_class()
        binary.read(path)

        shader_files = [
            f"{mb.shader_hex[0]:0>8x}_{mb.shader_hex[1]:0>8x}_{mb.shader_hex[2]:0>8x}_{mb.shader_hex[3]:0>8x}"
            for mb in binary.materials
            if all(sh != 0 for sh in mb.shader_hex)
        ]

        shaders = []
        for sf in shader_files:
            vertex_shader_path = os.path.join(os.path.dirname(path), "shaders", sf + "_vp.shad")
            fragment_shader_path = os.path.join(os.path.dirname(path), "shaders", sf + "_fp.shad")

            with open(vertex_shader_path, 'r') as F:
                vertex_shader = F.read()
            with open(fragment_shader_path, 'r') as F:
                fragment_shader = F.read()

            shaders.append((vertex_shader, fragment_shader))

        return cls.from_binary(binary, shaders)

    @classmethod
    def from_binary(cls, binary, shaders):
        instance = cls()
        instance.meshes     = [Mesh.from_binary(mb) for mb in binary.meshes]
        instance.materials  = [Material.from_binary(mb) for mb in binary.materials]
        instance.textures   = [t.rstrip(b'\x00').decode('ascii') for t in binary.textures]
        instance.cameras    = binary.cameras
        instance.lights     = binary.lights
        instance.ibpms      = binary.ibpms
        instance.extra_clut = binary.extra_clut
        return instance

    def to_file(self, filepath, model_type):
        binary = self.to_binary(model_type)
        binary.write(filepath)

    def to_binary(self, model_type):
        if model_type in self.__KEY_MAPPING:
            binary_class = self.__KEY_MAPPING[model_type]
        else:
            raise ValueError(f"Cannot serialise GeomInterface with the key '{model_type}'. "
                             f"Options are: {', '.join(self.__KEY_MAPPING.keys())}")

        binary = binary_class()
        binary.meshes     = [mi.to_binary(binary.MESH_TYPE) for mi in self.meshes]
        binary.materials  = [mi.to_binary() for mi in self.materials]
        binary.textures   = [t.encode('ascii').ljust(0x20, b'\x00') for t in self.textures]
        binary.cameras    = self.cameras
        binary.lights     = self.lights
        binary.ibpms      = self.ibpms
        binary.extra_clut = self.extra_clut

        binary.mesh_count           = len(self.meshes)
        binary.material_count       = len(self.materials)
        binary.texture_section_size = len(self.textures)*0x20
        binary.camera_count         = len(self.cameras)
        binary.light_source_count   = len(self.lights)
        binary.ibpm_count           = len(self.ibpms)

        # Geometry
        vmeshes = [m for m in binary.meshes if m.vertex_count]
        if len(vmeshes):
            maximum_coord = [c + d for c, d in zip(vmeshes[0].centre_point, vmeshes[0].bounding_box_diagonal)]
            minimum_coord = [c - d for c, d in zip(vmeshes[0].centre_point, vmeshes[0].bounding_box_diagonal)]
            for mesh in vmeshes[1:]:
                for idx in range(3):
                    maximum_coord[idx] = mesh.centre_point[idx] + mesh.bounding_box_diagonal[idx]
                    minimum_coord[idx] = mesh.centre_point[idx] - mesh.bounding_box_diagonal[idx]
            binary.centre_point          = [(mx + mn) / 2 for mx, mn in zip(maximum_coord, minimum_coord)]
            binary.bounding_box_diagonal = [(mx - mn) / 2 for mx, mn in zip(maximum_coord, minimum_coord)]
        else:
            binary.centre_point = [0., 0., 0.]
            binary.bounding_box_diagonal = [0., 0., 0.]

        # Offsets
        ot = OffsetTracker()
        ot.rw_obj_method(binary, binary.rw_header)
        if binary.mesh_count:
            binary.meshes_offset = ot.tell()
            ot.rw_obj_array(binary.meshes, binary.MESH_TYPE, binary.mesh_count)
            for mesh in binary.meshes:
                mesh.vertices_offset          = ot.tell() if mesh.vertex_count            else 0; ot.rw_obj_method(mesh, mesh.rw_VAO)
                mesh.matrix_palette_offset    = ot.tell() if mesh.matrix_palette_count    else 0; ot.rw_obj_method(mesh, mesh.rw_matrix_palette)
                mesh.indices_offset           = ot.tell() if mesh.index_count             else 0; ot.rw_obj_method(mesh, mesh.rw_IBO)
                ot.align(ot.local_tell(), 0x04)
                mesh.vertex_attributes_offset = ot.tell() if mesh.vertex_attribute_count  else 0; ot.rw_obj_method(mesh, mesh.rw_vertex_attributes)
        else:
            binary.meshes_offset = 0

        binary.materials_offset     = ot.tell() if binary.material_count         else 0; ot.rw_obj_method(binary, binary.rw_materials)
        binary.textures_offset      = ot.tell() if binary.texture_section_size   else 0; ot.rw_obj_method(binary, binary.rw_textures)
        binary.light_sources_offset = ot.tell() if binary.light_source_count     else 0; ot.rw_obj_method(binary, binary.rw_lights)
        binary.cameras_offset       = ot.tell() if binary.camera_count           else 0; ot.rw_obj_method(binary, binary.rw_cameras)
        ot.align(ot.local_tell(), 0x10)
        binary.ibpms_offset         = ot.tell() if binary.ibpm_count             else 0; ot.rw_obj_method(binary, binary.rw_ibpms)
        binary.extra_clut_offset    = ot.tell() if binary.extra_clut is not None else 0; ot.rw_obj_method(binary, binary.rw_extra_clut)
        return binary


class Mesh:
    def __init__(self):
        self.name_hash   = None
        self.flags       = None
        self.material_id = None
        self.vertices    = None
        self.indices     = None

        # To be reconstructed
        self.vertex_attributes = None
        self.bytes_per_vertex = None

    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        instance.name_hash   = binary.name_hash
        instance.flags       = binary.flags
        instance.material_id = binary.material_id
        instance.vertices    = cls.__from_binary_vertices(binary)

        ptype = binary.PRIMITIVE_TYPES[binary.primitive_type]
        dtype = binary.DATA_TYPES[binary.index_type]
        instance.indices     = create_index_interface(ptype, dtype, binary.IBO)

        instance.vertex_attributes = binary.vertex_attributes  # Needs reconstruction
        instance.bytes_per_vertex = binary.bytes_per_vertex  # Needs reconstruction
        return instance

    def to_binary(self, ctor):
        binary = ctor()

        # Main data
        binary.name_hash = self.name_hash
        binary.flags     = self.flags
        binary.material_id = self.material_id
        binary.IBO         = self.indices.buffer
        binary.vertex_attributes = self.vertex_attributes
        binary.bytes_per_vertex = self.bytes_per_vertex  # NEED TO CALCULATE
        self.__to_binary_vertices(binary, self.vertices)

        # Counts
        binary.matrix_palette_count = len(binary.matrix_palette)
        binary.vertex_attribute_count = len(binary.vertex_attributes)

        index_type = self.indices.data_type
        if index_type == "auto":
            max_size = max(self.indices.buffer)
            if max_size == 0:
                index_type = 'B'
            else:
                bitsize = math.log2(max_size)
                if bitsize < 8:
                    index_type = 'B'
                elif bitsize < 16:
                    index_type = 'H'
                elif bitsize < 32:
                    index_type = 'I'
                else:
                    raise ValueError("More than 2**32 - 1 vertices in the indices")

        dtype = {t: i for i, t in binary.DATA_TYPES.items()}[index_type]
        ptype = {t: i for i, t in binary.PRIMITIVE_TYPES.items()}[self.indices.primitive_type]
        binary.index_type     = dtype
        binary.primitive_type = ptype
        binary.vertex_count = len(self.vertices)
        binary.index_count = 0 if binary.IBO is None else len(binary.IBO)

        # Calculate geometry variables
        if len(self.vertices):
            maximum_dims = [self.vertices[0].position[0], self.vertices[0].position[1], self.vertices[0].position[2]]
            minimum_dims = [self.vertices[0].position[0], self.vertices[0].position[1], self.vertices[0].position[2]]
            for v in self.vertices[1:]:
                for idx in range(3):
                    maximum_dims[idx] = max(maximum_dims[idx], v.position[idx])
                    minimum_dims[idx] = min(minimum_dims[idx], v.position[idx])
            binary.bounding_box_diagonal = [(mx - mn) / 2 for mx, mn in zip(maximum_dims, minimum_dims)]
            binary.centre_point          = [(mx + mn) / 2 for mx, mn in zip(maximum_dims, minimum_dims)]

            maximum_distance = 0.
            centre = binary.centre_point
            for v in self.vertices:
                pos = v.position
                radial_distance = sum([(p - c)**2 for p, c in zip(pos, centre)])
                maximum_distance = max(maximum_distance, radial_distance)
            binary.bounding_sphere_radius = maximum_distance**.5
        else:
            binary.centre_point           = [0., 0., 0.]
            binary.bounding_box_diagonal  = [0., 0., 0.]
            binary.bounding_sphere_radius = [0., 0., 0.]

        # Deal with offsets later

        return binary

    @staticmethod
    def __from_binary_vertices(binary):
        vertices = binary.unpack_vertices()

        if binary.vertex_groups_per_vertex == 0:
            for v in vertices:
                v.weights = [(0, 1.0)]
        elif binary.vertex_groups_per_vertex == 1:
            for v in vertices:
                v.weights = [(int(v.position[3]), 1.0)]

        if vertices[0].weights is not None:
            for v in vertices:
                v.weights = [(binary.matrix_palette[idx // 3], wgt) for idx, wgt in v.weights]

        return vertices

    @staticmethod
    def __to_binary_vertices(binary, vertices):
        """
        Sets the vertex_groups_per_vertex and matrix_palette variables, and prepares vertices for packing.
        """
        vertices = copy.deepcopy(vertices)
        data_types = {v: k for k, v in binary.DATA_TYPES.items()}

        # Deal with position / weights
        weights_used = set(v.weights is not None and len(v.weights) > 0 for v in vertices)
        if len(weights_used) > 1:
            raise ValueError("Some vertices have at least one 'weight' value and some do not")
        if list(weights_used)[0]:
            used_indices = set()
            max_weights = 0
            for v in vertices:
                used_indices.update(set([w[0] for w in v.weights]))
                max_weights = max(max_weights, len(v.weights))

            if len(used_indices) == 1:
                # Need to think carefully about how to generate the vertex attributes
                binary.vertex_groups_per_vertex = 0
                binary.matrix_palette = list(used_indices)
                for v in vertices:
                    v.weights = None
            elif max_weights == 1:
                binary.vertex_groups_per_vertex = 1
                binary.matrix_palette = sorted(used_indices)
                idx_lookup = {idx: i*3 for i, idx in enumerate(binary.matrix_palette)}
                for v in vertices:
                    v.weights = [(idx_lookup[w[0]], w[1]) for w in v.weights]
            else:
                binary.vertex_groups_per_vertex = max_weights
                binary.matrix_palette = sorted(used_indices)
                idx_lookup = {idx: i*3 for i, idx in enumerate(binary.matrix_palette)}
                for v in vertices:
                    v.weights = [(idx_lookup[w[0]], w[1]) for w in v.weights]
                    v.weights += [(0, 0.) for _ in range(max_weights - len(v.weights))]

        binary.VAO = binary.pack_vertices(vertices)


class Material:
    def __init__(self):
        self.name_hash       = None
        self.flags           = None
        self.shader_file     = None
        self.shader_uniforms = None
        self.opengl_settings = None

    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        instance.name_hash = binary.name_hash
        instance.flags = binary.flags
        instance.shader_file = binary.shader_hex
        instance.shader_uniforms = binary.shader_uniforms
        instance.opengl_settings = binary.opengl_settings
        return instance

    def to_binary(self):
        binary = MaterialBinary()
        binary.name_hash = self.name_hash
        binary.shader_hex = self.shader_file
        binary.shader_uniform_count = len(self.shader_uniforms)
        binary.opengl_setting_count = len(self.opengl_settings)
        binary.flags = self.flags

        binary.shader_uniforms = self.shader_uniforms
        binary.opengl_settings = self.opengl_settings
        return binary