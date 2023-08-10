import bpy
from mathutils import Vector


################################
# GENERIC - TO GO INTO LIBRARY #
################################
def connect_scalar(connect, in_value, out_value):
    if type(in_value) in (float, int): out_value.default_value = in_value
    else:                              connect(in_value, out_value)

def connect_vector(connect, in_value, out_value):
    if hasattr(in_value, "__iter__"): out_value.default_value = in_value
    else:                             connect(in_value, out_value)

def set_node_metadata(node, name, location, parent):
    node.name     = name
    node.label    = name
    node.parent   = parent
    node.location = location

def set_nodesocket_metadata(node, name, location, socket):
    node.name     = name
    node.label    = name
    node.parent   = socket.node.parent
    node.location = location
    
def mk_attribute_node(nodes, type, attr_path, name, location, parent=None):
    node = nodes.new("ShaderNodeAttribute")
    node.attribute_type = type
    node.attribute_name = attr_path
    set_node_metadata(node, name, location, parent)
    return node


def mk_normalize_node(nodes, name, location, parent=None):
    node = nodes.new('ShaderNodeVectorMath')
    node.operation = "NORMALIZE"
    set_node_metadata(node, name, location, parent)
    return node

def multiply_colors(nodes, connect, color_1, color_2, name, location, parent):
    product = nodes.new('ShaderNodeMix')
    product.data_type = "RGBA"
    product.blend_type = "MULTIPLY"
    product.clamp_result = False
    product.clamp_factor = True
    product.inputs["Factor"].default_value = 1.
    set_node_metadata(product, name, location, parent)

    connect_vector(connect, color_1, product.inputs[6])
    connect_vector(connect, color_2, product.inputs[7])
    return product.outputs[2]



def binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, op):
    vec_sum = nodes.new('ShaderNodeVectorMath')
    vec_sum.operation = op
    set_node_metadata(vec_sum, name, location, parent)
    
    connect_vector(connect, vector_1, vec_sum.inputs[0])
    connect_vector(connect, vector_2, vec_sum.inputs[1])
    return vec_sum.outputs[0]

def add_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "ADD")

def subtract_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "SUBTRACT")

def multiply_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "MULTIPLY")

def divide_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "DIVIDE")

def maximum_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "MAXIMUM")

def minimum_vectors(nodes, connect, vector_1, vector_2, name, location, parent):
    return binop_vectors(nodes, connect, vector_1, vector_2, name, location, parent, "MINIMUM")

def multiply_add_vectors(nodes, connect, vector, multiplier, addend, name, location, parent):
    product = nodes.new('ShaderNodeVectorMath')
    product.operation = "MULTIPLY_ADD"
    set_node_metadata(product, name, location, parent)
    
    connect_vector(connect, vector,     product.inputs[0])
    connect_vector(connect, multiplier, product.inputs[1])
    connect_vector(connect, addend,     product.inputs[2])
    return product.outputs[0]


def scale_vector(nodes, connect, vector, scalar, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "SCALE"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector, node.inputs[0])
    connect_vector(connect, scalar, node.inputs[3])
    return node.outputs[0]


def uop_scalar(nodes, connect, scalar, name, location, parent, op):
    product = nodes.new('ShaderNodeMath')
    product.operation = op
    set_node_metadata(product, name, location, parent)
    
    connect_scalar(connect, scalar, product.inputs[0])
    return product.outputs[0]

def binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, op):
    product = nodes.new('ShaderNodeMath')
    product.operation = op
    set_node_metadata(product, name, location, parent)
    
    connect_scalar(connect, scalar_1, product.inputs[0])
    connect_scalar(connect, scalar_2, product.inputs[1])
    return product.outputs[0]

def add_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "ADD")

def subtract_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "SUBTRACT")

def multiply_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "MULTIPLY")

def divide_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "DIVIDE")

def maximum_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "MAXIMUM")

def minimum_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    return binop_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent, "MINIMUM")

def clamp_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    clamp = nodes.new('ShaderNodeClamp')
    set_node_metadata(clamp, name, location, parent)
    connect_scalar(connect, scalar_1, clamp.inputs[0])
    connect_scalar(connect, scalar_2, clamp.inputs[1])
    return clamp.outputs[0]

def ceil_scalar(nodes, connect, scalar, name, location, parent):
    return uop_scalar(nodes, connect, scalar, name, location, parent, "CEIL")

def floor_scalar(nodes, connect, scalar, name, location, parent):
    return uop_scalar(nodes, connect, scalar, name, location, parent, "FLOOR")

def multiply_add_scalars(nodes, connect, scalar, multiplier, addend, name, location, parent):
    product = nodes.new('ShaderNodeMath')
    product.operation = "MULTIPLY_ADD"
    set_node_metadata(product, name, location, parent)
    
    connect_scalar(connect, scalar,     product.inputs[0])
    connect_scalar(connect, multiplier, product.inputs[1])
    connect_scalar(connect, addend,     product.inputs[2])
    return product.outputs[0]

def normalize_vector(nodes, connect, vector, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "NORMALIZE"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector, node.inputs[0])
    return node.outputs[0]


def length_vector(nodes, connect, vector, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "LENGTH"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector, node.inputs[0])
    return node.outputs[1]


def dot_vector(nodes, connect, vector_1, vector_2, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "DOT_PRODUCT"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector_1, node.inputs[0])
    connect_vector(connect, vector_2, node.inputs[1])
    return node.outputs[1]


def lerp_scalar(nodes, connect, interpolation_value, scalar_1, scalar_2, name, location, parent):
    # Fresnel Effect Reflection Strength
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "FLOAT"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True
    set_node_metadata(lerp, name, location, parent)
    
    connect_scalar(connect, interpolation_value, lerp.inputs[0])
    connect_scalar(connect, scalar_1,            lerp.inputs[2])
    connect_scalar(connect, scalar_2,            lerp.inputs[3])
    return lerp.outputs[0]


def lerp_vector(nodes, connect, interpolation_value, vector_1, vector_2, name, location, parent):
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "VECTOR"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True
    set_node_metadata(lerp, name, location, parent)
    
    connect_scalar(connect, interpolation_value, lerp.inputs[0])
    connect_vector(connect, vector_1,            lerp.inputs[4])
    connect_vector(connect, vector_2,            lerp.inputs[5])
    return lerp.outputs[1]


def lerp_color(nodes, connect, interpolation_value, color_1, color_2, name, location, parent):
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "RGBA"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    set_node_metadata(lerp, name, location, parent)
    
    connect_scalar(connect, interpolation_value, lerp.inputs[0])
    connect_vector(connect, color_1,             lerp.inputs[6])
    connect_vector(connect, color_2,             lerp.inputs[7])
    return lerp.outputs[2]

class SplitVector:
    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

class SplitColor:
    def __init__(self, r, g, b):
        self.R = r
        self.G = g
        self.B = b

def split_vector(nodes, connect, vector, name, location, parent):
    split_vector = nodes.new('ShaderNodeSeparateXYZ')
    set_node_metadata(split_vector, name, location, parent)
    connect_vector(connect, vector, split_vector.inputs[0])
    
    return SplitVector(split_vector.outputs[0],
                       split_vector.outputs[1],
                       split_vector.outputs[2])

def combine_vector(nodes, connect, x, y, z, name, location, parent):
    vector = nodes.new('ShaderNodeCombineXYZ')
    set_node_metadata(vector, name, location, parent)
    connect_scalar(connect, x, vector.inputs[0])
    connect_scalar(connect, y, vector.inputs[1])
    connect_scalar(connect, z, vector.inputs[2])
    
    return vector.outputs[0]

def split_color(nodes, connect, color, name, location, parent):
    split_vector = nodes.new('ShaderNodeSeparateColor')
    set_node_metadata(split_vector, name, location, parent)
    connect_vector(connect, color, split_vector.inputs[0])
    
    return SplitColor(split_vector.outputs[0],
                      split_vector.outputs[1],
                      split_vector.outputs[2])

def combine_color(nodes, connect, r, g, b, name, location, parent):
    vector = nodes.new('ShaderNodeCombineColor')
    set_node_metadata(vector, name, location, parent)
    connect_scalar(connect, r, vector.inputs[0])
    connect_scalar(connect, g, vector.inputs[1])
    connect_scalar(connect, b, vector.inputs[2])
    
    return vector.outputs[0]

def NodeFrame(nodes, name, location, parent):
    frame = nodes.new("NodeFrame")
    frame.name  = name
    frame.label = name
    frame.location = location
    frame.parent = parent
    return frame
