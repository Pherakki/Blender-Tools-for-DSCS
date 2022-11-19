from ..Base import AttributeTypes


class CopySingleIndicesIntoPosition:
    # Needs implementing and behaviour removed from pack_vertices
    APPLIES_TO = (AttributeTypes.POSITION,)

    @staticmethod
    def forwards(vertex, attribute):
        pass

    @staticmethod
    def create_attributes(attribute_list):
        pass

    @staticmethod
    def backwards(vertex, attribute):
        pass

    @staticmethod
    def delete_attributes(attribute_list):
        pass


class DeleteSingleIndices:
    # Needs implementing and behaviour removed from pack_vertices
    APPLIES_TO = (AttributeTypes.INDEX, AttributeTypes.WEIGHT)

    @staticmethod
    def forwards(vertex, attribute):
        pass

    @staticmethod
    def create_attributes(attribute_list):
        pass

    @staticmethod
    def backwards(vertex, attribute):
        pass

    @staticmethod
    def delete_attributes(attribute_list):
        pass


class DivideTexcoordBy1024:
    APPLIES_TO = (AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3)

    @staticmethod
    def forwards(vertex, attribute):
        vertex.buffer[attribute] = [d/1024 for d in vertex.buffer[attribute]]

    @staticmethod
    def create_attributes(attribute_list):
        pass

    @staticmethod
    def backwards(vertex, attribute):
        vertex.buffer[attribute] = [int(d*1024) for d in vertex.buffer[attribute]]

    @staticmethod
    def delete_attributes(attribute_list):
        pass


class DivideIndicesBy3:
    # Does not commute with CopySingleIndicesIntoPosition...
    # forwards and backwards need to be separate lists...
    APPLIES_TO = (AttributeTypes.INDEX,)

    @staticmethod
    def forwards(vertex, attribute):
        vertex.buffer[attribute] = [d//3 for d in vertex.buffer[attribute]]

    @staticmethod
    def create_attributes(attribute_list):
        pass

    @staticmethod
    def backwards(vertex, attribute):
        vertex.buffer[attribute] = [d*3 for d in vertex.buffer[attribute]]

    @staticmethod
    def delete_attributes(attribute_list):
        pass
