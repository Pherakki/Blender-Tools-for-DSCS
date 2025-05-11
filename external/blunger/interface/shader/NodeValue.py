class BaseValue:
    def __init__(self, generator, socket):
        self.generator = generator
        self._socket = socket
    
    @property
    def node(self):
        return self._socket.node
    
    @property
    def var(self):
        return self._socket
    
    @property
    def location(self):
        return self.node.location
    @location.setter
    def location(self, value):
        self.node.location = value
    
    def set_location(self, location):
        self.location = location
    
    def set_location_relative_to(self, node, location):
        self.location = node.location + location


class ShaderScalar(BaseValue):
    def __init__(self, generator, socket):
        super().__init__(generator, socket)


class ShaderVector(BaseValue):
    def __init__(self, generator, socket):
        super().__init__(generator, socket)


class ShaderColor(BaseValue):
    def __init__(self, generator, socket):
        super().__init__(generator, socket)


# Composite value
class ShaderVectorScalar:
    def __init__(self, generator, vector_socket, scalar_socket):
        self.vector = ShaderVector(generator, vector_socket)
        self.scalar = ShaderScalar(generator, scalar_socket)
    
    @property
    def location(self):
        return self.vector.location
    @location.setter
    def location(self, value):
        delta = self.scalar.location - self.vector.location
        
        self.vector.location = value
        self.scalar.location = value + delta
    

# Composite value
class ShaderColorAlpha:
    def __init__(self, generator, color_socket, alpha_socket):
        self.color = ShaderColor(generator, color_socket)
        self.alpha = ShaderScalar(generator, alpha_socket)

    @property
    def location(self):
        return self.color.location
    @location.setter
    def location(self, value):
        delta = self.alpha.location - self.color.location
        
        self.color.location = value
        self.alpha.location = value + delta
    
    def __mul__(self, other):
        if isinstance(other, ShaderColorAlpha):
            return ShaderColorAlpha(self.color*other.color, self.alpha*other.alpha)
        elif isinstance(other, ShaderVectorScalar):
            return ShaderVectorScalar(self.color*other.vector, self.alpha*other.scalar)
        else:
            return ShaderVectorScalar(self.color*other, self.alpha*other)

