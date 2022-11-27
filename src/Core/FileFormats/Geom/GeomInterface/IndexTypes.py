from ..GeomBinary.MeshBinary.Base import PrimitiveTypes


class IndexType:
    def __init__(self, primitive_type, data_type, buffer):
        self.__primitive_type = primitive_type
        self.__data_type = data_type
        self.buffer = buffer

    @property
    def primitive_type(self):
        return self.__primitive_type

    @property
    def data_type(self):
        return self.__data_type

    @data_type.setter
    def data_type(self, value):
        if value in ['auto', 'B', 'H', 'I']:
            self.__data_type = value
        else:
            raise ValueError("Attempted to set the index type to an invalid value; can only accept "
                             "'auto' (automatically choose smallest that fits buffer)"
                             "'B' (uint8), "
                             "'H' (uint16), "
                             "'I' (uint32)")


class Points(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.POINTS, data_type, buffer)


class Lines(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.LINES, data_type, buffer)


class LineLoop(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.LINE_LOOP, data_type, buffer)


class LineStrip(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.LINE_STRIP, data_type, buffer)


class Triangles(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.TRIANGLES, data_type, buffer)

    def unpack(self):
        return [(t1, t2, t3) for t1, t2, t3 in zip(self.buffer[0::3], self.buffer[1::3], self.buffer[2::3])]


class TriangleStrip(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.TRIANGLE_STRIP, data_type, buffer)

    def to_triangles(self):
        buffer = []
        for i, (t1, t2, t3) in enumerate(zip(self.buffer[0:], self.buffer[1:], self.buffer[2:])):
            if len({t1, t2, t3}) < 3:
                continue
            if i % 2:
                buffer.extend((t1, t2, t3))
            else:
                buffer.extend((t2, t1, t3))
        return Triangles(self.data_type, buffer)


class TriangleFan(IndexType):
    def __init__(self, data_type, buffer):
        super().__init__(PrimitiveTypes.TRIANGLE_FAN, data_type, buffer)


def create_index_interface(primitive_type, data_type, buffer):
    if primitive_type == PrimitiveTypes.POINTS:
        return Points(data_type, buffer)
    elif primitive_type == PrimitiveTypes.LINES:
        return Lines(data_type, buffer)
    elif primitive_type == PrimitiveTypes.LINE_LOOP:
        return LineLoop(data_type, buffer)
    elif primitive_type == PrimitiveTypes.LINE_STRIP:
        return LineStrip(data_type, buffer)
    elif primitive_type == PrimitiveTypes.TRIANGLES:
        return Triangles(data_type, buffer)
    elif primitive_type == PrimitiveTypes.TRIANGLE_STRIP:
        return TriangleStrip(data_type, buffer)
    elif primitive_type == PrimitiveTypes.TRIANGLE_FAN:
        return TriangleFan(data_type, buffer)
    else:
        return IndexType(primitive_type, data_type, buffer)
