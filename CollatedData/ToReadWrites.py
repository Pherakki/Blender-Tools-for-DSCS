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

        nameReader.bone_name_pointers = [8 + sum([len(name) for name in bone_names[:i]])
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
        skelReader.rel_ptr_to_end_of_parent_bones_chunk = 4 + skelReader.rel_ptr_to_end_of_bone_defs + 0  # FIX ME
        skelReader.unknown_rel_ptr_2 = 4 + skelReader.rel_ptr_to_end_of_parent_bones + skelReader.num_bones*4
        skelReader.unknown_rel_ptr_3 = 4 + skelReader.unknown_rel_ptr_2 + skelReader.unknown_0x0C*4
        skelReader.rel_ptr_to_end_of_parent_bones = 16 + skelReader.rel_ptr_to_end_of_bone_defs + skelReader.num_bones*2

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
        skelReader.parent_bones_junk = model_data.skeleton.unknown_data['parent_bones_junk']
        skelReader.unknown_data_2 = model_data.skeleton.unknown_data['unknown_data_2']
        skelReader.unknown_data_3 = model_data.skeleton.unknown_data['unknown_data_3']
        skelReader.unknown_data_4 = model_data.skeleton.unknown_data['unknown_data_4']


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
        geomReader.meshes_start_ptr = 112
        virtual_pos = geomReader.meshes_start_ptr + 104*geomReader.num_meshes
        for mesh, meshReader in zip(model_data.meshes, geomReader.meshes):
            meshReader.vertex_data_start_ptr = virtual_pos

            meshReader.bytes_per_vertex, meshReader.vertex_components = calculate_vertex_properties(mesh.vertices[0])
            virtual_pos += meshReader.bytes_per_vertex*len(mesh.vertices)
            meshReader.weighted_bone_data_start_ptr = virtual_pos

            meshReader.polygon_data_start_ptr = virtual_pos


def calculate_vertex_properties(example_vertex):
    """
    Contains some nasty repetition of non-trivial data but I just want to get this done at this point
    """
    bytes_per_vertex = 0
    vertex_components = []
    if example_vertex.position is not None:
        vertex_components.append(VertexComponent(['Position', 3, 'f', 20, bytes_per_vertex]))
        bytes_per_vertex += 12
    if example_vertex.normal is not None:
        vertex_components.append(VertexComponent(['Normal', 3, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 8
    if example_vertex.uv is not None:
        vertex_components.append(VertexComponent(['UV', 2, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 4
    if 'UnknownVertexUsage1' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent(['UnknownVertexUsage1', 4, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 8
    if 'UnknownVertexUsage2' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent(['UnknownVertexUsage2', 3, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 8
    if 'UnknownVertexUsage3' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent(['UnknownVertexUsage3', 2, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 4
    if 'UnknownVertexUsage4' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent(['UnknownVertexUsage4', 2, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 4
    if 'UnknownVertexUsage5' in example_vertex.unknown_data:
        vertex_components.append(VertexComponent(['UnknownVertexUsage5', 4, 'e', 20, bytes_per_vertex]))
        bytes_per_vertex += 8
    if example_vertex.vertex_groups is not None:
        vertex_components.append(VertexComponent(['WeightedBoneID', len(example_vertex.vertex_groups), 'B', 20, bytes_per_vertex]))
        nominal_bytes = len(example_vertex.vertex_groups)
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)

        vertex_components.append(VertexComponent(['BoneWeight', len(example_vertex.vertex_groups), 'e', 20, bytes_per_vertex]))
        nominal_bytes = 2*len(example_vertex.vertex_groups)
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)

    return bytes_per_vertex, vertex_components


def convert_vertices(vertices, vertex_components):
    for component in vertex_components:
        pass
