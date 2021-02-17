from ...FileReaders.GeomReader import GeomReader
from .MeshInterface import MeshInterface
from .MaterialInterface import MaterialInterface
import numpy as np


class GeomInterface:
    def __init__(self):
        self.meshes = []
        self.material_data = []
        self.texture_data = []
        self.unknown_cam_data_1 = []
        self.unknown_cam_data_2 = []
        self.inverse_bind_pose_matrices = []
        self.unknown_footer_data = []

    def add_mesh(self):
        interface = MeshInterface()
        self.meshes.append(interface)
        return interface

    def add_material(self):
        interface = MaterialInterface()
        self.material_data.append(interface)
        return interface

    @classmethod
    def from_file(cls, path, platform):
        with open(path, 'rb') as F:
            readwriter = GeomReader.for_platform(F, platform)
            readwriter.read()

        new_interface = cls()
        new_interface.meshes = [MeshInterface.from_subfile(mesh) for mesh in readwriter.meshes]
        new_interface.material_data = [MaterialInterface.from_subfile(mat) for mat in readwriter.material_data]
        new_interface.texture_data = readwriter.texture_data
        new_interface.unknown_cam_data_1 = readwriter.unknown_cam_data_1
        new_interface.unknown_cam_data_2 = readwriter.unknown_cam_data_2
        new_interface.inverse_bind_pose_matrices = readwriter.inverse_bind_pose_matrices
        new_interface.unknown_footer_data = readwriter.unknown_footer_data

        return new_interface

    def to_file(self, path, platform):
        with open(path, 'wb') as F:
            geomReader = GeomReader.for_platform(F, platform)

            geomReader.filetype = 100
            geomReader.num_meshes = len(self.meshes)
            geomReader.num_materials = len(self.material_data)
            geomReader.num_unknown_cam_data_1 = len(self.unknown_cam_data_1)
            geomReader.num_unknown_cam_data_2 = len(self.unknown_cam_data_2)
            geomReader.num_bones = len(self.inverse_bind_pose_matrices)

            geomReader.num_bytes_in_texture_names_section = 32 * len(self.texture_data)

            vertices = np.array([v['Position'] for mesh in self.meshes for v in mesh.vertices])
            if len(vertices) > 0:
                minvs = np.min(vertices, axis=0)
                maxvs = np.max(vertices, axis=0)
            else:
                minvs = np.zeros(3)
                maxvs = np.zeros(3)
            assert len(maxvs) == 3

            geomReader.geom_centre = (maxvs + minvs) / 2
            geomReader.geom_bounding_box_lengths = (maxvs - minvs) / 2
            geomReader.padding_0x2C = 0

            # This generates the mesh and material subreaders that we can then populate
            geomReader.prepare_read_op()

            # Header is 112 bytes long
            virtual_pos = 112

            # Dump meshes
            geomReader.meshes_start_ptr = virtual_pos if len(self.meshes) > 0 else 0
            virtual_pos += 104 * geomReader.num_meshes
            for mesh, meshReader in zip(self.meshes, geomReader.meshes):
                virtual_pos = mesh.to_subfile(meshReader, virtual_pos)

            # Dump materials
            geomReader.materials_start_ptr = virtual_pos if len(self.material_data) > 0 else 0
            for material, materialReader in zip(self.material_data, geomReader.material_data):
                virtual_pos = material.to_subfile(materialReader, virtual_pos)

            # Dump textures
            geomReader.texture_names_start_ptr = virtual_pos if len(self.texture_data) > 0 else 0
            for texture in self.texture_data:
                geomReader.texture_data.append(texture)
                virtual_pos += 32

            # Dump unknown cam data 1
            geomReader.unknown_cam_data_1_start_ptr = virtual_pos if len(self.unknown_cam_data_1) > 0 else 0
            for elem in self.unknown_cam_data_1:
                geomReader.unknown_cam_data_1.append(elem)
                virtual_pos += 64

            # Dump unknown cam data 2
            geomReader.unknown_cam_data_2_start_ptr = virtual_pos if len(self.unknown_cam_data_2) > 0 else 0
            for elem in self.unknown_cam_data_2:
                geomReader.unknown_cam_data_2.append(elem)
                virtual_pos += 48

            # Ragged chunk fixing
            virtual_pos += (16 - (virtual_pos % 16)) % 16

            # Dump inverse bind pose matrices
            geomReader.bone_matrices_start_ptr = virtual_pos if len(self.inverse_bind_pose_matrices) > 0 else 0
            geomReader.inverse_bind_pose_matrices = self.inverse_bind_pose_matrices
            virtual_pos += geomReader.num_bones * 12 * 4

            geomReader.padding_0x58 = 0
            # Dump the footer data
            geomReader.unknown_footer_data = self.unknown_footer_data
            geomReader.footer_data_start_offset = virtual_pos if len(geomReader.unknown_footer_data) else 0
            geomReader.write()
