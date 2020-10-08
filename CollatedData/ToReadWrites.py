from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from ..FileReaders.GeomReader.MeshReader import VertexComponent


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

        skelReader.rel_ptr_to_end_of_unknown_parent_child_data = 24 + skelReader.num_unknown_parent_child_data*16
        skelReader.rel_ptr_to_end_of_bone_defs = 4 + skelReader.rel_ptr_to_end_of_unknown_parent_child_data + skelReader.num_bones*12*4
        skelReader.rel_ptr_to_end_of_parent_bones = 16 + skelReader.rel_ptr_to_end_of_bone_defs + skelReader.num_bones*2
        skelReader.rel_ptr_to_end_of_parent_bones_chunk = 4 + skelReader.rel_ptr_to_end_of_bone_defs + 0  # FIX ME
        skelReader.unknown_rel_ptr_2 = 4 + skelReader.rel_ptr_to_end_of_parent_bones + skelReader.num_bones*4
        skelReader.unknown_rel_ptr_3 = 4 + skelReader.unknown_rel_ptr_2 + skelReader.unknown_0x0C*4

        bytes_after_parent_bones_chunk = skelReader.unknown_rel_ptr_3 - skelReader.rel_ptr_to_end_of_parent_bones_chunk - 4
        bytes_after_parent_bones_chunk += (16 - (bytes_after_parent_bones_chunk % 16)) % 16

        skelReader.total_bytes = skelReader.rel_ptr_to_end_of_parent_bones_chunk + bytes_after_parent_bones_chunk
        skelReader.remaining_bytes_after_parent_bones_chunk = bytes_after_parent_bones_chunk

        skelReader.padding_0x26 = 0
        skelReader.padding_0x2A = 0
        skelReader.padding_0x2E = 0
        skelReader.padding_0x32 = 0

        skelReader.unknown_parent_child_data = model_data.skeleton.unknown_data['unknown_parent_child_data']
        skelReader.bone_data = model_data.skeleton.unknown_data['bone_data']
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
        virtual_pos = geomReader.meshes_start_ptr + 104*geomReader.num_meshes
        for mesh, meshReader in zip(model_data.meshes, geomReader.meshes):
            meshReader.vertex_data_start_ptr = virtual_pos

            meshReader.bytes_per_vertex, meshReader.vertex_components, vertex_generators = calculate_vertex_properties(mesh.vertices[0])
            meshReader.vertex_data = generate_vertex_data(mesh.vertices, vertex_generators)
            virtual_pos += meshReader.bytes_per_vertex*len(meshReader.vertex_data)
            meshReader.weighted_bone_data_start_ptr = virtual_pos
            meshReader.weighted_bone_idxs = [vgroup.bone_idx for vgroup in mesh.vertex_groups]
            virtual_pos += 4*len(meshReader.weighted_bone_idxs)
            meshReader.polygon_data_start_ptr = virtual_pos
            meshReader.polygon_data = polys_to_triangles(mesh.polygons)
            virtual_pos += 2*len(meshReader.polygon_data)
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
            meshReader.unknown_0x44 = mesh.unknown_data['unknown_0x44']
            meshReader.unknown_0x50 = mesh.unknown_data['unknown_0x50']
            meshReader.unknown_0x5C = mesh.unknown_data['unknown_0x5C']

        geomReader.materials_start_ptr = virtual_pos if len(model_data.materials) > 0 else 0
        for material, materialReader in zip(model_data.materials, geomReader.material_data):
            materialReader.unknown_0x00 = material.unknown_data['unknown_0x00']
            materialReader.unknown_0x10 = material.unknown_data['unknown_0x10']
            materialReader.unknown_0x11 = material.unknown_data['unknown_0x11']
            materialReader.unknown_0x12 = material.unknown_data['unknown_0x12']
            materialReader.unknown_0x16 = material.unknown_data['unknown_0x16']

            for key in material.unknown_data:
                if 'type_1_component_' in key:
                    materialReader.unknown_data.append(material.unknown_data[key])
                    virtual_pos += 24
            for key in material.unknown_data:
                if 'type_2_component_' in key:
                    materialReader.unknown_data.append(material.unknown_data[key])
                    virtual_pos += 24

            materialReader.num_material_components = len(materialReader.material_components)
            materialReader.num_unknown_data = len(materialReader.unknown_data)

            virtual_pos += 24

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
                                                      model_data.skeleton.bone_xvecs,
                                                      model_data.skeleton.bone_yvecs,
                                                      model_data.skeleton.bone_zvecs,
                                                      geomReader.bone_data):
            boneReader.unknown_0x00, boneReader.unknown_0x04, boneReader.unknown_0x08 = xvec
            boneReader.unknown_0x0C, boneReader.unknown_0x10, boneReader.unknown_0x14 = yvec
            boneReader.unknown_0x1A, boneReader.unknown_0x1E, boneReader.unknown_0x22 = zvec
            boneReader.xpos, boneReader.ypos, boneReader.zpos = [-item for item in bone]
        virtual_pos += geomReader.num_bones*12*4

        geomReader.padding_0x58 = 0

        geomReader.texture_names_start_ptr = virtual_pos if len(model_data.textures) > 0 else 0
        for texture in model_data.textures:
            geomReader.texture_data.append(texture.name)
            virtual_pos += 32

        geomReader.footer_data_start_offset = virtual_pos
        geomReader.unknown_footer_data = model_data.unknown_data['unknown_footer_data']


def calculate_vertex_properties(example_vertex):
    """
    Contains some nasty repetition of non-trivial data but I just want to get this done at this point
    """
    bytes_per_vertex = 0
    vertex_components = []
    vertex_generators = []
    if example_vertex.position is not None:
        vertex_components.append(VertexComponent([1, 3, 6, 20, bytes_per_vertex]))
        bytes_per_vertex += 12
        vertex_generators.append(lambda vtx: {'Position': vtx.position})
    if example_vertex.normal is not None:
        vertex_components.append(VertexComponent([2, 3, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'Normal': vtx.normal})
    if example_vertex.UV is not None:
        vertex_components.append(VertexComponent([3, 2, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 4
        vertex_generators.append(lambda vtx: {'UV': vtx.UV})
    if 'UnknownVertexUsage1' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([4, 4, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage1': vtx.unknown_data['UnknownVertexUsage1']})
    if 'UnknownVertexUsage2' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent([5, 3, 11, 20, bytes_per_vertex]))
        bytes_per_vertex += 8
        vertex_generators.append(lambda vtx: {'UnknownVertexUsage2': vtx.unknown_data['UnknownVertexUsage2']})
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
        vertex_components.append(VertexComponent([10, len(example_vertex.vertex_groups), 1, 20, bytes_per_vertex]))
        nominal_bytes = len(example_vertex.vertex_groups)
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)
        vertex_generators.append(lambda vtx: {'WeightedBoneID': [grp*3 for grp in vtx.vertex_groups]})

        vertex_components.append(VertexComponent([11, len(example_vertex.vertex_groups), 1, 20, bytes_per_vertex]))
        nominal_bytes = 2*len(example_vertex.vertex_groups)
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)
        vertex_generators.append(lambda vtx: {'BoneWeight': vtx.vertex_group_weights})

    return bytes_per_vertex, vertex_components, vertex_generators


def generate_vertex_data(vertices, generators):
    retval = []
    for vertex in vertices:
        vdata = [generator(vertex) for generator in generators]
        retval.append({k: v for d in vdata for k, v in d.items()})
    return retval


def polys_to_triangles(polys):
    return [sublist for list in [poly.indices for poly in polys] for sublist in list]
