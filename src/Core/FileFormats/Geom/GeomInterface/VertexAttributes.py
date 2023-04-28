from ..GeomBinary.MeshBinary.Base import AttributeTypes, VertexAttributeBinary


class VertexAttribute:
    def __init__(self, index, type, normalised, count):
        self.index      = index
        self.type       = type
        self.normalised = normalised
        self.count      = count

    @property
    def _ATTR_TYPE(self):
        return f"CustomAttribute::{self.index}"

    def __repr__(self):
        return f"[Geom::{self._ATTR_TYPE}] {self.count}{self.type}/{self.normalised}"

    def to_binary(self, INVERSE_DATA_TYPES, offset=0):
        vab = VertexAttributeBinary()
        vab.index = self.index
        vab.normalised = self.normalised
        vab.elem_count = self.count
        vab.type = INVERSE_DATA_TYPES[self.type]
        vab.offset = offset
        return vab


class PositionAttribute(VertexAttribute):
    def __init__(self, type='f', normalised=0, count=3):
        super().__init__(AttributeTypes.POSITION, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"PositionAttribute"


class NormalAttribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=3):
        super().__init__(AttributeTypes.NORMAL, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"NormalAttribute"


class TangentAttribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=4):
        super().__init__(AttributeTypes.TANGENT, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"TangentAttribute"


class BinormalAttribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=3):
        super().__init__(AttributeTypes.BINORMAL, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"BinormalAttribute"


class UV1Attribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=2):
        super().__init__(AttributeTypes.UV1, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"UV1Attribute"


class UV2Attribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=2):
        super().__init__(AttributeTypes.UV2, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"UV2Attribute"


class UV3Attribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=2):
        super().__init__(AttributeTypes.UV3, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"UV3Attribute"


class ColorAttribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=4):
        super().__init__(AttributeTypes.COLOR, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"ColorAttribute"


class IndexAttribute(VertexAttribute):
    def __init__(self, type='B', normalised=0, count=4):
        super().__init__(AttributeTypes.INDEX, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"IndexAttribute"


class WeightAttribute(VertexAttribute):
    def __init__(self, type='e', normalised=0, count=4):
        super().__init__(AttributeTypes.WEIGHT, type, normalised, count)

    @property
    def _ATTR_TYPE(self):
        return f"WeightAttribute"


def create_vertex_attribute_interface(va, data_types):
    index = va.index
    if index == AttributeTypes.POSITION:
        return PositionAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.NORMAL:
        return NormalAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.TANGENT:
        return TangentAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.BINORMAL:
        return BinormalAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.UV1:
        return UV1Attribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.UV2:
        return UV2Attribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.UV3:
        return UV3Attribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.COLOR:
        return ColorAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.INDEX:
        return IndexAttribute(data_types[va.type], va.normalised, va.elem_count)
    elif index == AttributeTypes.WEIGHT:
        return WeightAttribute(data_types[va.type], va.normalised, va.elem_count)
    else:
        return VertexAttribute(va.index, data_types[va.type], va.normalised, va.elem_count)
