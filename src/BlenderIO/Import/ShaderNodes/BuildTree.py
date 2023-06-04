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


############################
# SPECIFIC - TO STAY HERE? #
############################
class ColorWrapper:
    __slots__ = ("RGB", "A")
    
    def __init__(self, node):
        self.RGB = node.outputs["Color"]
        self.A   = node.outputs["Alpha"]
        
    @property
    def color(self):
        return self.RGB
        
    @property
    def alpha(self):
        return self.A

def mk_scene_attribute_node(nodes, attr_name, name, location, parent):
    return mk_attribute_node(nodes, "VIEW_LAYER", f"DSCS_SceneProperties.{attr_name}", name, location, parent)

def mk_material_attribute_node(nodes, attr_name, name, location, parent):
    if len(attr_name) > 23:
         raise ValueError(f"Attribute name too long: {attr_name}")
    return mk_attribute_node(nodes, "OBJECT", f"active_material.DSCS_MaterialProperties.{attr_name}", name, location, parent)

def SceneColorAttribute(nodes, attr_name, name, location, parent):
    return ColorWrapper(mk_scene_attribute_node(nodes, attr_name, name, location, parent))

def SceneVectorAttribute(nodes, attr_name, name, location, parent):
    return mk_scene_attribute_node(nodes, attr_name, name, location, parent).outputs["Vector"]

def SceneFloatAttribute(nodes, attr_name, name, location, parent):
    return mk_scene_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]

def MaterialColorAttribute(nodes, attr_name, name, location, parent):
    return ColorWrapper(mk_material_attribute_node(nodes, attr_name, name, location, parent))

def MaterialVectorAttribute(nodes, attr_name, name, location, parent):
    return mk_material_attribute_node(nodes, attr_name, name, location, parent).outputs["Vector"]

def MaterialFloatAttribute(nodes, attr_name, name, location, parent):
    return mk_material_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]


class ShaderVariables:
    def __init__(self):
        self.TREE_WIDTH     = 0
        self.TREE_HEIGHT    = 0
        
        # Geometry
        self.NORMAL         = None
        self.TANGENT        = None
        self.BINORMAL       = None
        self.VVIEW          = None
        self.UV1            = None
        self.UV2            = None
        self.UV3            = None
        self.VERTEX_COLOR   = None
        self.VERTEX_ALPHA   = None
        self.OVERLAY_FACTOR = None
        self.TIME           = None
        
        # Variables
        self.DIFFUSE_COLOR    = None
        self.DIFFUSE_ALPHA    = None
        self.SPECULAR_COLOR   = None
        self.SPECULAR_ALPHA   = None
        self.REFLECTION_COLOR = None
        self.REFLECTION_ALPHA = None
        self.DIFFUSE_LIGHTING_COLOR  = None
        self.SPECULAR_LIGHTING_COLOR = None
        
        # Normal Mappings
        self.PARALLAX   = None
        self.DISTORTION = None
        
        # Texture Samplers
        self.COLOR_SAMPLER_COLOR          = None
        self.COLOR_SAMPLER_ALPHA          = None
        self.OVERLAY_COLOR_SAMPLER_COLOR  = None
        self.OVERLAY_COLOR_SAMPLER_ALPHA  = None
        self.LIGHTMAP_SAMPLER_COLOR       = None
        self.LIGHTMAP_SAMPLER_ALPHA       = None
        self.NORMAL_SAMPLER_COLOR         = None
        self.NORMAL_SAMPLER_ALPHA         = None
        self.OVERLAY_NORMAL_SAMPLER_COLOR = None
        self.OVERLAY_NORMAL_SAMPLER_ALPHA = None


def attach_UV(sampler_node, sampler_props, shvar, connect, parallax=None):
    if   sampler_props.uv_map == "UV1":
        UV = shvar.UV1
    elif sampler_props.uv_map == "UV2":
        UV = shvar.UV2
    elif sampler_props.uv_map == "UV3":
        UV = shvar.UV3

    if UV is not None:
        if parallax is not None:
            connect(UV, parallax.inputs[1])
            UV = parallax.outputs[0]
        connect(UV, sampler_node.inputs["Vector"])


def attach_UV1(sampler_node, shvar, connect, parallax=None):
    UV = shvar.UV1
    if UV is not None:
        if parallax is not None:
            connect(UV, parallax.inputs[1])
            UV = parallax.outputs[0]
        connect(UV, sampler_node.inputs["Vector"])


def rebuild_tree(bpy_material, used_images):
    props    = bpy_material.DSCS_MaterialProperties
    node_tree = bpy_material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    connect = links.new
    
    # Wipe tree
    nodes.clear()
    
    # Build contributions
    shvar = ShaderVariables()
    
    # Generate geometry edits
    column_pos = 0
    shvar.TREE_HEIGHT = 0
    build_geometry(props, nodes, connect, shvar, column_pos)
    
    # Height mapping
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_parallax(props, nodes, connect, used_images, shvar, column_pos)
    
    # Textures
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_textures(props, nodes, connect, used_images, shvar, column_pos)
   
    # Next column
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_overlay_strength(props, nodes, connect, shvar, column_pos)
    
    # Bump mapping
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_bump(props, nodes, connect, shvar, column_pos)
    #build_distortion(props, nodes, connect, shvar)
    
    # Create Color
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_flat_diffuse(props, nodes, connect, used_images, shvar, column_pos)
    build_lighting    (props, nodes, connect, used_images, shvar, column_pos)
    build_reflections (props, nodes, connect, used_images, shvar, column_pos)
    # build_glassmap(...)
    # build_shadows(...)
    
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_ambient_light(props, nodes, connect, shvar, column_pos)
    
    column_pos = shvar.TREE_WIDTH
    shvar.TREE_HEIGHT = 0
    build_specular(props, nodes, connect, shvar)
    build_total_color(props, nodes, connect, shvar)
    # TODO: build_fog(...) # Need to figure out how to get the fogparams first

    # OpenGL settings
    build_GL_ALPHA(props, nodes, connect, shvar)
    build_GL_BLEND(props, nodes, connect, shvar)
    
    # Just here so alpha can be properly implemented...
    transparency = nodes.new('ShaderNodeBsdfTransparent')
    transparency.location = (shvar.TREE_WIDTH, -300)
    shvar.TREE_WIDTH += 300
    
    mix_alpha = nodes.new('ShaderNodeMixShader')
    mix_alpha.name  = "+ Alpha"
    mix_alpha.label = "+ Alpha"
    connect_scalar(connect, shvar.DIFFUSE_ALPHA, mix_alpha.inputs[0])
    connect(transparency.outputs[0], mix_alpha.inputs[1])
    connect(shvar.DIFFUSE_COLOR,     mix_alpha.inputs[2])
    mix_alpha.location = (shvar.TREE_WIDTH, 0)
    shvar.TREE_WIDTH += 300

    mat_out = nodes.new('ShaderNodeOutputMaterial')
    mat_out.location = (shvar.TREE_WIDTH, 0)
    connect(mix_alpha.outputs[0], mat_out.inputs["Surface"])


def build_geometry(props, nodes, connect, shvar, column_pos):
    column_pos = 0
    
    geometry_frame = nodes.new("NodeFrame")   
    geometry_frame.name  = "Geometry"
    geometry_frame.label = "Geometry"
    geometry_frame.location = (shvar.TREE_WIDTH, shvar.TREE_HEIGHT)
    
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.name  = "Geometry"
    geometry.label = "Geometry"
    geometry.parent = geometry_frame
    geometry.location = Vector((column_pos, 0))

    bitangent_node = nodes.new("ShaderNodeAttribute")
    bitangent_node.attribute_type = "GEOMETRY"
    bitangent_node.attribute_name = "bitangent"
    bitangent_node.name  = "Binormal"
    bitangent_node.label = "Binormal"
    bitangent_node.parent = geometry_frame
    bitangent_node.location =  Vector((0, -250))

    shvar.NORMAL   = geometry      .outputs["Normal"]
    shvar.TANGENT  = geometry      .outputs["Tangent"]
    shvar.BINORMAL = bitangent_node.outputs["Vector"]
    shvar.VVIEW    = geometry      .outputs["Incoming"]

    shvar.TREE_WIDTH += 400
    shvar.TREE_HEIGHT = -500
    
    if props.requires_colors:
        vertex_color = nodes.new('ShaderNodeVertexColor')
        vertex_color.parent   = geometry_frame
        vertex_color.location = Vector((0, shvar.TREE_HEIGHT))
        vertex_color.layer_name = "Map"
        shvar.VERTEX_COLOR = vertex_color.outputs["Color"]
        shvar.VERTEX_ALPHA = vertex_color.outputs["Alpha"]
        shvar.TREE_HEIGHT -= 200
    
    if props.use_time:
        build_time(props, nodes, connect, shvar, column_pos)
    # TODO: SPLIT UVs TO NEW COLUMN
    if props.uv_1_active:
        build_uv(props.uv_1, nodes, connect, shvar, props.uv_1_is_projection, 1, column_pos)
    if props.uv_2_active:
        build_uv(props.uv_2, nodes, connect, shvar, props.uv_2_is_projection, 2, column_pos)
    if props.uv_3_active:
        build_uv(props.uv_3, nodes, connect, shvar, props.uv_3_is_projection, 3, column_pos)


def build_time(props, nodes, connect, shvar, column_pos):
    frame = nodes.new("NodeFrame")   
    frame.name  = "Time"
    frame.label = "Time"
    frame.location = (column_pos, shvar.TREE_HEIGHT)
    
    frame_tick = nodes.new("ShaderNodeAttribute")
    frame_tick.attribute_type = "VIEW_LAYER"
    frame_tick.attribute_name = "frame_float"
    frame_tick.name  = "Animation Frame"
    frame_tick.label = "Animation Frame"
    frame_tick.parent = frame
    frame_tick.location = Vector((0, 0))
    
    frame_rate = nodes.new("ShaderNodeAttribute")
    frame_rate.attribute_type = "VIEW_LAYER"
    frame_rate.attribute_name = "render.fps"
    frame_rate.name  = "Framerate"
    frame_rate.label = "Framerate"
    frame_rate.parent = frame
    frame_rate.location = Vector((0, -200))
      
    time = nodes.new("ShaderNodeMath")
    time.operation = "DIVIDE"
    time.name  = "Time"
    time.label = "Time"
    time.parent = frame
    time.location = Vector((200, -50))
    connect(frame_tick.outputs["Fac"], time.inputs[0])
    connect(frame_rate.outputs["Fac"], time.inputs[1])
    
    shvar.TIME = time.outputs[0]  # This should become a shvar member
    shvar.TREE_HEIGHT -= 450
    shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + 400)


def build_uv(uv_props, nodes, connect, shvar, is_proj, idx, column_pos):
    frame = nodes.new("NodeFrame")   
    frame.name  = f"UV Transforms {idx}"
    frame.label = f"UV Transforms {idx}"
    frame.location = (column_pos, shvar.TREE_HEIGHT)
    
    if is_proj:
        uv_map_node = nodes.new("ShaderNodeTexCoord")
        uv_map_node.name  = f"UV{idx} - ScreenSpace"
        uv_map_node.label = f"UV{idx} - ScreenSpace"
        uv_map_node.parent = frame
        uv_map_node.location = Vector((0, 0))
        
        UV = uv_map_node.outputs["Window"]
        tree_height = 300
    else:
        uv_map_node = nodes.new("ShaderNodeUVMap")
        uv_map_node.uv_map = f"UV{idx}"
        uv_map_node.name  = f"UV{idx}"
        uv_map_node.label = f"UV{idx}"
        uv_map_node.parent = frame
        uv_map_node.location = Vector((0, 0))
        
        UV = uv_map_node.outputs[0]
        tree_height = -200
        
    offset = 200
    # UV Scroll
    if uv_props.use_scroll_speed and shvar.TIME is not None:
        SCROLL_SPEED  = MaterialVectorAttribute(nodes, f"uv_{idx}.scroll_speed", "Scroll Speed", (offset, -200), frame)
        SCROLL_OFFSET = scale_vector(nodes, connect, SCROLL_SPEED,    shvar.TIME, "Scroll Offset", (offset + 200, -200), frame)
        UV            = add_vectors (nodes, connect, UV,           SCROLL_OFFSET,      "+ Scroll", (offset + 400,    0), frame)            

        offset += 600
        tree_height = min(tree_height, -450)
    
    # UV Rotation
    if uv_props.use_rotation:
        ROTATION  = MaterialFloatAttribute(nodes, f"uv_{idx}.rotation", "Rotation", (offset, -200), frame)
    
        # Rotation needs to be an rotation about the vector (0., 0., 1.) through the point (0.5, 0.5, 0.0)
        # Probably doable by defining the rotation vector as (0.5, 0.5, 0.) and providing the angle?
        # Rotation plane might also be tangent to the rotation vector, 
        # meanining that the input vector requires offsetting...
        plus_rotation = nodes.new("ShaderNodeVectorRotate")
        plus_rotation.rotation_type = "Z_AXIS"
        plus_rotation.name     = "+ Rotation"
        plus_rotation.label    = "+ Rotation"
        plus_rotation.parent   = frame
        plus_rotation.location = Vector((offset + 200, 0))
        connect(UV, plus_rotation.inputs[0])
        plus_rotation.inputs[1].default_value = [0.5, 0.5, 0.]
        connect(ROTATION, plus_rotation.inputs[3])
        
        offset += 400
        tree_height = min(tree_height, -400)

    # UV Offset
    if uv_props.use_offset:
        OFFSET = MaterialVectorAttribute(nodes, f"uv_{idx}.offset", "Offset", (offset, -200), frame)
        UV     = add_vectors(nodes, connect, UV, OFFSET, "+ Offset", (offset + 200, 0), frame)            

        offset += 400
        tree_height = min(tree_height, -400)

    # UV Scale
    if uv_props.use_scale:
        SCALE = MaterialVectorAttribute(nodes, f"uv_{idx}.scale", "Scale", (offset, -200), frame)
        UV    = multiply_vectors(nodes, connect, UV, SCALE, "+ Scale", (offset + 200, 0), frame)            

        offset += 400
        tree_height = min(tree_height, -400)
    
    setattr(shvar, f"UV{idx}", UV)
    shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + offset)
    shvar.TREE_HEIGHT += tree_height


def build_textures(props, nodes, connect, used_images, shvar, column_pos):
    column_pos += 100
    # Texture Samplers
    samplers_frame = nodes.new("NodeFrame")
    samplers_frame.label    = "Texture Samplers"
    samplers_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))
   
    HEIGHT = 0
    LOCAL_WIDTH = 0
    INCREMENT = -300
    
    def mk_parallax(height_offset):
        plus_parallax = nodes.new('ShaderNodeVectorMath')
        plus_parallax.operation = "ADD"
        plus_parallax.name  = "+ Parallax"
        plus_parallax.label = "+ Parallax"
        plus_parallax.parent = samplers_frame
        plus_parallax.location = Vector((0, HEIGHT + height_offset))
        connect(shvar.PARALLAX, plus_parallax.inputs[0])
        return plus_parallax
    
    def mk_sampler(HEIGHT, sampler_name, sampler_props, use_parallax=False):
        def mk_sampler_node(width_offset, height_offset):
            sampler_node = nodes.new('ShaderNodeTexImage')
            sampler_node.name     = sampler_name
            sampler_node.label    = sampler_name
            sampler_node.parent   = samplers_frame
            sampler_node.image    = used_images.get(sampler_props.typename)
            sampler_node.location =  Vector((width_offset, HEIGHT+height_offset))
            return sampler_node
        
        width_offset = 0
        parallax_node = None
        alpha_parallax_node = None
        if shvar.PARALLAX is not None and use_parallax:
            parallax_node = mk_parallax(0)
            width_offset += 200
        
        sampler_node = mk_sampler_node(width_offset, 0)
        attach_UV(sampler_node, sampler_props, shvar, connect, parallax_node)
        COLOR = sampler_node.outputs["Color"]
        if sampler_props.split_alpha:
            sampler_node_alpha = mk_sampler_node(width_offset, -300)
            sampler_node.name        = f"{sampler_name} - Color"
            sampler_node.label       = f"{sampler_name} - Color"
            sampler_node_alpha.name  = f"{sampler_name} - Alpha"
            sampler_node_alpha.label = f"{sampler_name} - Alpha"
            if shvar.PARALLAX is not None and use_parallax:
                alpha_parallax_node = mk_parallax(-300)
            attach_UV1(sampler_node_alpha, shvar, connect, alpha_parallax_node)
            ALPHA = sampler_node_alpha.outputs["Alpha"]
            HEIGHT = -600
        else:
            ALPHA = sampler_node.outputs["Alpha"]
            HEIGHT = -300
            
        return COLOR, ALPHA, 300 + width_offset, HEIGHT
    
    # ColorSampler
    COLOR_WIDTH = 0
    use_color_sampler = (props.color_sampler.typename in used_images)
    if use_color_sampler:
        DIFFUSE_COLOR, \
        DIFFUSE_ALPHA, \
        COLOR_WIDTH,   \
        NODES_HEIGHT = mk_sampler(HEIGHT, "ColorSampler", props.color_sampler, use_parallax=True)
        shvar.COLOR_SAMPLER_COLOR = DIFFUSE_COLOR
        shvar.COLOR_SAMPLER_ALPHA = DIFFUSE_ALPHA
    
        COLOR_WIDTH -= 300
    
    elif props.use_diffuse_color:
        diffuse = MaterialColorAttribute(nodes, "diffuse_color", "Diffuse Color", (0, HEIGHT), samplers_frame)
        NODES_HEIGHT = INCREMENT
        DIFFUSE_COLOR = diffuse.RGB
        DIFFUSE_ALPHA = diffuse.A
    
    else:
        diffuse_color = nodes.new("ShaderNodeRGB")
        diffuse_color.label = "Fallback Diffuse Color"
        diffuse_color.parent = samplers_frame
        diffuse_color.location = Vector((0, HEIGHT))
        diffuse_color.outputs["Color"].default_value = (1., 1., 1., 1.)
        
        DIFFUSE_COLOR = diffuse_color.outputs["Color"]
        
        diffuse_alpha = nodes.new("ShaderNodeValue")
        diffuse_alpha.label = "Fallback Diffuse Alpha"
        diffuse_alpha.parent = samplers_frame
        diffuse_alpha.location = Vector((0, HEIGHT - 190))
        diffuse_alpha.outputs["Value"].default_value = 1.
        
        DIFFUSE_ALPHA = diffuse_alpha.outputs["Value"]
        
        NODES_HEIGHT = INCREMENT
        
    COLOR_WIDTH += 300
    
    HEIGHT += NODES_HEIGHT
    LOCAL_WIDTH = max(LOCAL_WIDTH, COLOR_WIDTH)
    shvar.DIFFUSE_COLOR = DIFFUSE_COLOR
    shvar.DIFFUSE_ALPHA = DIFFUSE_ALPHA

    
    use_overlay_color_sampler = (props.overlay_color_sampler.typename in used_images)
    if use_overlay_color_sampler:
        shvar.OVERLAY_COLOR_SAMPLER_COLOR, \
        shvar.OVERLAY_COLOR_SAMPLER_ALPHA, \
        NODES_WIDTH,                       \
        NODES_HEIGHT = mk_sampler(HEIGHT, "OverlayColorSampler", props.overlay_color_sampler)
        HEIGHT += NODES_HEIGHT

        LOCAL_WIDTH = max(LOCAL_WIDTH, NODES_WIDTH)
    
    use_lightmap_sampler = (props.lightmap_sampler.typename in used_images)
    if use_lightmap_sampler:
        shvar.LIGHTMAP_SAMPLER_COLOR, \
        shvar.LIGHTMAP_SAMPLER_ALPHA, \
        NODES_WIDTH,                  \
        NODES_HEIGHT = mk_sampler(HEIGHT, "LightSampler", props.lightmap_sampler)
        HEIGHT += NODES_HEIGHT

        LOCAL_WIDTH = max(LOCAL_WIDTH, NODES_WIDTH)

    use_normal_sampler = (props.normal_sampler.typename in used_images)
    if use_normal_sampler:
        shvar.NORMAL_SAMPLER_COLOR, \
        shvar.NORMAL_SAMPLER_ALPHA, \
        NODES_WIDTH,                \
        NODES_HEIGHT = mk_sampler(HEIGHT, "NormalSampler", props.normal_sampler, use_parallax=True)
        HEIGHT += NODES_HEIGHT

        LOCAL_WIDTH = max(LOCAL_WIDTH, NODES_WIDTH)
    
    use_overlay_normal_sampler = (props.overlay_normal_sampler.typename in used_images)
    if use_overlay_normal_sampler:
        shvar.OVERLAY_NORMAL_SAMPLER_COLOR, \
        shvar.OVERLAY_NORMAL_SAMPLER_ALPHA, \
        NODES_WIDTH,                        \
        NODES_HEIGHT = mk_sampler(HEIGHT, "OverlayNormalSampler", props.overlay_normal_sampler)
        HEIGHT += NODES_HEIGHT

        LOCAL_WIDTH = max(LOCAL_WIDTH, NODES_WIDTH)
    
    shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + LOCAL_WIDTH)


def build_overlay_strength(props, nodes, connect, shvar, column_pos):
    if props.use_overlay_strength:
        column_pos += 100
        # Overlay Factor frame
        overlay_frame = nodes.new("NodeFrame")
        overlay_frame.label = "Overlay Factor"
        overlay_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))

        WIDTH = 0
        
        # Mixing factor
        OVERLAY_FACTOR = MaterialFloatAttribute(nodes, "overlay_strength", "OverlayStrength", (WIDTH, 0), overlay_frame)
        WIDTH += 200
        
        # Overlay color alpha
        if shvar.OVERLAY_COLOR_SAMPLER_ALPHA is not None:
            OVERLAY_FACTOR = multiply_scalars(nodes, connect, shvar.OVERLAY_COLOR_SAMPLER_ALPHA, OVERLAY_FACTOR, "* Overlay Color Alpha", (WIDTH, 0), overlay_frame)
            WIDTH += 200

        # Vertex alpha
        if props.use_overlay_vertex_alpha and shvar.VERTEX_ALPHA is not None:
            OVERLAY_FACTOR = multiply_scalars(nodes, connect, OVERLAY_FACTOR, shvar.VERTEX_ALPHA, "* Vertex Alpha", (WIDTH, 0), overlay_frame)
            WIDTH += 200
        
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + WIDTH + 30)
        shvar.OVERLAY_FACTOR = OVERLAY_FACTOR


def build_parallax(props, nodes, connect, used_images, shvar, column_pos):
    if props.use_parallax_bias_x or props.use_parallax_bias_y:
        column_pos += 100
        
        parallax_frame = nodes.new("NodeFrame")
        parallax_frame.label    = "Parallax"
        parallax_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))
    
        parallax_sampler = nodes.new('ShaderNodeTexImage')
        parallax_sampler.name     = "Parallax Sampler"
        parallax_sampler.label    = "Parallax Sampler"
        parallax_sampler.parent   = parallax_frame
        parallax_sampler.location =  Vector((0, 0))
        parallax_props = None
        # if props.parallax_map_type == "NORMAL":
        #     props.color_sampler = props.normal_sampler
        # elif props.parallax_map_type == "COLOR":    
        #     parallax_props = props.color_sampler
        # if (props.normal_sampler.typename in used_images):
        #     parallax_props = props.normal_sampler
        if (props.color_sampler.typename in used_images):    
            parallax_props = props.color_sampler
            
            if not props.color_sampler.split_alpha:
                attach_UV(parallax_sampler, parallax_props, shvar, connect)
            else:
                attach_UV1(parallax_sampler, shvar, connect)
            
        if parallax_props is not None:
            parallax_sampler.image    = used_images.get(parallax_props.typename)
        
        PARALLAX_CHANNEL = parallax_sampler.outputs["Alpha"]
        
        # TODO
        # THIS IS WRONG FOR SOME REASON - UNSURE WHY
        
        ###################
        # BIAS GENERATION #
        ###################
        PARALLAX_INPUT = PARALLAX_CHANNEL if PARALLAX_CHANNEL is not None else 0
        PARALLAX_X     = MaterialFloatAttribute(nodes, "parallax_bias_x", "Parallax Bias X", (0, -300), parallax_frame)
        PARALLAX_Y     = MaterialFloatAttribute(nodes, "parallax_bias_y", "Parallax Bias Y", (0, -500), parallax_frame)

        PARALLAX = multiply_add_scalars(nodes, connect, PARALLAX_INPUT, PARALLAX_X, PARALLAX_Y, "(HEIGHT * Bias X) + Bias Y", (400, 0), parallax_frame)
        
        #######################
        # PARALLAX GENERATION #
        #######################
        XCOORD = dot_vector(nodes, connect, shvar.VVIEW, shvar.TANGENT,  "U Coord", (0, -700), parallax_frame)
        YCOORD = dot_vector(nodes, connect, shvar.VVIEW, shvar.BINORMAL, "V Coord", (0, -900), parallax_frame)
        
        PARALLAX_U = multiply_scalars(nodes, connect, PARALLAX, XCOORD, "Parallax X", (800,    0), parallax_frame)
        PARALLAX_V = multiply_scalars(nodes, connect, PARALLAX, YCOORD, "Parallax Y", (800, -200), parallax_frame)

        # Output vector
        shvar.PARALLAX = combine_vector(nodes, connect, PARALLAX_U, PARALLAX_V, 0, "UV Parallax", (1000, 0), parallax_frame)
        
        shvar.TREE_HEIGHT -= 700
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + 1200)


def build_bump(props, nodes, connect, shvar, column_pos):
    if props.use_bumpiness:
        column_pos += 100
        bump_frame = nodes.new("NodeFrame")
        bump_frame.label    = "Bumpiness"
        bump_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))
    
        BUMP = None
        OVERLAY_BUMP = None
        def mk_bump_channel(label, sampler_color, bump_attr, HEIGHT):
            bump_channel_frame = nodes.new("NodeFrame")
            bump_channel_frame.label    = f"{label} Bump Map Channel"
            bump_channel_frame.parent = bump_frame
            bump_channel_frame.location = Vector((0, HEIGHT-30))
            bump_channel_frame.use_custom_color = True
            bump_channel_frame.color = (0.3, 0.3, 0.3)

            BUMPINESS       = MaterialFloatAttribute(nodes, bump_attr, f"{label}Bumpiness", (0, -300), bump_channel_frame)
            HALF_NORMAL_MAP = subtract_vectors(nodes, connect, sampler_color, [0.5, 0.5, 0.5], f"{label} Half Normal", (0, 0), bump_channel_frame)
            BUMP_MAP        = scale_vector(nodes, connect, HALF_NORMAL_MAP, BUMPINESS, f"{label} Bump Map", (200, 0), bump_channel_frame)
            SPLIT_BUMP_MAP  = split_vector(nodes, connect, BUMP_MAP, f"Split {label} Bump Map", (400, 0), bump_channel_frame)
                
            XCOORD = scale_vector(nodes, connect, shvar.TANGENT,  SPLIT_BUMP_MAP.X, "Tangent Influence", (600, 0), bump_channel_frame)
            YCOORD = scale_vector(nodes, connect, shvar.BINORMAL, SPLIT_BUMP_MAP.Y, "Binormal Influence", (600, -200), bump_channel_frame)
            FULL_BUMP_MAP = add_vectors(nodes, connect, XCOORD, YCOORD, f"Full {label} Bump Map", (800, 0), bump_channel_frame)
        
            shvar.TREE_HEIGHT -= 500
            
            return FULL_BUMP_MAP
        
        channel_height = 0
        if shvar.NORMAL_SAMPLER_COLOR is not None:
            BUMP         = mk_bump_channel("",        shvar.NORMAL_SAMPLER_COLOR,         "bumpiness",         channel_height)
            channel_height -= 550
        if shvar.OVERLAY_NORMAL_SAMPLER_COLOR is not None:
            OVERLAY_BUMP = mk_bump_channel("Overlay", shvar.OVERLAY_NORMAL_SAMPLER_COLOR, "overlay_bumpiness", channel_height)
            channel_height -= 550

        CONTRIB = None
        EXTRA_OFFSET = 0
        if BUMP is not None and OVERLAY_BUMP is not None:
            EXTRA_OFFSET += 300
            CONTRIB = lerp_vector(nodes, connect, shvar.OVERLAY_FACTOR, BUMP, OVERLAY_BUMP, "Mixed Bump", (1000, -450), bump_frame)
        elif BUMP is not None and OVERLAY_BUMP is None:
            CONTRIB = BUMP
        elif BUMP is None and OVERLAY_BUMP is not None:
            CONTRIB = OVERLAY_BUMP
            
        if CONTRIB is not None:
            BUMPED_NORMAL = add_vectors(nodes, connect, shvar.NORMAL, CONTRIB, "Bumped Normal", (EXTRA_OFFSET + 1000, 0), bump_frame)
            shvar.NORMAL = normalize_vector(nodes, connect, BUMPED_NORMAL, "BumpNormalized Normal", (EXTRA_OFFSET + 1200, 0), bump_frame)

        shvar.TREE_HEIGHT += channel_height
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + 1000 + EXTRA_OFFSET + 400)


def build_distortion(props, nodes, connect, shvar):
    # TODO: DISTORTION SOURCE CAN BE OVERLAY NORMAL OR NORMAL MAP
    # THIS CAN AFFECT SAMPLING OF OTHER MAPS
    if props.use_distortion:
        distortion_frame = nodes.new("NodeFrame")
        distortion_frame.label    = "Distortion"
        distortion_frame.location = Vector((0, 0))
    
        half_normal_sampler = nodes.new('ShaderNodeVectorMath')
        half_normal_sampler.operation = "SUBTRACT"
        half_normal_sampler.name  = "Half Normal"
        half_normal_sampler.label = "Half Normal"
        if shvar.NORMAL_SAMPLER_COLOR is not None:
            connect(shvar.NORMAL_SAMPLER_COLOR, half_normal_sampler.inputs[0])
        else:
            half_normal_sampler.inputs[0].default_value[0] = 0.5
            half_normal_sampler.inputs[0].default_value[1] = 0.5
            half_normal_sampler.inputs[0].default_value[2] = 0.5
        half_normal_sampler.inputs[1].default_value[0] = 0.5
        half_normal_sampler.inputs[1].default_value[1] = 0.5
        half_normal_sampler.inputs[1].default_value[2] = 0.5
        half_normal_sampler.parent = distortion_frame
        half_normal_sampler.location = Vector((0, 0))

        DISTORTION_STRENGTH = MaterialFloatAttribute(nodes, "distortion_strength", "DistortionStrength", (0, 0), distortion_frame)
                
        distortion = nodes.new('ShaderNodeVectorMath')
        distortion.operation = "SCALE"
        distortion.name  = "Distortion"
        distortion.label = "Distortion"
        connect(half_normal_sampler.outputs[0], distortion.inputs[0])
        connect(DISTORTION_STRENGTH,            distortion.inputs[2])
        distortion.parent = distortion_frame
        distortion.location = Vector((0, 0))

        shvar.DISTORTION = distortion.outputs[0]


def build_flat_diffuse(props, nodes, connect, used_images, shvar, column_pos):
    diffuse_frame = nodes.new("NodeFrame")
    diffuse_frame.label = "Flat Diffuse Contribution"
    diffuse_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))

    SAMPLER_COLUMN = 0
    ROW_0 = 0
    WORKING_COLUMN = 0
    WORKING_ROW = 0
    
    DIFFUSE_COLOR = shvar.DIFFUSE_COLOR
    DIFFUSE_ALPHA = shvar.DIFFUSE_ALPHA
    
    ####################
    # TRANSPARENCY MAP #
    ####################
    # TODO: Skip for now
    pass

    ###################
    # OVERLAY TEXTURE #
    ###################
    if shvar.OVERLAY_COLOR_SAMPLER_COLOR is not None:
        WORKING_COLUMN = 280

        # RGB only
        overlay_factor = 0.5 if shvar.OVERLAY_FACTOR is None else shvar.OVERLAY_FACTOR
        DIFFUSE_COLOR = lerp_color(nodes, connect, overlay_factor, DIFFUSE_COLOR, shvar.OVERLAY_COLOR_SAMPLER_COLOR, "Mixed Texture", (WORKING_COLUMN, ROW_0), diffuse_frame)
        
        WORKING_COLUMN += 200
        WORKING_ROW = min(WORKING_ROW, -200)
    
    ##################
    # VERTEX COLOURS #
    ##################
    if shvar.VERTEX_COLOR is not None:
        DIFFUSE_COLOR = multiply_colors(nodes, connect, DIFFUSE_COLOR, shvar.VERTEX_COLOR, "+ Vertex Color", (WORKING_COLUMN, ROW_0), diffuse_frame)
        
        WORKING_ROW = min(WORKING_ROW, -450)
        DIFFUSE_ALPHA = 1.
        if props.use_vertex_alpha and shvar.VERTEX_ALPHA is not None:
            DIFFUSE_ALPHA = multiply_scalars(nodes, connect, DIFFUSE_ALPHA, shvar.VERTEX_ALPHA, "* Vertex Alpha", (WORKING_COLUMN, ROW_0-200), diffuse_frame)
            WORKING_ROW = min(WORKING_ROW, ROW_0 - 200)
        
        WORKING_COLUMN += 200
    
    #######################
    # FLAT DIFFUSE COLOUR #
    #######################
    if shvar.COLOR_SAMPLER_COLOR is not None:
        # Create flat diffuse color
        if props.use_diffuse_color:
            diffuse_color = MaterialColorAttribute(nodes, "diffuse_color", "Diffuse Color", (WORKING_COLUMN, -250), diffuse_frame)
            
            FLAT_DIFFUSE_COLOR = diffuse_color.RGB
            FLAT_DIFFUSE_ALPHA = diffuse_color.A
        else:
            diffuse_color = nodes.new("ShaderNodeRGB")
            diffuse_color.label = "Fallback Diffuse Color"
            diffuse_color.parent = diffuse_frame
            diffuse_color.location = Vector((WORKING_COLUMN, -250))
            diffuse_color.outputs["Color"].default_value = (1., 1., 1., 1.)
            
            FLAT_DIFFUSE_COLOR = diffuse_color.outputs["Color"]
            
            diffuse_alpha = nodes.new("ShaderNodeValue")
            diffuse_alpha.label = "Fallback Diffuse Alpha"
            diffuse_alpha.parent = diffuse_frame
            diffuse_alpha.location = Vector((WORKING_COLUMN, -250 - 190))
            diffuse_alpha.outputs["Value"].default_value = 1.
            
            FLAT_DIFFUSE_ALPHA = diffuse_alpha.outputs["Value"]
        
        WORKING_COLUMN += 200
        WORKING_ROW = min(WORKING_ROW, -650)
        
        ########################
        # DIFFUSE STRENGTH MAP #
        ########################
        if props.use_diffuse_str_map:
            if   props.diffuse_str_map_channel == "ColorSamplerA"  and shvar.COLOR_SAMPLER_ALPHA  is not None:
                diffuse_strength = shvar.COLOR_SAMPLER_ALPHA
            elif props.diffuse_str_map_channel == "NormalSamplerA" and shvar.NORMAL_SAMPLER_ALPHA is not None:
                diffuse_strength = shvar.NORMAL_SAMPLER_ALPHA
            elif props.diffuse_str_map_channel == "NormalSamplerR" and shvar.NORMAL_SAMPLER_COLOR is not None:
                diffuse_strength = shvar.NORMAL_SAMPLER_COLOR
            elif props.diffuse_str_map_channel == "LightSamplerA" and shvar.LIGHT_SAMPLER_ALPHA   is not None:
                diffuse_strength = shvar.LIGHT_SAMPLER_ALPHA
            else:
                raise NotImplementedError(f"Unknown Diffuse Map type: {props.diffuse_str_map_channel}")

            # Should probably handle "R" channel differently but this probably works
            DIFFUSE_COLOR = lerp_color (nodes, connect, diffuse_strength, [1., 1., 1., 1.], DIFFUSE_COLOR, "Diffuse Color Map", (WORKING_COLUMN,    0), diffuse_frame)
            DIFFUSE_ALPHA = lerp_scalar(nodes, connect, diffuse_strength,               1., DIFFUSE_ALPHA, "Diffuse Alpha Map", (WORKING_COLUMN, -500), diffuse_frame)
            WORKING_COLUMN += 200

        DIFFUSE_COLOR = multiply_colors (nodes, connect, DIFFUSE_COLOR, FLAT_DIFFUSE_COLOR, "* Flat Diffuse Color", (WORKING_COLUMN, 0),    diffuse_frame)        
        DIFFUSE_ALPHA = multiply_scalars(nodes, connect, DIFFUSE_ALPHA, FLAT_DIFFUSE_ALPHA, "* Flat Diffuse Alpha", (WORKING_COLUMN, -500), diffuse_frame)
    
        WORKING_COLUMN += 200
        WORKING_ROW = min(WORKING_ROW, -700)

    #########################
    # LIGHTMAP CONTRIBUTION #
    #########################
    if shvar.LIGHTMAP_SAMPLER_COLOR is not None:
        LIGHTMAP_POWER    = MaterialFloatAttribute(nodes, "lightmap_power",    "LightmapPower",    (WORKING_COLUMN, - 200), diffuse_frame)
        LIGHTMAP_STRENGTH = MaterialFloatAttribute(nodes, "lightmap_strength", "LightmapStrength", (WORKING_COLUMN, - 400), diffuse_frame)
        
        LIGHTMAP_COLOR      = scale_vector(nodes, connect, shvar.LIGHTMAP_SAMPLER_COLOR, LIGHTMAP_POWER, "Lightmap Color", (WORKING_COLUMN+200, -250), diffuse_frame)
        FULL_LIGHTMAP_COLOR = lerp_color(nodes, connect, LIGHTMAP_STRENGTH, [1., 1., 1., 1.], LIGHTMAP_COLOR, "Full Lightmap Color", (WORKING_COLUMN+400, -250), diffuse_frame)
        DIFFUSE_COLOR       = multiply_vectors(nodes, connect, DIFFUSE_COLOR, FULL_LIGHTMAP_COLOR, "+ Lightmap", (WORKING_COLUMN + 600, -250), diffuse_frame)
        
        WORKING_ROW = min(WORKING_ROW, -600)
        WORKING_COLUMN += 800
        
    
    shvar.DIFFUSE_COLOR = DIFFUSE_COLOR
    shvar.DIFFUSE_ALPHA = DIFFUSE_ALPHA
    shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + WORKING_COLUMN)
    shvar.TREE_HEIGHT = WORKING_ROW
    

def build_lighting(props, nodes, connect, used_images, shvar, column_pos):
    # if lighting is used...
    if props.use_dir_light:
        FRAME_OFFSET = -50
        # lighting_frame = nodes.new("NodeFrame")
        # lighting_frame.name  = "Local Lighting"
        # lighting_frame.label = "Local Lighting"
        # lighting_frame.location = (0, 0)
        
        diffuse_lighting_frame = nodes.new("NodeFrame")
        diffuse_lighting_frame.name  = "Diffuse Lighting"
        diffuse_lighting_frame.label = "Diffuse Lighting"
    
        diffuse_lighting_frame.location = (column_pos, shvar.TREE_HEIGHT + FRAME_OFFSET)
        
        WORKING_COLUMN = 0
        CONTRIB_HEIGHT = 0
        #############
        # DIRLAMP 1 #
        #############
        # Lambert term
        LIGHT_DIRECTION = SceneVectorAttribute(nodes,"dir_light_direction", "LightDirection", (WORKING_COLUMN, 0), diffuse_lighting_frame)
        WORKING_COLUMN += 200
        normed_light_dir = mk_normalize_node(nodes, "Normalized Light Direction", (WORKING_COLUMN, 0), diffuse_lighting_frame)
        WORKING_COLUMN += 200
        connect(LIGHT_DIRECTION, normed_light_dir.inputs[0])
        
        LAMBERT_TERM = dot_vector(nodes, connect, normed_light_dir.outputs[0], shvar.NORMAL, "Lambert Term", (WORKING_COLUMN, 0), diffuse_lighting_frame)
        
        # If specular?
        # Specular Intensity vector
        RAW_HALF_VECTOR = add_vectors(nodes, connect, normed_light_dir.outputs[0], shvar.VVIEW, "Raw Half Vector", (WORKING_COLUMN, -150), diffuse_lighting_frame)
        WORKING_COLUMN += 200
        
        HALF_VECTOR = normalize_vector(nodes, connect, RAW_HALF_VECTOR, "Half Vector", (WORKING_COLUMN, -150), diffuse_lighting_frame)
        WORKING_COLUMN += 200
        
        SPECULAR_INTENSITY = dot_vector(nodes, connect, HALF_VECTOR, shvar.NORMAL, "Specular Intensity", (WORKING_COLUMN, -200), diffuse_lighting_frame)
        WORKING_COLUMN += 200
        
        toon_shading_frame = nodes.new("NodeFrame")
        toon_shading_frame.name  = "Toon Shading"
        toon_shading_frame.label = "Toon Shading"
        toon_shading_frame.use_custom_color = True
        toon_shading_frame.color = (0.3, 0.3, 0.3)
        toon_shading_frame.parent = diffuse_lighting_frame
        toon_shading_frame.location = (WORKING_COLUMN, -30)
        use_clut = props.clut_sampler.active
        LOCAL_WORKING_COLUMN = 0
        CONTRIB_HEIGHT = -400
        if use_clut:
            ###############
            # SAMPLE CLUT #
            ###############
            # U Coordinate
            U_COORD   = multiply_add_scalars(nodes, connect, LAMBERT_TERM,        0.495, 0.500, "U Coord", (LOCAL_WORKING_COLUMN,    0), toon_shading_frame)
            V_COORD   = multiply_add_scalars(nodes, connect, SPECULAR_INTENSITY, -0.980, 0.990, "V Coord", (LOCAL_WORKING_COLUMN, -300), toon_shading_frame)
            UV_COORDS = combine_vector(nodes, connect, U_COORD, V_COORD, 0, "UV Coords", (LOCAL_WORKING_COLUMN + 200, -150), toon_shading_frame)

                    
            clut_sampler = nodes.new('ShaderNodeTexImage')
            clut_sampler.name  = "CLUTSampler"
            clut_sampler.label = "CLUTSampler"
            clut_sampler.image = used_images.get(props.clut_sampler.typename)
            clut_sampler.extension = "EXTEND"
            if clut_sampler.image is not None:
                clut_sampler.image.alpha_mode = "CHANNEL_PACKED"    
            clut_sampler.parent = toon_shading_frame
            clut_sampler.location = Vector((LOCAL_WORKING_COLUMN + 400, -100))
            connect(UV_COORDS, clut_sampler.inputs["Vector"])
            WORKING_COLUMN += 700
            
            DIFFUSE_POWER  = clut_sampler.outputs["Color"]
            if props.use_specular:
                    SPECULAR_POWER = clut_sampler.outputs["Alpha"]
                    
            CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -400)
        else:
            # Diffuse Power term
            CLAMPED_LAMBERT_TERM = maximum_scalars(nodes, connect, LAMBERT_TERM, 0., "Clamped Lambert Term", (LOCAL_WORKING_COLUMN, 0), toon_shading_frame)
            DIFFUSE_POWER = combine_color(nodes, connect, 
                                          CLAMPED_LAMBERT_TERM, CLAMPED_LAMBERT_TERM, CLAMPED_LAMBERT_TERM,
                                          "Lambert Factor", (LOCAL_WORKING_COLUMN + 200, 0), toon_shading_frame)
            
            SPEC_HEIGHT = -350
            if props.use_specular:
                # Specular Power Term
                SPEC_POWER = MaterialFloatAttribute(nodes, "specular_power", "SpecularPower", (LOCAL_WORKING_COLUMN, SPEC_HEIGHT - 150), toon_shading_frame)
                SPEC_COEFF = subtract_scalars(nodes, connect, 1, SPECULAR_INTENSITY, "1-d", (LOCAL_WORKING_COLUMN, SPEC_HEIGHT - 450), toon_shading_frame)
                SPEC_DENOM = multiply_add_scalars(nodes, connect, SPEC_COEFF, SPEC_POWER, SPECULAR_INTENSITY, "SpecPow*(1-d) + d", (LOCAL_WORKING_COLUMN + 200, SPEC_HEIGHT - 250), toon_shading_frame)
                SPEC_RATIO = divide_scalars(nodes, connect, SPECULAR_INTENSITY, SPEC_DENOM, "Specular Ratio", (LOCAL_WORKING_COLUMN + 400, SPEC_HEIGHT - 150), toon_shading_frame)
                CLAMPED_SPECULAR = maximum_scalars(nodes, connect, SPEC_RATIO, 0., "Modulated Specular", (LOCAL_WORKING_COLUMN + 600, SPEC_HEIGHT - 150), toon_shading_frame)

                CLIPPED_LAMBERT = ceil_scalar(nodes, connect, CLAMPED_LAMBERT_TERM, "Clipped Lambert Term", (LOCAL_WORKING_COLUMN + 600, SPEC_HEIGHT), toon_shading_frame)
                SPECULAR_POWER  = multiply_scalars(nodes, connect, CLIPPED_LAMBERT, CLAMPED_SPECULAR, "Full Specular Power", (LOCAL_WORKING_COLUMN + 800, SPEC_HEIGHT), toon_shading_frame)
                
                WORKING_COLUMN += 1000
                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, SPEC_HEIGHT - 650)
            else:    
                WORKING_COLUMN += 400
                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, SPEC_HEIGHT)
            
        # Light color
        light_color = SceneColorAttribute(nodes, "dir_light_color", "Light Color", (WORKING_COLUMN, -200), diffuse_lighting_frame)
        
        shvar.DIFFUSE_LIGHTING_COLOR = multiply_colors(nodes, connect, DIFFUSE_POWER, light_color.RGB, "Diffuse Lighting", (WORKING_COLUMN + 200, 0), diffuse_lighting_frame)
        
        if props.use_specular:
            ###########################
            # BUILD SPECULAR STRENGTH #
            ###########################
            if props.use_specular_map:
                if props.specular_map_channel == "ColorSamplerA" and shvar.COLOR_SAMPLER_ALPHA is not None:
                    SPECULAR_STRENGTH = shvar.COLOR_SAMPLER_ALPHA
                elif props.specular_map_channel == "NormalSamplerA" and shvar.NORMAL_SAMPLER_ALPHA is not None:
                    SPECULAR_STRENGTH = shvar.NORMAL_SAMPLER_ALPHA
                else:
                    raise ValueError(f"Unknown specular map channel '{props.specular_map_channel}'")
            else:
                SPECULAR_STRENGTH = MaterialFloatAttribute(nodes, "specular_strength", "SpecularStrength", (WORKING_COLUMN, -480), diffuse_lighting_frame)
                WORKING_COLUMN += 200
            
            M_FULL_SPEC_POWER = multiply_scalars(nodes, connect, SPECULAR_POWER, SPECULAR_STRENGTH, "Modulated Full Spec Power", (WORKING_COLUMN, -380), diffuse_lighting_frame)
            shvar.SPECULAR_LIGHTING_COLOR = scale_vector(nodes, connect, shvar.DIFFUSE_LIGHTING_COLOR, M_FULL_SPEC_POWER, "Specular Lighting", (WORKING_COLUMN + 200, -380), diffuse_lighting_frame)

            WORKING_COLUMN += 400
            CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -680)
            
        ##############
        # SUBSURFACE #
        ##############
        if props.use_velvet_strength:
            velvet_frame = nodes.new("NodeFrame")
            velvet_frame.name  = "Subsurface/Velvet"
            velvet_frame.label = "Subsurface/Velvet"
            velvet_frame.use_custom_color = True
            velvet_frame.color = (0.3, 0.3, 0.3)
            velvet_frame.parent = diffuse_lighting_frame
            velvet_frame.location = (WORKING_COLUMN, 0)
            
            VELVET_STRENGTH = MaterialFloatAttribute(nodes, "velvet_strength", "VelvetStrength", (0, -200), velvet_frame)
            ROLLOFF         = MaterialFloatAttribute(nodes, "rolloff",         "Rolloff",        (0, -400), velvet_frame)
            NEG_ROLLOFF     = multiply_scalars(nodes, connect, ROLLOFF, -1, "-Rolloff", (0 + 200, -400), velvet_frame)

            SURFACE_COLOR    = MaterialColorAttribute(nodes, "surface_color",    "SurfaceColor",    (0, -600), velvet_frame)
            SUBSURFACE_COLOR = MaterialColorAttribute(nodes, "subsurface_color", "SubSurfaceColor", (0, -800), velvet_frame)
            
            if props.use_fuzzy_spec_color:
                FUZZY_SPEC_COLOR = MaterialColorAttribute(nodes, "fuzzy_spec_color", "FuzzySpecColor", (0, -1000), velvet_frame)
            
            def smoothstep(column_offset, row_offset, a, b, x):  
                SMOOTHSTEP_1 = clamp_scalars(nodes, connect, x, a, "t", (column_offset, row_offset-100), velvet_frame)
                SMOOTHSTEP_2 = multiply_add_scalars(nodes, connect, SMOOTHSTEP_1, -2., 3., "3 - 2t", (column_offset + 200, row_offset), velvet_frame)
                SMOOTHSTEP_3 = multiply_scalars(nodes, connect, SMOOTHSTEP_1, SMOOTHSTEP_1, "t^2", (column_offset + 200, row_offset - 200), velvet_frame)
                return multiply_scalars(nodes, connect, SMOOTHSTEP_2, SMOOTHSTEP_3, "(t^2)*(3-2t)", (column_offset + 400, row_offset-100), velvet_frame)
        
            sublambert_term_1 = smoothstep(400, -200, NEG_ROLLOFF, 1.0, LAMBERT_TERM)
            sublambert_term_2 = smoothstep(400, -600,         0.0, 1.0, LAMBERT_TERM)
    
            SUBLAMBERT_TERM = subtract_scalars(nodes, connect, sublambert_term_1, sublambert_term_2, "SubLambert Term", (1200, -450), velvet_frame)
            SUBLAMBERT_TERM.node.use_clamp = True
            SUBCOLOR_CONTRIB = scale_vector(nodes ,connect, SUBSURFACE_COLOR.RGB, SUBLAMBERT_TERM, "Subcolor Contribution", (1400, -450), velvet_frame)            

            VELVET_SUBCOLOR_CONTRIB = scale_vector(nodes, connect, SUBCOLOR_CONTRIB, VELVET_STRENGTH, "* Strength", (1600, 0), velvet_frame)

            if shvar.DIFFUSE_LIGHTING_COLOR is not None:
                lighting = shvar.DIFFUSE_LIGHTING_COLOR
            else:
                lighting = [0., 0., 0.]
            
            shvar.DIFFUSE_LIGHTING_COLOR = multiply_add_vectors(nodes, connect, lighting, SURFACE_COLOR.RGB, VELVET_SUBCOLOR_CONTRIB, "+ Diffuse Subsurface", (1800, 0), velvet_frame)
            CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -1000)
            
            if props.use_fuzzy_spec_color and props.use_specular:
                INV_SPEC_FAC       = dot_vector(nodes, connect, shvar.VVIEW, shvar.NORMAL, "Inverse Specular Factor", (400, -1000), velvet_frame)
                SPEC_FAC           = subtract_scalars(nodes, connect, 1., INV_SPEC_FAC, "Specular Factor", (600, -1000), velvet_frame)
                VELVET_SPEC_FAC    = multiply_scalars(nodes, connect, SPEC_FAC, VELVET_STRENGTH, "Velvet Specular Factor", (800, -1000), velvet_frame)
                FUZZY_SPEC_CONTRIB = scale_vector(nodes, connect, FUZZY_SPEC_COLOR.RGB, VELVET_SPEC_FAC, "Subcolor Contribution", (1000, -1000), velvet_frame) 
                
                lighting = [0., 0., 0.] if shvar.SPECULAR_LIGHTING_COLOR is None else shvar.SPECULAR_LIGHTING_COLOR
                shvar.SPECULAR_LIGHTING_COLOR  = add_vectors(nodes, connect, lighting, FUZZY_SPEC_CONTRIB, "+ Specular Subsurface", (1200, -1000), velvet_frame)

                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -1200)
            
            WORKING_COLUMN += 2000
        
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + WORKING_COLUMN)
        shvar.TREE_HEIGHT += CONTRIB_HEIGHT + FRAME_OFFSET


def build_reflections(props, nodes, connect, used_images, shvar, column_pos):
    if props.use_reflections:
        reflections_frame = nodes.new("NodeFrame")
        reflections_frame.name  = "Reflections"
        reflections_frame.label = "Reflections"
        reflections_frame.location = (column_pos, shvar.TREE_HEIGHT)
        
        WORKING_COLUMN = 0
        
        #####################
        # REFLECTION VECTOR #
        #####################
        reflection_vector_frame = nodes.new("NodeFrame")
        reflection_vector_frame.name  = "Reflection Vector"
        reflection_vector_frame.label = "Reflection Vector"
        reflection_vector_frame.use_custom_color = True
        reflection_vector_frame.color = (0.3, 0.3, 0.3)
        reflection_vector_frame.parent = reflections_frame
        reflection_vector_frame.location = (0, 0)
        
        inverted_raycast = nodes.new("ShaderNodeVectorMath")
        inverted_raycast.operation = "SCALE"
        inverted_raycast.name  = "Inverted Raycast"
        inverted_raycast.label = "Inverted Raycast"
        inverted_raycast.parent = reflection_vector_frame
        inverted_raycast.location = Vector((0, 0))
        connect(shvar.VVIEW, inverted_raycast.inputs[0])
        inverted_raycast.inputs[3].default_value = -1.
        
        inverted_normal = nodes.new("ShaderNodeVectorMath")
        inverted_normal.operation = "SCALE"
        inverted_normal.name  = "Inverted Normal"
        inverted_normal.label = "Inverted Normal"
        inverted_normal.parent = reflection_vector_frame
        inverted_normal.location = Vector((0, -200))
        connect(shvar.NORMAL, inverted_normal.inputs[0])
        inverted_normal.inputs[3].default_value = -1.
        
        reflection_vector = nodes.new('ShaderNodeVectorMath')
        reflection_vector.operation = "REFLECT"
        reflection_vector.name  = "Reflection Vector"
        reflection_vector.label = "Reflection Vector"
        reflection_vector.parent = reflection_vector_frame
        reflection_vector.location = Vector((200, -50))
        connect(inverted_raycast.outputs[0], reflection_vector.inputs[0])
        connect(inverted_normal .outputs[0], reflection_vector.inputs[1])
        
        WORKING_COLUMN += 450
        
        # TODO
        # if layer_1_distortion:
        #     distort...
        
        
        ######################
        # REFLECTION TEXTURE #
        ######################
        reflection_texture_frame = nodes.new("NodeFrame")
        reflection_texture_frame.name  = "Reflection Texture"
        reflection_texture_frame.use_custom_color = True
        reflection_texture_frame.color = (0.3, 0.3, 0.3)
        reflection_texture_frame.parent = reflections_frame
        reflection_texture_frame.location = (WORKING_COLUMN, 0)

        if props.env_sampler.active:
            reflection_texture_frame.label = "Cubemap"
            
            u_coordinate = nodes.new('ShaderNodeVectorMath')
            u_coordinate.operation = "DOT_PRODUCT"
            u_coordinate.name  = "U Coordinate"
            u_coordinate.label = "U Coordinate"
            u_coordinate.parent = reflection_texture_frame
            u_coordinate.location = Vector((0, 0))
            connect(reflection_vector.outputs["Vector"], u_coordinate.inputs[0])
            u_coordinate.inputs[1].default_value[0] = -1.
            u_coordinate.inputs[1].default_value[1] =  1.
            u_coordinate.inputs[1].default_value[2] =  0.
            
            v_coordinate = nodes.new('ShaderNodeVectorMath')
            v_coordinate.operation = "DOT_PRODUCT"
            v_coordinate.name  = "V Coordinate"
            v_coordinate.label = "V Coordinate"
            v_coordinate.parent = reflection_texture_frame
            v_coordinate.location = Vector((0, -300))
            connect(reflection_vector.outputs["Vector"], v_coordinate.inputs[0])
            v_coordinate.inputs[1].default_value[0] =  0.
            v_coordinate.inputs[1].default_value[1] =  1.
            v_coordinate.inputs[1].default_value[2] = -1.
            
            uv_coord = nodes.new('ShaderNodeCombineXYZ')
            uv_coord.name  = "UV Coords"
            uv_coord.label = "UV Coords"
            uv_coord.parent = reflection_texture_frame
            uv_coord.location = Vector((200, 0))
            connect(u_coordinate.outputs[1], uv_coord.inputs[0])
            connect(v_coordinate.outputs[1], uv_coord.inputs[1])
            
            refl_sampler = nodes.new('ShaderNodeTexImage')
            refl_sampler.name  = "EnvSampler"
            refl_sampler.label = "EnvSampler"
            refl_sampler.image = used_images.get(props.env_sampler.typename)
            refl_sampler.parent = reflection_texture_frame
            refl_sampler.location = Vector((400, 0))
            connect(uv_coord.outputs[0], refl_sampler.inputs["Vector"])
            
            REFLECTION_COLOR = refl_sampler.outputs["Color"]
            REFLECTION_ALPHA = refl_sampler.outputs["Alpha"]
            
            WORKING_COLUMN += 700
        elif props.envs_sampler.active:
            reflection_texture_frame.label = "Spheremap"
        
            refl_vector = reflection_vector.outputs["Vector"]
            offset_vector = add_vectors   (nodes, connect, refl_vector,   [0., 0., 1.], "Offset Reflection Vector",   (0, -200), reflection_texture_frame)
            length        = length_vector (nodes, connect, offset_vector,               "Offset Vector Length",     (200, -200), reflection_texture_frame)
            divisor       = divide_scalars(nodes, connect,           0.5,       length, "Divisor",                  (400, -200), reflection_texture_frame)
            scaled_refl   = scale_vector  (nodes, connect, refl_vector,        divisor, "Scaled Reflection",        (600,    0), reflection_texture_frame)
            uv_coord      = add_vectors   (nodes, connect, scaled_refl, [0.5, 0.5, 0.], "UV Coords",                (800,    0), reflection_texture_frame)
        
            refl_sampler = nodes.new('ShaderNodeTexImage')
            refl_sampler.name  = "EnvsSampler"
            refl_sampler.label = "EnvsSampler"
            refl_sampler.image = used_images.get(props.envs_sampler.typename)
            refl_sampler.parent = reflection_texture_frame
            refl_sampler.location = Vector((1000, 0))
            connect(uv_coord, refl_sampler.inputs["Vector"])
            
            REFLECTION_COLOR = refl_sampler.outputs["Color"]
            REFLECTION_ALPHA = refl_sampler.outputs["Alpha"]
            
            WORKING_COLUMN += 1300
        else:
            REFLECTION_COLOR = [0., 0., 0.]
            REFLECTION_ALPHA = 1.
        
        #######################
        # REFLECTION STRENGTH #
        #######################
        # Reflection Strength
        REFLECTION_STRENGTH = MaterialFloatAttribute(nodes, "reflection_strength", "ReflectionStrength", (0, -600), reflections_frame)
        REFLECTION_COLUMN = 200
        # Fresnel
        if (props.use_fresnel_min or props.use_fresnel_exp):
            fresnel_frame = nodes.new("NodeFrame")
            fresnel_frame.name  = "Fresnel Effect"
            fresnel_frame.label = "Fresnel Effect"
            fresnel_frame.use_custom_color = True
            fresnel_frame.color = (0.3, 0.3, 0.3)
            fresnel_frame.parent = reflections_frame
            fresnel_frame.location = (200, -600)
                        
            # Incident Angle
            incident_angle = nodes.new("ShaderNodeVectorMath")
            incident_angle.operation = "DOT_PRODUCT"
            incident_angle.name  = "Incident Angle"
            incident_angle.label = "Incident Angle"
            incident_angle.parent = fresnel_frame
            incident_angle.location = Vector((000, -200))
            connect(shvar.VVIEW,  incident_angle.inputs[0])
            connect(shvar.NORMAL, incident_angle.inputs[1])
            
            abs_incident_angle = nodes.new("ShaderNodeMath")
            abs_incident_angle.operation = "ABSOLUTE"
            abs_incident_angle.name  = "Abs Incident Angle"
            abs_incident_angle.label = "Abs Incident Angle"
            abs_incident_angle.parent = fresnel_frame
            abs_incident_angle.location = Vector((200, -200))
            connect(incident_angle.outputs[1], abs_incident_angle.inputs[0])
            
            # Fresnel Exp
            FRESNEL_EXP = MaterialFloatAttribute(nodes, "fresnel_exp", "FresnelExp", (0, -400), fresnel_frame)
            
            # Inverted Exponent
            inv_fresnel_exp = nodes.new('ShaderNodeMath')
            inv_fresnel_exp.operation = "DIVIDE"
            inv_fresnel_exp.name  = "Inverse FresnelExp"
            inv_fresnel_exp.label = "Inverse FresnelExp"
            inv_fresnel_exp.parent = fresnel_frame
            inv_fresnel_exp.location = Vector((200, -400))
            inv_fresnel_exp.inputs[0].default_value = 1.
            connect(FRESNEL_EXP, inv_fresnel_exp.inputs[1])

            # Interpolation Value
            interpolation_value = nodes.new("ShaderNodeMath")
            interpolation_value.operation = "POWER"
            interpolation_value.name  = "Interpolation Value"
            interpolation_value.label = "Interpolation Value"
            interpolation_value.parent = fresnel_frame
            interpolation_value.location = Vector((400, -200))
            connect(abs_incident_angle.outputs[0], interpolation_value.inputs[0])
            connect(inv_fresnel_exp.outputs[0], interpolation_value.inputs[1])
            
            # Fresnel Min
            FRESNEL_MIN = MaterialFloatAttribute(nodes, "fresnel_min", "FresnelMin", (0, -600), fresnel_frame)
            
            # Minimum Reflection value
            min_reflection_strength = nodes.new('ShaderNodeMath')
            min_reflection_strength.operation = "MULTIPLY"
            min_reflection_strength.name  = "Minimum Reflection Strength"
            min_reflection_strength.label = "Minimum Reflection Strength"
            min_reflection_strength.parent = fresnel_frame
            min_reflection_strength.location = Vector((200, -600))
            connect(REFLECTION_STRENGTH, min_reflection_strength.inputs[0])
            connect(FRESNEL_MIN,         min_reflection_strength.inputs[1])
            
            # Fresnel Effect Reflection Strength
            fresnel_effect = nodes.new('ShaderNodeMix')
            fresnel_effect.data_type = "FLOAT"
            fresnel_effect.blend_type = "MIX"
            fresnel_effect.clamp_result = False
            fresnel_effect.clamp_factor = True
            fresnel_effect.name  = "Fresnel Effect Reflection Strength"
            fresnel_effect.label = "Fresnel Effect Reflection Strength"
            fresnel_effect.parent = fresnel_frame
            fresnel_effect.location = Vector((800, 0))
            connect(interpolation_value    .outputs[0], fresnel_effect.inputs[0])
            connect(REFLECTION_STRENGTH,                fresnel_effect.inputs[2])
            connect(min_reflection_strength.outputs[0], fresnel_effect.inputs[3])
            
            REFLECTION_STRENGTH = fresnel_effect.outputs[0]
            
            REFLECTION_COLUMN += 1000
        
        # Reflection RGBA
        offset = max(WORKING_COLUMN, WORKING_COLUMN)
        shvar.REFLECTION_COLOR = scale_vector    (nodes, connect, REFLECTION_COLOR, REFLECTION_STRENGTH, "Reflection Color", (offset,    0), reflections_frame)
        shvar.REFLECTION_ALPHA = multiply_scalars(nodes, connect, REFLECTION_ALPHA, REFLECTION_STRENGTH, "Reflection Alpha", (offset, -200), reflections_frame)

        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + offset)


def build_ambient_light(props, nodes, connect, shvar, column_pos):
    if props.use_ambient_light:
        ambient_frame = NodeFrame(nodes, "Ambient Lighting", (column_pos, shvar.TREE_HEIGHT), None)
        
        WORKING_COLUMN = 0
        AMBIENT_COLOR = SceneColorAttribute(nodes, "ambient_color", "AmbientColor", (WORKING_COLUMN, 0), ambient_frame).RGB
        
        if props.use_hemisph_light:
            ground_color = SceneColorAttribute(nodes,  "ground_color",  "GroundColor",  (WORKING_COLUMN, -200), ambient_frame).RGB
            sky_dir      = SceneVectorAttribute(nodes, "sky_direction", "SkyDirection", (WORKING_COLUMN, -400), ambient_frame)
            
            WORKING_COLUMN += 200
            sky_proj = dot_vector(nodes, connect, shvar.NORMAL, sky_dir, ("Sky Projection"), (WORKING_COLUMN, -250), ambient_frame)
            WORKING_COLUMN += 200
            interp_val = multiply_add_scalars(nodes, connect, sky_proj, 0.5, 0.5, "Interpolation Value", (WORKING_COLUMN, -250), ambient_frame)

            AMBIENT_COLOR = lerp_color(nodes, connect, interp_val, ground_color, AMBIENT_COLOR, "Interpolated Ambient Color", (WORKING_COLUMN, -250), ambient_frame)
        
        WORKING_COLUMN += 200
        if props.use_dir_light:
            shvar.DIFFUSE_LIGHTING_COLOR = multiply_colors(nodes, connect, shvar.DIFFUSE_LIGHTING_COLOR, AMBIENT_COLOR, "+ Ambient", (WORKING_COLUMN, 0), ambient_frame)    
            WORKING_COLUMN += 200
        

def build_specular(props, nodes, connect, shvar):
    # TODO: Implement 'obscure' in here too
    if props.use_reflections:
        if shvar.SPECULAR_LIGHTING_COLOR is not None:
            spec_contrib = nodes.new('ShaderNodeMix')
            spec_contrib.data_type = "RGBA"
            spec_contrib.blend_type = "ADD"
            spec_contrib.clamp_result = False
            spec_contrib.clamp_factor = True
            spec_contrib.name  = "Specular Contribution"
            spec_contrib.label = "Specular Contribution"
            spec_contrib.location = Vector((shvar.TREE_WIDTH, -400))
            spec_contrib.inputs["Factor"].default_value = 1.
            connect(shvar.SPECULAR_LIGHTING_COLOR, spec_contrib.inputs[6])
            connect(shvar.REFLECTION_COLOR,        spec_contrib.inputs[7])
            
            shvar.SPECULAR_COLOR = spec_contrib.outputs[2]
        else:
            shvar.SPECULAR_COLOR = shvar.REFLECTION_COLOR
        shvar.SPECULAR_ALPHA = shvar.REFLECTION_ALPHA
    elif shvar.SPECULAR_LIGHTING_COLOR is not None:
        shvar.SPECULAR_COLOR = shvar.SPECULAR_LIGHTING_COLOR    


def build_total_color(props, nodes, connect, shvar):
    shift = 0
    if props.use_dir_light:
        plus_diff_light = nodes.new('ShaderNodeMix')
        plus_diff_light.data_type = "RGBA"
        plus_diff_light.blend_type = "MULTIPLY"
        plus_diff_light.clamp_result = False
        plus_diff_light.clamp_factor = True
        plus_diff_light.name  = "+ Diffuse Lighting"
        plus_diff_light.label = "+ Diffuse Lighting"
        plus_diff_light.location = Vector((shvar.TREE_WIDTH, 0))
        plus_diff_light.inputs["Factor"].default_value = 1.
        connect(shvar.DIFFUSE_COLOR,          plus_diff_light.inputs[6])
        connect(shvar.DIFFUSE_LIGHTING_COLOR, plus_diff_light.inputs[7])
        
        shvar.DIFFUSE_COLOR = plus_diff_light.outputs[2]
        shift += 200
    
    if shvar.SPECULAR_COLOR is not None:
        plus_spec_light = nodes.new('ShaderNodeMix')
        plus_spec_light.data_type = "RGBA"
        plus_spec_light.blend_type = "ADD"
        plus_spec_light.clamp_result = False
        plus_spec_light.clamp_factor = True
        plus_spec_light.name  = "+ Specular"
        plus_spec_light.label = "+ Specular"
        plus_spec_light.location = Vector((shvar.TREE_WIDTH + 200, 0)) # Going to be shifted by either diff or spec node, 200 either way...
        plus_spec_light.inputs["Factor"].default_value = 1.
        connect(shvar.DIFFUSE_COLOR,  plus_spec_light.inputs[6])
        connect(shvar.SPECULAR_COLOR, plus_spec_light.inputs[7])
        
        shvar.DIFFUSE_COLOR = plus_spec_light.outputs[2]
        shift += 200
    
    shvar.TREE_WIDTH += shift
    

def build_GL_ALPHA(props, nodes, connect, shvar):
    if props.use_gl_alpha and props.gl_alpha_func != "INVALID" and props.gl_alpha_func != "GL_ALWAYS":
        gl_alpha_frame = nodes.new("NodeFrame")
        gl_alpha_frame.label = "glAlphaTest"
        shvar.TREE_WIDTH += 50
        gl_alpha_frame.location = (shvar.TREE_WIDTH, -600)
        
        def mk_inverter_node(input_socket, name, offset):
            node = nodes.new('ShaderNodeMath')
            node.operation = "SUBTRACT"
            node.name  = name
            node.label = name
            node.parent = gl_alpha_frame
            node.location = Vector((offset + 200, -150))
            node.inputs[0].default_value = 1.
            connect(input_socket, node.inputs[1])
            return node
        
        if props.gl_alpha_func == "GL_NEVER":
            node = nodes.new('ShaderNodeMath')
            node.operation = "MULTIPLY"
            node.name  = "Never Pass"
            node.label = "Never Pass"
            node.parent = gl_alpha_frame
            node.location = Vector((0, 0))
            connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
            node.inputs[1].default_value = 0.
            shvar.TREE_WIDTH += 200
        else:
            THRESHOLD = MaterialFloatAttribute(nodes, "gl_alpha_threshold", "Threshold", (0, -200), gl_alpha_frame)
            
            offset = 200
            if props.gl_alpha_func == "GL_LESS":
                node = nodes.new('ShaderNodeMath')
                node.operation = "LESS_THAN"
                node.name  = "Less Than"
                node.label = "Less Than"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                
                offset += 200
                TEST_RESULT = node.outputs[0]
            elif props.gl_alpha_func == "GL_LEQUAL":
                node = nodes.new('ShaderNodeMath')
                node.operation = "GREATER_THAN"
                node.name  = "Less Than/Equal To - Step 1"
                node.label = "Less Than/Equal To - Step 1"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                
                inverted = mk_inverter_node(node.outputs[0], "Less Than/Equal To - Step 2", offset)
                
                offset += 400
                TEST_RESULT = inverted.outputs[0]
            elif props.gl_alpha_func == "GL_EQUAL":
                node = nodes.new('ShaderNodeMath')
                node.operation = "COMPARE"
                node.name  = "Equal To"
                node.label = "Equal To"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                node.inputs[2].default_value = 0.
                
                offset += 200
                TEST_RESULT = node.outputs[0]
            elif props.gl_alpha_func == "GL_NOTEQUAL":
                node = nodes.new('ShaderNodeMath')
                node.operation = "COMPARE"
                node.name  = "Not Equal To - Step 1"
                node.label = "Not Equal To - Step 1"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                node.inputs[2].default_value = 0.
                
                inverted = mk_inverter_node(node.outputs[0], "Not Equal To - Step 2", offset)
                
                TEST_RESULT = inverted.outputs[0]
                offset += 400
            elif props.gl_alpha_func == "GL_GREATER":
                node = nodes.new('ShaderNodeMath')
                node.operation = "GREATER_THAN"
                node.name  = "Greater Than"
                node.label = "Greater Than"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                
                offset += 200
                TEST_RESULT = node.outputs[0]
            elif props.gl_alpha_func == "GL_GEQUAL":
                node = nodes.new('ShaderNodeMath')
                node.operation = "LESS_THAN"
                node.name  = "Greater Than/Equal To - Step 1"
                node.label = "Greater Than/Equal To - Step 1"
                node.parent = gl_alpha_frame
                node.location = Vector((offset, -150))
                connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
                connect(THRESHOLD,           node.inputs[1])
                
                inverted = mk_inverter_node(node.outputs[0], "Greater Than/Equal To - Step 2", offset)
                
                TEST_RESULT = inverted.outputs[0]
                offset += 400
                
            node = nodes.new('ShaderNodeMath')
            node.operation = "MULTIPLY"
            node.name  = "Clipped Alpha"
            node.label = "Clipped Alpha"
            node.parent = gl_alpha_frame
            node.location = Vector((offset, 0))
            connect(shvar.DIFFUSE_ALPHA, node.inputs[0])
            connect(TEST_RESULT,         node.inputs[1])
            shvar.TREE_WIDTH += offset + 200
            
            shvar.DIFFUSE_ALPHA = node.outputs[0]


def build_GL_BLEND(props, nodes, connect, shvar):
    if props.use_gl_blend:
        shvar.TREE_WIDTH += 50
        
        glblend_frame = nodes.new("NodeFrame")
        glblend_frame.name  = "glBlend"
        glblend_frame.label = "glBlend"
        glblend_frame.location = (shvar.TREE_WIDTH, 0)
        
        rgb_split = nodes.new("ShaderNodeSeparateColor")
        rgb_split.parent = glblend_frame
        rgb_split.location = Vector((0, 0))
        connect(shvar.DIFFUSE_COLOR, rgb_split.inputs[0])
        
        transparency = nodes.new("ShaderNodeBsdfTransparent")
        transparency.parent = glblend_frame
        transparency.location = Vector((0, 200))
        
        # RED
        red_emission = nodes.new("ShaderNodeEmission")
        red_emission.parent = glblend_frame
        red_emission.location = Vector((200, 100))
        red_emission.inputs["Color"].default_value = [1., 0., 0., 1.]
        
        red_shader = nodes.new("ShaderNodeMixShader")
        red_shader.parent = glblend_frame
        red_shader.location = Vector((400, 200))
        connect(rgb_split.outputs["Red"],         red_shader.inputs[0])
        connect(transparency.outputs["BSDF"],     red_shader.inputs[1])
        connect(red_emission.outputs["Emission"], red_shader.inputs[2])
        
        # GREEN
        green_emission = nodes.new("ShaderNodeEmission")
        green_emission.parent = glblend_frame
        green_emission.location = Vector((200, -100))
        green_emission.parent = glblend_frame
        green_emission.inputs["Color"].default_value = [0., 1., 0., 1.]
        
        green_shader = nodes.new("ShaderNodeMixShader")
        green_shader.parent = glblend_frame
        green_shader.location = Vector((400, 0))
        connect(rgb_split.outputs["Green"],         green_shader.inputs[0])
        connect(transparency.outputs["BSDF"],       green_shader.inputs[1])
        connect(green_emission.outputs["Emission"], green_shader.inputs[2])
        
        # BLUE
        blue_emission = nodes.new("ShaderNodeEmission")
        blue_emission.parent = glblend_frame
        blue_emission.location = Vector((200, -300))
        blue_emission.inputs["Color"].default_value = [0., 0., 1., 1.]
        
        blue_shader = nodes.new("ShaderNodeMixShader")
        blue_shader.parent = glblend_frame
        blue_shader.location = Vector((400, -200))
        connect(rgb_split.outputs["Blue"],         blue_shader.inputs[0])
        connect(transparency.outputs["BSDF"],      blue_shader.inputs[1])
        connect(blue_emission.outputs["Emission"], blue_shader.inputs[2])
        
        # ADD UP
        rg_shader = nodes.new("ShaderNodeAddShader")
        rg_shader.parent = glblend_frame
        rg_shader.location = Vector((600, 100))
        connect(red_shader  .outputs[0], rg_shader.inputs[0])
        connect(green_shader.outputs[0], rg_shader.inputs[1])
        
        rgb_shader = nodes.new("ShaderNodeAddShader")
        rgb_shader.parent = glblend_frame
        rgb_shader.location = Vector((600, -100))
        connect(rg_shader  .outputs[0], rgb_shader.inputs[0])
        connect(blue_shader.outputs[0], rgb_shader.inputs[1])
        
        shvar.DIFFUSE_COLOR = rgb_shader.outputs[0]
        shvar.TREE_WIDTH += 850
