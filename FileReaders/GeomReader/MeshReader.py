from ..BaseRW import BaseRW
import numpy as np
import struct


class MeshReader(BaseRW):
    """
    A class to read mesh data within geom files. These files are split into five main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section that contains raw byte data for each vertex.
        3. A section that contains bone indices which have vertices assigned to them by this mesh.
        4. A section that defines the polygons.
        5. A section that states how to construct meaningful information out of the raw vertex bytes.

    Completion status
    ------
    (o) MeshReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (x) MeshReader cannot yet fully interpret all mesh data in geom files in DSDB archive.
    (o) MeshReader can write data to geom files.

    Current hypotheses and observations
    ------
    1. *Every* header contains a value of 5123 occupying bytes 0x2C-0x2F. Maybe it's a checksum?
    2. *Every* vertex component contains a value of 20 occupying byte 0x05. Another checksum?! Weird junk data?
    3. The remaining unknowns have been modified on the pc002 mesh, and the results have been inconclusive.
       No visual changes have been seen, except in the case of unknown_0x31, which may affect bone weights.
       Setting all the floats to 0 (unknowns 0x48 - 0x68) has no observable effect.
    """
    polygon_type_defs = {4: 'Triangles', 5: 'TriangleStrips'}

    def __init__(self, io_stream):
        super().__init__(io_stream)

        # Header variables
        self.vertex_data_start_ptr = None
        self.polygon_data_start_ptr = None
        self.weighted_bone_data_start_ptr = None
        self.padding_0x18 = None

        self.vertex_components_start_ptr = None
        self.num_weighted_bone_idxs = None
        self.num_vertex_components = None
        self.bytes_per_vertex = None
        self.always_5123 = None

        self.max_vertex_groups_per_vertex = None
        self.unknown_0x31 = None
        self.polygon_numeric_data_type = None
        self.unknown_0x34 = None
        self.unknown_0x36 = None
        self.material_id = None
        self.num_vertices = None

        self.num_polygon_idxs = None
        self.padding_0x44 = None
        self.padding_0x48 = None
        self.unknown_0x4C = None
        self.mesh_centre = None
        self.bounding_box_lengths = None

        # Data holders
        self.vertex_data = None
        self.weighted_bone_idxs = None
        self.polygon_data = None
        self.vertex_components = None

        # Utility data
        self.polygon_data_type = None

    def read_header(self):
        self.rw_header(self.read_buffer)

    def write_header(self):
        self.rw_header(self.write_buffer)

    def rw_header(self, rw_operator):
        rw_operator('vertex_data_start_ptr', 'Q')
        rw_operator('polygon_data_start_ptr', 'Q')
        rw_operator('weighted_bone_data_start_ptr', 'Q')
        rw_operator('padding_0x18', 'Q')  # Always 0
        self.assert_is_zero('padding_0x18')

        rw_operator('vertex_components_start_ptr', 'Q')
        rw_operator('num_weighted_bone_idxs', 'H')  # Lists a set of bones near the mesh
        rw_operator('num_vertex_components', 'H')
        rw_operator('bytes_per_vertex', 'H')
        rw_operator('always_5123', 'H')  # Always 5123?!
        self.assert_equal('always_5123', 5123)

        # pc002:
        # Unknown0x34, Unknown0x36 the same for meshes 0-6: these are individual body parts with a single material each
        # They are also the same for meshes 7-8: these seem to be 'outline' meshes.
        # 0x30, 0x31 look like switches of some variety...
        # Same with unknown_0x34
        # Setting unknown_0x31 to 4 makes pc002 mesh disappear, setting to 5 seems to remap the bone weights.
        # Might describe how to build the polygons?
        rw_operator('max_vertex_groups_per_vertex', 'B')  # takes values 0, 1, 2, 3, 4
        rw_operator('unknown_0x31', 'B')  # values 1, 4, 5: 4 means pos and normal only, diff between 1 nad 5 is what?? 1 doesn't have unk vt 2...
        rw_operator('polygon_numeric_data_type', 'H')  # 4 or 5
        # Definitely not a float... could be B, H, or e.
        rw_operator('unknown_0x34', 'H')  # All over the place - I have no idea.
        rw_operator('unknown_0x36', 'H')  # All over the place - I have no idea.

        rw_operator('material_id', 'I')
        rw_operator('num_vertices', 'I')

        rw_operator('num_polygon_idxs', 'I')
        rw_operator('padding_0x44', 'I')
        self.assert_is_zero('padding_0x44')
        rw_operator('padding_0x48', 'I')
        self.assert_is_zero('padding_0x48')
        rw_operator('unknown_0x4C', 'f')  # May be related to the two below?!
        rw_operator('mesh_centre', 'fff')
        rw_operator('bounding_box_lengths', 'fff')

        self.polygon_data_type = MeshReader.polygon_type_defs[self.polygon_numeric_data_type]

    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.cleanup_ragged_chunk_read)
        self.interpret_mesh_data()

    def write(self):
        self.reinterpret_mesh_data()
        self.read_write(self.write_buffer, self.write_raw, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_operator_raw, chunk_cleanup_operator):
        self.assert_file_pointer_now_at(self.vertex_data_start_ptr)
        self.rw_vertices(rw_operator_raw)
        self.rw_weighted_bone_indices(rw_operator)
        self.rw_polygons(rw_operator, chunk_cleanup_operator)
        self.rw_vertex_components(rw_operator)

    def rw_vertices(self, rw_operator_raw):
        self.assert_file_pointer_now_at(self.vertex_data_start_ptr)
        rw_operator_raw('vertex_data', self.num_vertices * self.bytes_per_vertex)

    def rw_weighted_bone_indices(self, rw_operator):
        self.assert_file_pointer_now_at(self.weighted_bone_data_start_ptr)
        rw_operator('weighted_bone_idxs', 'I'*self.num_weighted_bone_idxs, force_1d=True)

    def rw_polygons(self, rw_operator, chunk_cleanup_operator):
        self.assert_file_pointer_now_at(self.polygon_data_start_ptr)
        rw_operator('polygon_data', 'H'*self.num_polygon_idxs, force_1d=True)

        chunk_cleanup_operator(self.bytestream.tell(), 4)

    def rw_vertex_components(self, rw_operator):
        rw_operator('vertex_components', 'HHBBH'*self.num_vertex_components)

    def interpret_vertices(self):
        add_implied_vertex_group = ('WeightedBoneID' not in [vc.vertex_type for vc in self.vertex_components]) and len(self.weighted_bone_idxs)
        # Since bools are 0 or 1, this is a concise way of implementing the converse implication operator
        # I.e. is False if *and only if* "cond_1 == False cond_2 == True" implemented without if/else statements
        # Fun fact: ** seems to be marginally faster, but both have highly variable performance so you'd only notice it
        # with a colossal amount of calls..!
        # assert (add_implied_vertex_group) <= (len(self.weighted_bone_idxs) <= 1)
        for i, raw_vertex_data in enumerate(self.vertex_data):
            interpreted_vertex = {}
            bounds = [vertex_component.data_start_ptr for vertex_component in self.vertex_components]
            bounds.append(len(raw_vertex_data))
            for j, vertex_component in enumerate(self.vertex_components):
                lo_bnd = bounds[j]
                hi_bnd = bounds[j + 1]
                raw_vertex_subdata = raw_vertex_data[lo_bnd:hi_bnd]
                used_data = vertex_component.num_elements * self.type_buffers[vertex_component.vertex_dtype]

                dtype = f'{vertex_component.num_elements}{vertex_component.vertex_dtype}'

                interpreted_data = np.array(struct.unpack(dtype, raw_vertex_subdata[:used_data]))
                if vertex_component.validate is not None:
                    interpreted_data = vertex_component.validate(interpreted_data)  # CHECK POSITION HACK!!!
                interpreted_vertex[vertex_component.vertex_type] = interpreted_data

                unused_data = raw_vertex_subdata[used_data:]
                if len(unused_data) > 0:
                    assert unused_data == self.pad_byte * len(unused_data), f"Presumed junk data is non-zero: {unused_data}"
            if add_implied_vertex_group:
                interpreted_vertex['WeightedBoneID'] = [0]
                interpreted_vertex['BoneWeight'] = [1]
            self.vertex_data[i] = interpreted_vertex

    def reinterpret_vertices(self):
        reinterpreted_vertices = []
        for i, vertex_data in enumerate(self.vertex_data):
            reinterpreted_vertex = b''
            bounds = [vertex_component.data_start_ptr for vertex_component in self.vertex_components]
            bounds.append(self.bytes_per_vertex)
            for j, vertex_component in enumerate(self.vertex_components):
                if vertex_component.validate is not None:
                    vertex_component.validate(vertex_data[vertex_component.vertex_type])
                #print(vertex_component.vertex_type, vertex_component.num_elements, vertex_component.vertex_dtype, vertex_data[vertex_component.vertex_type])
                reinterpreted_vertex += struct.pack(f'{vertex_component.num_elements}{vertex_component.vertex_dtype}',
                                                   *vertex_data[vertex_component.vertex_type])
                reinterpreted_vertex += self.pad_byte * (bounds[j+1] - len(reinterpreted_vertex))
            
            reinterpreted_vertices.append(reinterpreted_vertex)
        self.vertex_data = b''.join(reinterpreted_vertices)

    def interpret_mesh_data(self):
        self.vertex_components = [VertexComponent(data) for data in self.chunk_list(self.vertex_components, 5)]
        self.vertex_data = self.chunk_list(self.vertex_data, self.bytes_per_vertex)
        self.interpret_vertices()

    def reinterpret_mesh_data(self):
        self.reinterpret_vertices()
        vertex_components = [(VertexComponent.reverse_vertex_types[vc.vertex_type],
                              vc.num_elements,
                              VertexComponent.reverse_dtypes[vc.vertex_dtype],
                              vc.always_20, vc.data_start_ptr)
                             for vc in self.vertex_components]
        self.vertex_components = self.flatten_list(vertex_components)


def validate_position(component_data):
    #assert len(component_data) == 3, f"Position is not a 3-vector: {component_data}"
    return component_data[:3]


def validate_weighted_bone_id(component_data):
    assert np.all(np.mod(component_data, 3)) == 0, f"WeightedBoneIDs were not all multiples of 3: {component_data}"
    return component_data


class VertexComponent:
    vertex_types = {1: 'Position',  # 3 floats
                    2: 'Normal',  # 3 half-floats
                    3: 'UnknownVertexUsage1',  # 4 half-floats, appears in chr, d, eff, npc, t, ui files # colour? # tangent?
                    4: 'UnknownVertexUsage2',  # 3 half-floats, appears in eff and ui files # binormal?
                    5: 'UV',  # 2 half-floats
                    6: 'UnknownVertexUsage3',  # 2 half-floats, appears in block, chr, d, e, eff, f, h, npc, scenario, t, ui files # uv2?
                    7: 'UnknownVertexUsage4',  # 2 half-floats, appears in chr, d, f, h, t # uv3?
                    9: 'UnknownVertexUsage5',  # 4 half-floats, appears in block, blok, chr, d, e, eff, ev, eve, f, h, line, medal, mob, npc, scenario, t, ui, # colour?
                    10: 'WeightedBoneID',  # Variable number of bytes. This is 3X THE INDEX of a bone id in MeshReader.weighted_bone_idxs
                    11: 'BoneWeight'}  # Variable number of half-floats

    reverse_vertex_types = {'Position': 1,  # 3 floats
                    'Normal' : 2,  # 3 half-floats
                    'UnknownVertexUsage1': 3,  # 4 half-floats, appears in chr, d, eff, npc, t, ui files # colour?
                    'UnknownVertexUsage2': 4,  # 3 half-floats, appears in eff and ui files
                    'UV': 5,  # 2 half-floats
                    'UnknownVertexUsage3': 6,  # 2 half-floats, appears in block, chr, d, e, eff, f, h, npc, scenario, t, ui files
                    'UnknownVertexUsage4': 7,  # 2 half-floats, appears in chr, d, f, h, t
                    'UnknownVertexUsage5': 9,  # 4 half-floats, appears in block, blok, chr, d, e, eff, ev, eve, f, h, line, medal, mob, npc, scenario, t, ui, # colour?
                    'WeightedBoneID': 10,  # Variable number of bytes. This is 3X THE INDEX of a bone id in MeshReader.weighted_bone_idxs
                    'BoneWeight': 11}  # Variable number of half-floats

    dtypes = {6: 'f',
              11: 'e',
              1: 'B'}

    reverse_dtypes = {'f': 6,
                      'e': 11,
                      'B': 1}

    validation_policies = {'Position': validate_position,
                           'WeightedBoneID': validate_weighted_bone_id}

    def __init__(self, data):
        self.vertex_type = VertexComponent.vertex_types[data[0]]
        self.num_elements = data[1]
        self.vertex_dtype = VertexComponent.dtypes[data[2]]
        self.always_20 = data[3]  # Always 20, no idea what for. Possibly a weird value for a junk byte.
        self.data_start_ptr = data[4]

        # Utility func
        self.validate = VertexComponent.validation_policies.get(self.vertex_type)

