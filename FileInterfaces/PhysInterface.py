from ..FileReaders.PhysReader import PhysReader


class PhysInterface:
    def __init__(self):
        self.colliders = []
        self.material_names = []
        self.bone_names = []

    def add_collider(self, position, scaled_quaternion, vertex_positions, triangles, material_index, bone_index):
        self.colliders.append(
            ColliderMeshInterface(position, scaled_quaternion, vertex_positions, triangles, material_index, bone_index))

    @classmethod
    def from_file(cls, path):
        with open(path, 'rb') as F:
            physreader = PhysReader(F)
            physreader.read()

        new_phys_interface = cls()

        for ragdoll in physreader.ragdolls:
            collider = physreader.colliders[ragdoll.collider_id]
            if collider.filetype == 0:
                vertices, triangles = cls.bound_box_to_mesh(collider.data.bounding_box_corner)
                new_phys_interface.add_collider(ragdoll.position, ragdoll.scaled_quaternion, vertices, triangles, 0,
                                                ragdoll.collider_id)
            elif collider.filetype == 2:
                keys = set([(mat_id, bone_id) for mat_id, bone_id in
                            zip(collider.data.submesh_material_indices, collider.data.submesh_bone_indices)])
                keys = sorted(keys)

                polygon_groups = {key: [] for key in keys}
                for tri, mat_id, bone_id in zip(collider.data.triangle_indices, collider.data.submesh_material_indices,
                                                collider.data.submesh_bone_indices):
                    polygon_groups[(mat_id, bone_id)].append(tri)

                for (mat_id, bone_id), polylist in polygon_groups.items():
                    vertex_indices = sorted(set([idx for poly in polylist for idx in poly]))
                    id_map = {idx: i for i, idx in enumerate(vertex_indices)}

                    triangles = [[id_map[idx] for idx in poly] for poly in polylist]
                    vertices = [collider.data.vertex_positions[idx] for idx in vertex_indices]

                    new_phys_interface.add_collider(ragdoll.position, ragdoll.scaled_quaternion, vertices, triangles,
                                                    mat_id, bone_id)
            else:
                assert 0, f"Unrecognised filetype {collider.filetype}"

        new_phys_interface.material_names = physreader.material_names
        new_phys_interface.bone_names = physreader.bone_names

        return new_phys_interface

    @classmethod
    def from_model(cls, name_interface, skel_interface, geom_interface):
        new_phys_interface = cls()

        material_ids = {}
        bone_ids = {}
        for mesh in geom_interface.meshes:
            bone_idx = mesh.vertex_group_bone_idxs[0]
            mat_idx = mesh.material_id

            if bone_idx not in bone_ids:
                bone_ids[bone_idx] = len(bone_ids)
            if mat_idx not in material_ids:
                material_ids[mat_idx] = len(material_ids)

            pos = skel_interface.rest_pose[bone_idx][1][:3]
            quat = skel_interface.rest_pose[bone_idx][0]

            new_phys_interface.add_collider(pos, quat, [v["Position"] for v in mesh.vertices], mesh.polygons,
                                            material_ids[mat_idx], bone_ids[bone_idx])

        new_phys_interface.material_names = [name_interface.material_names[i] for i in material_ids.values()]
        new_phys_interface.bone_names = [name_interface.bone_names[i] for i in bone_ids.values()]

        return new_phys_interface

    def to_file(self, path):
        with open(path, 'wb') as F:
            physwriter = PhysReader(F)

            joint_colliders = {i: [] for i in range(len(self.bone_names))}
            for collider in self.colliders:
                joint_colliders[collider.bone_index].append(collider)

            physwriter.ragdoll_count = len(joint_colliders)
            physwriter.collider_count = len(joint_colliders)
            physwriter.material_names_count = len(self.material_names)
            physwriter.bone_names_count = len(self.bone_names)

            physwriter.material_names = self.material_names
            physwriter.bone_names = self.bone_names

            physwriter.init_structs()

            for i, collider_set in joint_colliders.items():
                # Complete this once you're happy you can ID simple colliders
                # if len(collider_set) == 1:
                #     collider = collider_set[0]
                #     if len(collider.vertices) == 8 and len(collider.triangles) == 12:
                #         if self.mesh_is_simple(collider.vertices):
                #             self.make_simple_mesh(i, physwriter, collider)
                #             continue
                collider_set = sorted(collider_set, key=lambda x: x.material_index)
                self.make_complex_mesh(i, physwriter, collider_set)

            virtual_pointer = 0x38
            physwriter.ragdolls_offset = virtual_pointer
            virtual_pointer += physwriter.ragdoll_count * 0x4C
            virtual_pointer += (0x08 - (virtual_pointer % 0x08)) % 0x08
            physwriter.colliders_offset = virtual_pointer
            virtual_pointer += physwriter.collider_count * 0x08
            physwriter.collider_ptrs = []
            for collider in physwriter.colliders:
                physwriter.collider_ptrs.append(virtual_pointer)

                if collider.filetype == 0:
                    virtual_pointer += 0x18
                elif collider.filetype == 2:
                    coldata = collider.data
                    virtual_pointer += 0x48
                    coldata.triangles_offset = virtual_pointer
                    virtual_pointer += coldata.triangle_count * 3 * 4
                    coldata.vertex_positions_offset = virtual_pointer
                    virtual_pointer += coldata.vertex_count * 3 * 4
                    coldata.submesh_material_indices_offset = virtual_pointer
                    virtual_pointer += coldata.triangle_count * 2 + 2 * (coldata.triangle_count % 2)
                    coldata.submesh_bone_indices_offset = virtual_pointer
                    virtual_pointer += coldata.triangle_count * 2 + 2 * (coldata.triangle_count % 2)
                else:
                    assert 0, f"Unknown filetype {physwriter.filetype}"

            physwriter.material_names_offset = virtual_pointer
            virtual_pointer += physwriter.material_names_count * 0x40
            physwriter.bone_names_offset = virtual_pointer
            virtual_pointer += physwriter.bone_names_count * 0x40

            physwriter.write()

    @staticmethod
    def make_simple_mesh(i, physwriter, collider):
        """
        UNFINISHED
        """
        ragdoll = physwriter.ragdolls[i]
        phys_collider = physwriter.colliders[i]
        bone_name = physwriter.bone_names[i]

        phys_collider.filetype = 0
        phys_collider.init_data()

        simple_mesh = phys_collider.data

    @staticmethod
    def make_complex_mesh(i, physwriter, collider_set):
        ragdoll = physwriter.ragdolls[i]
        phys_collider = physwriter.colliders[i]
        bone_name = physwriter.bone_names[i]

        phys_collider.filetype = 2
        phys_collider.init_data()

        complex_mesh = phys_collider.data
        ragdoll.position = collider_set[0].position
        ragdoll.scaled_quaternion = collider_set[0].scaled_quaternion
        ragdoll.unknown_float = 0.
        ragdoll.collider_id = i
        ragdoll.unknown_flag = 1
        prefix = "ragdoll_"
        ragdoll.ragdoll_name = bone_name[len(prefix):] if bone_name.startswith(prefix) else bone_name

        complex_mesh.triangle_count = 0
        complex_mesh.vertex_count = 0
        complex_mesh.first_vertex_copy_1 = collider_set[0].vertex_positions[0]
        complex_mesh.first_vertex_copy_2 = collider_set[0].vertex_positions[0]

        complex_mesh.triangle_indices = []
        complex_mesh.vertex_positions = []
        complex_mesh.submesh_material_indices = []
        complex_mesh.submesh_bone_indices = []

        for collider in collider_set:
            num_tris = len(collider.triangles)
            num_verts = len(complex_mesh.vertex_positions)

            complex_mesh.triangle_indices.extend([[idx + num_verts for idx in tri] for tri in collider.triangles])

            complex_mesh.vertex_positions.extend(collider.vertex_positions)
            complex_mesh.submesh_material_indices.extend([collider.material_index] * num_tris)
            complex_mesh.submesh_bone_indices.extend([collider.bone_index] * num_tris)

            complex_mesh.vertex_count += len(collider.vertex_positions)
            complex_mesh.triangle_count += num_tris

    @staticmethod
    def bound_box_to_mesh(corner):
        verts = []
        for pm1 in [-1, 1]:
            for pm2 in [-1, 1]:
                for pm3 in [1, -1]:
                    verts.append([corner[0] * pm1, corner[1] * pm2, corner[2] * pm3])

        tris = [(0, 1, 2), (2, 1, 3),
                (4, 5, 6), (6, 5, 7),
                (0, 1, 4), (4, 1, 5),
                (2, 3, 6), (6, 3, 7),
                (0, 2, 4), (4, 2, 6),
                (1, 3, 5), (5, 3, 7)]

        return verts, tris

    @staticmethod
    def mesh_is_simple(verts):
        n_parallel = [0, 0, 0]
        for vert in verts:
            v1_len = (vert[0] ** 2 + vert[1] ** 2 + vert[2] ** 2) ** .5
            for idx in range(3):
                n_parallel[idx] += (vert[idx] / v1_len) > 0.99

        return all([var == 4 for var in n_parallel])


class ColliderMeshInterface:
    def __init__(self, position, scaled_quaternion, vertex_positions, triangles, material_index, bone_index):
        self.position = position
        self.scaled_quaternion = scaled_quaternion
        self.vertex_positions = vertex_positions
        self.triangles = triangles
        self.material_index = material_index
        self.bone_index = bone_index
