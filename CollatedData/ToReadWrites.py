from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from ..FileReaders.GeomReader.MeshReader import VertexComponent
from ..FileReaders.GeomReader.MaterialReader import MaterialComponent, UnknownMaterialData
import numpy as np


def generate_files_from_intermediate_format(filepath, model_data):
    make_namereader(filepath, model_data)
    make_skelreader(filepath, model_data)
    make_geomreader(filepath, model_data)


def make_namereader(filepath, model_data):
    bone_names = model_data.skeleton.bone_names
    material_names = model_data.unknown_data['material names']

    with open(filepath + ".name", 'wb') as F:
        nameReader = NameReader(F)

        nameReader.num_bone_names = len(bone_names)
        nameReader.num_material_names = len(material_names)

        num_ptrs = len(bone_names) + len(material_names)
        nameReader.bone_name_pointers = [8 + 4*num_ptrs + sum([len(name) for name in bone_names[:i]])
                                         for i in range(len(bone_names))]

        nameReader.material_name_pointers = [nameReader.bone_name_pointers[-1] + len(bone_names[-1]) +
                                         sum([len(name) for name in material_names[:i]])
                                         for i in range(len(material_names))]
        nameReader.bone_names = bone_names
        nameReader.material_names = material_names

        nameReader.write()


def make_skelreader(filepath, model_data):
    with open(filepath + '.skel', 'wb') as F:
        skelReader = SkelReader(F)

        skelReader.filetype = '20SE'
        skelReader.num_bones = len(model_data.skeleton.unknown_data['bone_data'])
        skelReader.unknown_0x0C = model_data.skeleton.unknown_data['unknown_0x0C']
        skelReader.num_unknown_parent_child_data = len(model_data.skeleton.unknown_data['unknown_parent_child_data'])

        # Just give up and make the absolute pointers
        skelReader.rel_ptr_to_end_of_unknown_parent_child_data = 40 + skelReader.num_unknown_parent_child_data*16
        skelReader.rel_ptr_to_end_of_bone_defs = skelReader.rel_ptr_to_end_of_unknown_parent_child_data + skelReader.num_bones*12*4 - 4
        skelReader.rel_ptr_to_end_of_parent_bones = skelReader.rel_ptr_to_end_of_bone_defs + skelReader.num_bones*2 - 16
        abs_end_of_parent_bones_chunk = skelReader.rel_ptr_to_end_of_parent_bones + skelReader.unknown_0x0C + 44

        skelReader.rel_ptr_to_end_of_parent_bones_chunk = skelReader.rel_ptr_to_end_of_parent_bones + skelReader.unknown_0x0C + 12
        skelReader.rel_ptr_to_end_of_parent_bones_chunk += (16 - ((abs_end_of_parent_bones_chunk) % 16)) % 16
        skelReader.unknown_rel_ptr_2 = skelReader.rel_ptr_to_end_of_parent_bones_chunk + skelReader.num_bones*4 - 4
        skelReader.unknown_rel_ptr_3 = skelReader.unknown_rel_ptr_2 + skelReader.unknown_0x0C*4 - 4

        bytes_after_parent_bones_chunk = (skelReader.unknown_rel_ptr_3 + 40) - (skelReader.rel_ptr_to_end_of_parent_bones_chunk + 32)
        bytes_after_parent_bones_chunk += (16 - (bytes_after_parent_bones_chunk % 16))

        skelReader.total_bytes = skelReader.rel_ptr_to_end_of_parent_bones_chunk + bytes_after_parent_bones_chunk + 32
        skelReader.remaining_bytes_after_parent_bones_chunk = bytes_after_parent_bones_chunk

        skelReader.padding_0x26 = 0
        skelReader.padding_0x2A = 0
        skelReader.padding_0x2E = 0
        skelReader.padding_0x32 = 0

        skelReader.unknown_parent_child_data = model_data.skeleton.unknown_data['unknown_parent_child_data']
        skelReader.bone_rotation_quaternions_xyz = model_data.skeleton.unknown_data['bone_data']
        skelReader.parent_bones = model_data.skeleton.bone_relations
        skelReader.unknown_data_1 = model_data.skeleton.unknown_data['unknown_data_1']
        skelReader.unknown_data_2 = model_data.skeleton.unknown_data['unknown_data_2']
        skelReader.unknown_data_3 = model_data.skeleton.unknown_data['unknown_data_3']
        skelReader.unknown_data_4 = model_data.skeleton.unknown_data['unknown_data_4']

        skelReader.write()


def make_geomreader(filepath, model_data):
    with open(filepath + '.geom', 'wb') as F:
        geomReader = GeomReader(F)

        geomReader.filetype = 100
        geomReader.num_meshes = len(model_data.meshes)
        geomReader.num_materials = len(model_data.materials)
        geomReader.num_unknown_cam_data_1 = len(model_data.unknown_data['unknown_cam_data_1'])
        geomReader.num_unknown_cam_data_2 = len(model_data.unknown_data['unknown_cam_data_2'])
        geomReader.num_bones = len(model_data.skeleton.bone_positions)

        geomReader.num_bytes_in_texture_names_section = 32*len(model_data.textures)
        geomReader.unknown_0x14 = model_data.unknown_data['geom_unknown_0x14']
        geomReader.unknown_0x20 = model_data.unknown_data['geom_unknown_0x20']
        geomReader.padding_0x2C = 0

        geomReader.prepare_read_op()
        virtual_pos = 112
        geomReader.meshes_start_ptr = virtual_pos if len(model_data.meshes) > 0 else 0
        virtual_pos += 104*geomReader.num_meshes
        for mesh, meshReader in zip(model_data.meshes, geomReader.meshes):
            meshReader.vertex_data_start_ptr = virtual_pos

            vgroup_idxs = sorted([vgroup.bone_idx for vgroup in mesh.vertex_groups])
            meshReader.bytes_per_vertex, meshReader.vertex_components, vertex_generators = calculate_vertex_properties(mesh.vertices, vgroup_idxs)
            meshReader.vertex_data = generate_vertex_data(mesh.vertices, vertex_generators)

            virtual_pos += meshReader.bytes_per_vertex*len(meshReader.vertex_data)
            meshReader.weighted_bone_data_start_ptr = virtual_pos
            meshReader.weighted_bone_idxs = vgroup_idxs
            virtual_pos += 4*len(meshReader.weighted_bone_idxs)
            meshReader.polygon_data_start_ptr = virtual_pos
            meshReader.polygon_data = polys_to_triangles(mesh.polygons)
            virtual_pos += 2*len(meshReader.polygon_data)
            virtual_pos += (4 - (virtual_pos % 4)) % 4  # Fix ragged chunk of size 4
            meshReader.padding_0x18 = 0

            meshReader.vertex_components_start_ptr = virtual_pos
            virtual_pos += 8*len(meshReader.vertex_components)
            meshReader.num_weighted_bone_idxs = len(meshReader.weighted_bone_idxs)
            meshReader.num_vertex_components = len(meshReader.vertex_components)
            meshReader.always_5123 = 5123

            meshReader.unknown_0x30 = mesh.unknown_data['unknown_0x30']
            meshReader.unknown_0x31 = mesh.unknown_data['unknown_0x31']
            meshReader.polygon_numeric_data_type = 4  # Can only write to triangles atm
            meshReader.unknown_0x34 = mesh.unknown_data['unknown_0x34']
            meshReader.unknown_0x36 = mesh.unknown_data['unknown_0x36']
            meshReader.material_id = mesh.material_id
            meshReader.num_vertices = len(meshReader.vertex_data)

            meshReader.num_polygon_idxs = len(meshReader.polygon_data)
            meshReader.padding_0x44 = 0
            meshReader.padding_0x48 = 0
            meshReader.unknown_0x5A = mesh.unknown_data['unknown_0x5A']

            vertices = np.array([v.position for v in mesh.vertices])
            minvs = np.min(vertices, axis=0)
            maxvs = np.max(vertices, axis=0)

            meshReader.mesh_centre = (maxvs + minvs)/2
            meshReader.bounding_box_lengths = (maxvs - minvs)/2

        geomReader.materials_start_ptr = virtual_pos if len(model_data.materials) > 0 else 0
        for material, materialReader in zip(model_data.materials, geomReader.material_data):
            materialReader.unknown_0x00 = material.unknown_data['unknown_0x00']
            materialReader.unknown_0x02 = material.unknown_data['unknown_0x02']
            materialReader.shader_hex = material.shader_hex
            materialReader.unknown_0x16 = material.unknown_data['unknown_0x16']

            for key in material.unknown_data:
                if 'type_1_component_' in key:
                    n_component = int(key[len('type_1_component_'):])
                    material_component = material.unknown_data[key]
                    mData = MaterialComponent(F)
                    mData.data = material_component
                    mData.component_type = n_component
                    mData.num_floats_in_data = MaterialComponent.component_types[n_component][1]
                    mData.always_65280 = 65280
                    mData.padding_0x14 = 0

                    materialReader.material_components.append(mData)
                    virtual_pos += 24
            for key in material.unknown_data:
                if 'type_2_component_' in key:
                    n_component = int(key[len('type_2_component_'):])
                    unknown_material_component = material.unknown_data[key]
                    unknown_mData = UnknownMaterialData(F)
                    unknown_mData.data = unknown_material_component
                    unknown_mData.padding_0x08 = 0
                    unknown_mData.padding_0x0A = 0
                    unknown_mData.padding_0x0C = 0
                    unknown_mData.padding_0x0E = 0
                    unknown_mData.maybe_component_type = n_component
                    unknown_mData.always_100 = 100
                    unknown_mData.always_65280 = 65280
                    unknown_mData.padding_0x14 = 0

                    materialReader.unknown_data.append(unknown_mData)
                    virtual_pos += 24

            materialReader.num_material_components = len(materialReader.material_components)
            materialReader.num_unknown_data = len(materialReader.unknown_data)

            virtual_pos += 24

        geomReader.texture_names_start_ptr = virtual_pos if len(model_data.textures) > 0 else 0
        for texture in model_data.textures:
            geomReader.texture_data.append(texture.name)
            virtual_pos += 32

        geomReader.unknown_cam_data_1_start_ptr = virtual_pos if len(model_data.unknown_data['unknown_cam_data_1']) > 0 else 0
        for elem in model_data.unknown_data['unknown_cam_data_1']:
            geomReader.unknown_cam_data_1.append(elem)
            virtual_pos += 64

        geomReader.unknown_cam_data_2_start_ptr = virtual_pos if len(model_data.unknown_data['unknown_cam_data_2']) > 0 else 0
        for elem in model_data.unknown_data['unknown_cam_data_2']:
            geomReader.unknown_cam_data_2.append(elem)
            virtual_pos += 48

        # Ragged chunk fixing
        virtual_pos += (16 - (virtual_pos % 16)) % 16

        geomReader.bone_data_start_ptr = virtual_pos if len(model_data.skeleton.bone_positions) > 0 else 0
        for bone, xvec, yvec, zvec, boneReader in zip(model_data.skeleton.bone_positions,
                                                      model_data.skeleton.bone_xaxes,
                                                      model_data.skeleton.bone_yaxes,
                                                      model_data.skeleton.bone_zaxes,
                                                      geomReader.bone_data):
            boneReader.x_axis = xvec
            boneReader.y_axis = yvec
            boneReader.z_axis = zvec
            boneReader.xpos, boneReader.ypos, boneReader.zpos = [-item for item in bone]
        virtual_pos += geomReader.num_bones*12*4

        geomReader.padding_0x58 = 0

        geomReader.footer_data_start_offset = virtual_pos
        geomReader.unknown_footer_data = model_data.unknown_data['unknown_footer_data']

        geomReader.write()


def calculate_vertex_properties(vertices, all_bones_used_by_vertices):
    """
    Contains some nasty repetition of non-trivial data but I just want to get this done at this point
    """
    bytes_per_vertex = 0
    vertex_components = []
    vertex_generators = []
    example_vertex = vertices[0]
    if example_vertex.position is not None:
        vertex_components.append(VertexComponent([1, 3, 6, 20, bytes_per_vertex]))
        bytes_per_vertex += 12
        vertex_generators.append(lambda vtx: {'Position': vtx.position})
    if example_vertex.normal is not None:
        vertex_components.append(VertexComponent([2, 3, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'Normal': vtx.normal})
    if 'UnknownVertexUsage1' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([3, 4, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage1': vtx.unknown_data['UnknownVertexUsage1']})
    if 'UnknownVertexUsage2' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([4, 3, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage2': vtx.unknown_data['UnknownVertexUsage2']})
    if example_vertex.UV is not None:
        vertex_components.append(VertexComponent([5, 2, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 4
        vertex_generators.append(lambda vtx: {'UV': (vtx.UV[0], 1 - vtx.UV[-1]) if vtx.UV is not None else vtx.UV})
    if 'UnknownVertexUsage3' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([6, 2, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 4
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage3': vtx.unknown_data['UnknownVertexUsage3']})
    if 'UnknownVertexUsage4' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([7, 2, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 4
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage4': vtx.unknown_data['UnknownVertexUsage4']})
    if 'UnknownVertexUsage5' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([9, 4, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage5': vtx.unknown_data['UnknownVertexUsage5']})
    if example_vertex.vertex_groups is not None:
        num_grps = max(max([len(vtx.vertex_groups) for vtx in vertices]), 2)
        vertex_components.append(VertexComponent([10, num_grps, 1, 20, bytes_per_vertex]))
        nominal_bytes = num_grps
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)
        vertex_generators.append(lambda vtx: {'WeightedBoneID': mk_extended_boneids(vtx, num_grps, None)})

        vertex_components.append(VertexComponent([11, num_grps, 11, 20, bytes_per_vertex]))
        nominal_bytes = 2*num_grps
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)
        vertex_generators.append(lambda vtx: {'BoneWeight': mk_extended_boneweights(vtx, num_grps)})

    return bytes_per_vertex, vertex_components, vertex_generators


def generate_vertex_data(vertices, generators):
    retval = []
    for vertex in vertices:
        vdata = [generator(vertex) for generator in generators]
        retval.append({k: v for d in vdata for k, v in d.items()})
    return retval


def polys_to_triangles(polys):
    return [sublist for list in [poly.indices for poly in polys] for sublist in list]


def mk_extended_boneids(vtx, num_grps, all_bones_used_by_vertices):
    use_groups = [grp*3 for grp in vtx.vertex_groups]
    if len(vtx.vertex_groups) < num_grps:
        use_groups.extend([0]*(num_grps-len(vtx.vertex_groups)))
    return use_groups


def mk_extended_boneweights(vtx, num_grps):
    use_groups = [grp for grp in vtx.vertex_group_weights]
    if len(vtx.vertex_group_weights) < num_grps:
        use_groups.extend([0.]*(num_grps-len(vtx.vertex_group_weights)))
    return use_groups
