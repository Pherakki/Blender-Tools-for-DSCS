from ..Base import AttributeTypes


class ShaderTransform:
    TRANSFORM_VERTICES = True
    TRANSFORM_ATTRS    = True
    
    def poll(self, vertex):
        raise NotImplementedError
    
    def vertex_transform_unpack(self, vertex):
        raise NotImplementedError
        
    def vertex_transform_pack(self, vertex):
        raise NotImplementedError
    
    def attribute_transform_pack(self, attributes):
        raise NotImplementedError
    
    
class PosPackedIndex(ShaderTransform):
    TRANSFORM_VERTICES = True
    TRANSFORM_ATTRS    = True
    
    def poll(self, vertex):
        return vertex.position is not None
    
    def vertex_transform_unpack(self, vertex):
        vertex.indices = [int(vertex.position[-1])]
        vertex.weights = [1.]
        vertex.position = vertex.position[:-1]
        
    def vertex_transform_pack(self, vertex):
        vertex.position = [*vertex.position, *vertex.indices]
        vertex.indices = None
        vertex.weights = None
    
    def attribute_transform_pack(self, attributes):
        attributes[AttributeTypes.POSITION].count += attributes[AttributeTypes.INDEX].count
        del attributes[AttributeTypes.INDEX]
        del attributes[AttributeTypes.WEIGHT]


class UVDiv1024(ShaderTransform):
    TRANSFORM_VERTICES = True
    TRANSFORM_ATTRS    = False
    
    def __init__(self, attribute):
        self.attribute = attribute
        
    def poll(self, vertex):
        return vertex.buffer[self.attribute] is not None
    
    def vertex_transform_unpack(self, vertex):
        vertex.buffer[self.attribute] = [d/1024 for d in vertex.buffer[self.attribute]]
        
    def vertex_transform_pack(self, vertex):
        vertex.buffer[self.attribute] = [int(d*1024) for d in vertex.buffer[self.attribute]]


class IndexDiv3(ShaderTransform):
    TRANSFORM_VERTICES = True
    TRANSFORM_ATTRS    = False
    
    def poll(self, vertex):
        return vertex.indices is not None
    
    def vertex_transform_pack(self, vertex):
        vertex.indices = [i//3 for i in vertex.indices]
    
    def vertex_transform_unpack(self, vertex):
        vertex.indices = [int(i*3) for i in vertex.indices]

class TypeCast(ShaderTransform):
    TRANSFORM_VERTICES = False
    TRANSFORM_ATTRS    = True
    
    def __init__(self, attribute, to_type):
        self.attribute = attribute
        self.to_type   = to_type
        
    def attribute_transform_pack(self, attributes):
        attributes[self.attribute].type = self.to_type
