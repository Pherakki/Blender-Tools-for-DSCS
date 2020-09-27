from ..BaseRW import BaseRW
import numpy as np
import struct


class MeshReader(BaseRW):
    """
    A class to read mesh data within geom files. These files are split into five main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. A section that contains raw byte data for each vertex.
        3. A section that describes bone indices associated with the mesh; currently unsure what the purpose is.
        4. A section that defines the polygons.
        5. A section that states how to construct meaningful information out of the raw vertex bytes.

    Completion status
    ------
    (o) MeshReader can successfully parse all meshes in geom files in DSDB archive within current constraints.
    (x) MeshReader cannot yet fully interpret all mesh data in geom files in DSDB archive.
    (x) MeshReader cannot yet write data to geom files.

    Current hypotheses and observations
    ------
    1. *Every* header contains a value of 5123 occupying bytes 0x2C-0x2F. Maybe it's a checksum?
    2. *Every* vertex attribute contains a value of 20 occupying byte 0x05. Another checksum?! Weird junk data?
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

        self.unknown_0x30 = None
        self.unknown_0x31 = None
        self.polygon_numeric_data_type = None
        self.unknown_0x34 = None
        self.material_id = None
        self.num_vertices = None

        self.num_polygon_idxs = None
        self.unknown_0x44 = None
        self.unknown_0x50 = None
        self.unknown_0x5C = None

        # Data holders
        self.vertex_data = None
        self.weighted_bone_idxs = None
        self.polygon_data = None
        self.vertex_attribs = None

        # Utility data
        self.bytes_read = 0
        self.polygon_data_type = None

    def read_header(self):
        self.vertex_data_start_ptr = self.unpack('Q')
        self.polygon_data_start_ptr = self.unpack('Q')
        self.weighted_bone_data_start_ptr = self.unpack('Q')
        self.padding_0x18 = self.unpack('Q')  # Always 0
        self.assert_is_zero('padding_0x18')

        self.vertex_components_start_ptr = self.unpack('Q')
        self.num_weighted_bone_idxs = self.unpack('H')  # Lists a set of bones near the mesh
        self.num_vertex_components = self.unpack('H')
        self.bytes_per_vertex = self.unpack('H')
        self.always_5123 = self.unpack('H')  # Always 5123?!
        self.assert_equal('always_5123', 5123)

        # pc002:
        # Unknown0x34, Unknown0x36 the same for meshes 0-6: these are individual body parts with a single material each
        # They are also the same for meshes 7-8: these seem to be 'outline' meshes.
        # 0x30, 0x31 look like switches of some variety...
        # Changing unknown_0x30 doesn't seem to affect the mesh...
        # Same with unknown_0x34
        # Setting unknown_0x31 to 4 makes pc002 mesh disappear, setting to 5 seems to remap the bone weights.
        self.unknown_0x30 = self.unpack('B')  # takes values 0, 1, 2, 3, 4
        self.unknown_0x31 = self.unpack('B')  # ditto # values 1, 4, 5
        self.polygon_numeric_data_type = self.unpack('H')  # 4 or 5
        # Definitely not a float... could be B, H, or e.
        self.unknown_0x34 = self.unpack('HH')  # All over the place - I have no idea.
        self.material_id = self.unpack('I')
        self.num_vertices = self.unpack('I')

        self.num_polygon_idxs = self.unpack('I')
        # Experiments have been inconclusive. Modifying these seems to have no effect on the mesh...
        self.unknown_0x44 = self.unpack('fff')  # All over the place
        self.unknown_0x50 = self.unpack('fff')  # All over the place
        self.unknown_0x5C = self.unpack('fff')  # All over the place

        self.bytes_read = 0
        self.polygon_data_type = MeshReader.polygon_type_defs[self.polygon_numeric_data_type]

    def read_chunk(self, origin, length):
        self.assert_file_pointer_now_at(origin)
        data = self.bytestream.read(length)
        self.bytes_read += len(data)
        return data

    def decode_chunk(self, origin, num_elements, dtype, num_per_subchunk):
        data = self.read_chunk(origin, num_elements * num_per_subchunk * self.type_buffers[dtype])
        return self.chunk_list(self.decode_data_as(dtype, data), num_per_subchunk)

    def read_vertices(self):
        self.vertex_data = self.chunk_list(self.read_chunk(self.vertex_data_start_ptr, self.num_vertices * self.bytes_per_vertex),
                                           self.bytes_per_vertex)

    def read_weighted_bone_indices(self):
        self.weighted_bone_idxs = [idx[0] for idx in self.decode_chunk(self.weighted_bone_data_start_ptr, self.num_weighted_bone_idxs, 'I', 1)]

    def read_polygons(self):
        self.polygon_data = [idx[0] for idx in self.decode_chunk(self.polygon_data_start_ptr, self.num_polygon_idxs, 'H', 1)]
        self.cleanup_ragged_chunk(self.bytes_read, 4)

    def read_vertex_attribs(self):
        # 8 bytes per vertex attribute
        chunksize = 8
        self.vertex_attribs = list(map(VertexComponents, self.chunk_list(
            self.read_chunk(self.vertex_components_start_ptr, self.num_vertex_components * chunksize), chunksize)))

    def interpret_vertices(self):
        for i, raw_vertex_data in enumerate(self.vertex_data):
            interpreted_vertex = {}
            bounds = [vertexAttribute.data_start_ptr for vertexAttribute in self.vertex_attribs]
            bounds.append(len(raw_vertex_data))
            for j, vertexAttribute in enumerate(self.vertex_attribs):
                lo_bnd = bounds[j]
                hi_bnd = bounds[j + 1]
                raw_vertex_subdata = raw_vertex_data[lo_bnd:hi_bnd]
                used_data = vertexAttribute.num_elements * self.type_buffers[vertexAttribute.vertex_dtype]

                dtype = f'{vertexAttribute.num_elements}{vertexAttribute.vertex_dtype}'
                interpreted_data = np.array(struct.unpack(dtype, raw_vertex_subdata[:used_data]))
                if vertexAttribute.validate is not None:
                    vertexAttribute.validate(interpreted_data)
                interpreted_vertex[vertexAttribute.vertex_type] = interpreted_data

                unused_data = raw_vertex_subdata[used_data:]
                if len(unused_data) > 0:
                    assert unused_data == self.pad_byte * len(unused_data), f"Presumed junk data is non-zero: {unused_data}"
            self.vertex_data[i] = interpreted_vertex


def validate_weighted_bone_id(attribute_data):
    assert np.all(np.mod(attribute_data, 3)) == 0, f"WeightedBoneIDs were not all multiples of 3: {attribute_data}"


class VertexComponents:
    vertex_types = {1: 'Position',  # 3 floats
                    2: 'Normal',  # 3 half-floats
                    3: 'UnknownVertexUsage1',  # 4 half-floats, appears in chr, d, eff, npc, t, ui files
                    4: 'UnknownVertexUsage2',  # 3 half-floats, appears in eff and ui files
                    5: 'UV',  # 2 half-floats
                    6: 'UnknownVertexUsage3',  # 2 half-floats, appears in block, chr, d, e, eff, f, h, npc, scenario, t, ui files
                    7: 'UnknownVertexUsage4',  # 2 half-floats, appears in chr, d, f, h, t
                    9: 'UnknownVertexUsage5',  # 4 half-floats, appears in block, blok, chr, d, e, eff, ev, eve, f, h, line, medal, mob, npc, scenario, t, ui,
                    10: 'WeightedBoneID',  # Variable number of bytes. This is 3X THE INDEX of a bone id in MeshReader.weighted_bone_idxs
                    11: 'BoneWeight'}  # Variable number of half-floats

    dtypes = {6: 'f',
              11: 'e',
              1: 'B'}

    validation_policies = {'WeightedBoneID': validate_weighted_bone_id}

    def __init__(self, args):
        data = struct.unpack('HHBBH', args)
        self.vertex_type = VertexComponents.vertex_types[data[0]]
        self.num_elements = data[1]
        self.vertex_dtype = VertexComponents.dtypes[data[2]]
        self.always_20 = data[3]  # Always 20, no idea what for. Possibly a weird value for a junk byte.
        self.data_start_ptr = data[4]

        # Utility func
        self.validate = VertexComponents.validation_policies.get(self.vertex_type)

