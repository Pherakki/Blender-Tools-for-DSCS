import numpy as np
from ...FileReaders.GeomReader.VertexComponents import vertex_components_from_names


##################################
#  Polygon data type converters  #
##################################
def triangle_strips_to_polys(idxs):
    triangles = []
    for i, tri in enumerate(zip(idxs, idxs[1:], idxs[2:])):
        order = i % 2
        tri = (tri[0 + order], tri[1 - order], tri[2])
        triangle = set(tri)
        if not (len(triangle) != 3 or tri in triangles):
            triangles.append(tri)
    return triangles


def triangles_to_polys(idxs):
    triangles = []
    for tri, (idx_a, idx_b, idx_c) in enumerate(zip(idxs[::3], idxs[1::3], idxs[2::3])):
        triangles.append((idx_a, idx_b, idx_c))
    return triangles


triangle_converters = {'Triangles': triangles_to_polys,
                       'TriangleStrips': triangle_strips_to_polys}


class MeshInterface:
    def __init__(self):
        self.unknown_0x31 = None
        self.unknown_0x34 = None
        self.unknown_0x36 = None
        self.unknown_0x4C = None

        self.vertices = []
        self.vertex_group_bone_idxs = []
        self.polygons = []
        self.material_id = None

    @classmethod
    def from_subfile(cls, meshReader):
        interface = cls()
        interface.unknown_0x31 = meshReader.unknown_0x31
        interface.unknown_0x34 = meshReader.unknown_0x34
        interface.unknown_0x36 = meshReader.unknown_0x36
        interface.unknown_0x4C = meshReader.unknown_0x4C

        interface.vertices = process_posweights(meshReader.vertex_data, meshReader.max_vertex_groups_per_vertex)
        interface.vertex_group_bone_idxs = meshReader.weighted_bone_idxs
        interface.polygons = triangle_converters[meshReader.polygon_data_type](meshReader.polygon_data)
        interface.material_id = meshReader.material_id

        return interface

    def to_subfile(self, meshReader, virtual_pos):
        meshReader.vertex_data_start_ptr = virtual_pos

        vgroup_idxs = sorted(self.vertex_group_bone_idxs)
        meshReader.bytes_per_vertex, meshReader.vertex_components = calculate_vertex_properties(self.vertices, vgroup_idxs)
        vertex_generators = [vc.generator for vc in meshReader.vertex_components]

        meshReader.vertex_data = generate_vertex_data(self.vertices, vertex_generators)

        virtual_pos += meshReader.bytes_per_vertex * len(meshReader.vertex_data)
        meshReader.weighted_bone_data_start_ptr = virtual_pos
        meshReader.weighted_bone_idxs = vgroup_idxs
        virtual_pos += 4 * len(meshReader.weighted_bone_idxs)
        meshReader.polygon_data_start_ptr = virtual_pos
        meshReader.polygon_data = polys_to_triangles(self.polygons)
        virtual_pos += 2 * len(meshReader.polygon_data)
        virtual_pos += (4 - (virtual_pos % 4)) % 4  # Fix ragged chunk of size 4
        meshReader.padding_0x18 = 0

        meshReader.vertex_components_start_ptr = virtual_pos
        virtual_pos += 8 * len(meshReader.vertex_components)
        meshReader.num_weighted_bone_idxs = len(meshReader.weighted_bone_idxs)
        meshReader.num_vertex_components = len(meshReader.vertex_components)
        meshReader.always_5123 = meshReader.header_breaker

        meshReader.max_vertex_groups_per_vertex = max([len(vtx['WeightedBoneID']) if vtx['WeightedBoneID'] is not None else 0 for vtx in self.vertices])
        meshReader.max_vertex_groups_per_vertex = 0 if len(meshReader.weighted_bone_idxs) == 1 else meshReader.max_vertex_groups_per_vertex
        meshReader.unknown_0x31 = self.unknown_0x31
        meshReader.polygon_numeric_data_type = 4  # Can only write to triangles atm
        meshReader.unknown_0x34 = self.unknown_0x34
        meshReader.unknown_0x36 = self.unknown_0x36
        meshReader.material_id = self.material_id
        meshReader.num_vertices = len(meshReader.vertex_data)

        meshReader.num_polygon_idxs = len(meshReader.polygon_data)
        meshReader.padding_0x44 = 0
        meshReader.padding_0x48 = 0
        meshReader.unknown_0x4C = self.unknown_0x4C

        vertices = np.array([v['Position'] for v in self.vertices])
        minvs = np.min(vertices, axis=0)
        maxvs = np.max(vertices, axis=0)
        assert len(maxvs) == 3

        meshReader.mesh_centre = (maxvs + minvs) / 2
        meshReader.bounding_box_lengths = (maxvs - minvs) / 2
        return virtual_pos


def process_posweights(vertices, max_vertex_groups_per_vertex):
    example_vertex = vertices[0]
    if 'WeightedBoneID' in example_vertex:
        for vtx in vertices:
            res_ids = []
            res_wghts = []
            for id, wght in zip(vtx['WeightedBoneID'], vtx['BoneWeight']):
                if wght != 0.:
                    res_ids.append(id//3)
                    res_wghts.append(wght)
            vtx['WeightedBoneID'] = res_ids
            vtx['BoneWeight'] = res_wghts
    elif max_vertex_groups_per_vertex == 0:
        for vtx in vertices:
            vtx['WeightedBoneID'] = [0]
            vtx['BoneWeight'] = [1]
    elif max_vertex_groups_per_vertex == 1:
        for vtx in vertices:
            vtx['WeightedBoneID'] = [int(vtx['Position'][3]) // 3]
            vtx['BoneWeight'] = [1]
            vtx['Position'] = vtx['Position'][:3]
    else:
        assert 0, "Something went seriously wrong when processing posweights."

    return vertices


def calculate_vertex_properties(vertices, num_vertex_groups):
    """
    Still a bit messy but much nicer than before.
    """
    bytes_per_vertex = 0
    vertex_components = []
    example_vertex = vertices[0]
    max_vtx_groups = max([len(vtx['WeightedBoneID']) for vtx in vertices])
    if 'Position' in example_vertex:
        if max_vtx_groups == 1 and len(num_vertex_groups) > 1:
            vertex_components.append(vertex_components_from_names['PosWeight'](bytes_per_vertex))
            bytes_per_vertex += 16
        else:
            vertex_components.append(vertex_components_from_names['Position'](bytes_per_vertex))
            bytes_per_vertex += 12
    if 'Normal' in example_vertex:
        vertex_components.append(vertex_components_from_names['Normal'](bytes_per_vertex))
        bytes_per_vertex += 8
    if 'UV' in example_vertex:
        vertex_components.append(vertex_components_from_names['UV'](bytes_per_vertex))
        bytes_per_vertex += 4
    if 'UV2' in example_vertex:
        vertex_components.append(vertex_components_from_names['UV2'](bytes_per_vertex))
        bytes_per_vertex += 4
    if 'UV3' in example_vertex:
        vertex_components.append(vertex_components_from_names['UV3'](bytes_per_vertex))
        bytes_per_vertex += 4
    if 'Colour' in example_vertex:
        vertex_components.append(vertex_components_from_names['Colour'](bytes_per_vertex))
        bytes_per_vertex += 8
    if 'Tangent' in example_vertex:
        vertex_components.append(vertex_components_from_names['Tangent'](bytes_per_vertex))
        bytes_per_vertex += 8
    if 'Binormal' in example_vertex:
        vertex_components.append(vertex_components_from_names['Binormal'](bytes_per_vertex))
        bytes_per_vertex += 8
    if 'WeightedBoneID' in example_vertex and max_vtx_groups >= 2:
        num_grps = max_vtx_groups
        vertex_components.append(vertex_components_from_names[f'Indices{num_grps}'](bytes_per_vertex))
        nominal_bytes = num_grps
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)

        vertex_components.append(vertex_components_from_names[f'Weights{num_grps}'](bytes_per_vertex))
        nominal_bytes = 2*num_grps
        bytes_per_vertex += nominal_bytes + ((4 - (nominal_bytes % 4)) % 4)

    return bytes_per_vertex, vertex_components


def generate_vertex_data(vertices, generators):
    retval = []
    for vertex in vertices:
        vdata = [generator(vertex) for generator in generators]
        retval.append({k: v for d in vdata for k, v in d.items()})
    return retval


def polys_to_triangles(polys):
    return [sublist for lst in polys for sublist in lst]


class MissingWeightsError(TypeError):
    pass
