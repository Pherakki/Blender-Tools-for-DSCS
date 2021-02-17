class BaseVertexComponent:
    vertex_type = None
    num_elements = None
    vertex_dtype = None

    def __init__(self, data_start_ptr):
        self.data_start_ptr = data_start_ptr

    @classmethod
    def generator(cls, vtx):
        assert len(vtx[cls.vertex_type]) == cls.num_elements, "Vertex has an invalid number of elements."
        return {cls.vertex_type: vtx[cls.vertex_type]}


class Position(BaseVertexComponent):
    vertex_type = 'Position'
    num_elements = 3
    vertex_dtype = 'f'


class PosWeight(BaseVertexComponent):
    vertex_type = 'Position'
    num_elements = 4
    vertex_dtype = 'f'

    def generator(self, vtx):
        return {'Position': [*vtx['Position'], float(3 * vtx['WeightedBoneID'][0])]}


class Normal(BaseVertexComponent):
    vertex_type = 'Normal'
    num_elements = 3
    vertex_dtype = 'e'


class Tangent(BaseVertexComponent):
    vertex_type = 'Tangent'
    num_elements = 4
    vertex_dtype = 'e'


class Binormal(BaseVertexComponent):
    vertex_type = 'Binormal'
    num_elements = 3
    vertex_dtype = 'e'


class UV(BaseVertexComponent):
    vertex_type = 'UV'
    num_elements = 2
    vertex_dtype = 'e'


class UV2(BaseVertexComponent):
    vertex_type = 'UV2'
    num_elements = 2
    vertex_dtype = 'e'


class UV3(BaseVertexComponent):
    vertex_type = 'UV3'
    num_elements = 2
    vertex_dtype = 'e'


class Colour(BaseVertexComponent):
    vertex_type = 'Colour'
    num_elements = 4
    vertex_dtype = 'e'


class BaseIndexComponent(BaseVertexComponent):
    @classmethod
    def generator(cls, vtx):
        num_missing_items = cls.num_elements - len(vtx[cls.vertex_type])
        current_items = [item*3 for item in vtx[cls.vertex_type]]
        current_items.extend([0] * num_missing_items)
        assert len(current_items) == cls.num_elements, "Something went wrong extending vertex indices."
        return {cls.vertex_type: current_items}


class BaseWeightComponent(BaseVertexComponent):
    @classmethod
    def generator(cls, vtx):
        num_missing_items = cls.num_elements - len(vtx[cls.vertex_type])
        current_items = vtx[cls.vertex_type]
        current_items.extend([0.] * num_missing_items)
        assert len(current_items) == cls.num_elements, "Something went wrong extending vertex indices."
        return {cls.vertex_type: current_items}


class Indices2(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 2
    vertex_dtype = 'B'


class Indices3(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 3
    vertex_dtype = 'B'


class Indices4(BaseIndexComponent):
    vertex_type = 'WeightedBoneID'
    num_elements = 4
    vertex_dtype = 'B'


class Weights2(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 2
    vertex_dtype = 'e'


class Weights3(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 3
    vertex_dtype = 'e'


class Weights4(BaseWeightComponent):
    vertex_type = 'BoneWeight'
    num_elements = 4
    vertex_dtype = 'e'


all_vtx_components = [Position, PosWeight, Normal, UV, UV2, UV3, Colour, Tangent, Binormal,
                      Indices2, Indices3, Indices4,
                      Weights2, Weights3, Weights4]

# These dictionaries are how the vertex components are accessed from other files via factory methods
vertex_components_from_names = {cls.__name__: cls for cls in all_vtx_components}
vertex_components_from_defn = {(cls.vertex_type, cls.num_elements, cls.vertex_dtype): cls for cls in all_vtx_components}
