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

def mk_mul_node(nodes, name, location, parent=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = "MULTIPLY"
    set_node_metadata(node, name, location, parent)
    return node


def mk_scale_node(nodes, name, location, parent=None):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "SCALE"
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


def multiply_scalars(nodes, connect, scalar_1, scalar_2, name, location, parent):
    product = nodes.new('ShaderNodeMath')
    product.operation = "MULTIPLY"
    set_node_metadata(product, name, location, parent)
    
    connect_scalar(connect, scalar_1, product.inputs[0])
    connect_scalar(connect, scalar_2, product.inputs[1])
    return product.outputs[0]


def normalize_vector(nodes, connect, vector, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "SCALE"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector, node.inputs[0])
    return node.outputs[0]


def scale_vector(nodes, connect, vector, scalar, name, location, parent):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = "SCALE"
    set_node_metadata(node, name, location, parent)

    connect_vector(connect, vector, node.inputs[0])
    connect_vector(connect, scalar, node.inputs[3])
    return node.outputs[0]


def lerp_scalar(nodes, connect, interpolation_value, scalar_1, scalar_2, name, location, parent):
    # Fresnel Effect Reflection Strength
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "FLOAT"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True
    set_node_metadata(lerp, name, location, parent)
    
    connect_scalar(connect, interpolation_value, lerp.outputs[0])
    connect_vector(connect, scalar_1,            lerp.outputs[2])
    connect_vector(connect, scalar_2,            lerp.outputs[3])
    return lerp.outputs[0]


def lerp_vector(nodes, connect, interpolation_value, vector_1, vector_2, name, location, parent):
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "Vector"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True
    set_node_metadata(lerp, name, location, parent)

    connect(interpolation_value, lerp.inputs[0])
    connect(vector_1, lerp.inputs[4])
    connect(vector_2, lerp.inputs[5])
    
    connect_scalar(connect, interpolation_value, lerp.outputs[0])
    connect_vector(connect, vector_1,            lerp.outputs[4])
    connect_vector(connect, vector_2,            lerp.outputs[5])
    return lerp.outputs[1]


def lerp_color(nodes, connect, interpolation_value, color_1, color_2, name, location, parent):
    lerp = nodes.new('ShaderNodeMix')
    lerp.data_type = "RGBA"
    lerp.blend_type = "MIX"
    lerp.clamp_result = False
    lerp.clamp_factor = True                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    set_node_metadata(lerp, name, location, parent)

    connect_scalar(connect, interpolation_value, lerp.outputs[0])
    connect_vector(connect, color_1,             lerp.outputs[6])
    connect_vector(connect, color_2,             lerp.outputs[7])
    return lerp.outputs[2]


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

def mk_scene_attribute_node(nodes, attr_name, name, location, parent=None):
    return mk_attribute_node(nodes, "VIEW_LAYER", f"DSCS_SceneProperties.{attr_name}", name, location, parent)

def mk_material_attribute_node(nodes, attr_name, name, location, parent=None):
    return mk_attribute_node(nodes, "OBJECT", f"active_material.DSCS_MaterialProperties.{attr_name}", name, location, parent)

def SceneColorAttribute(nodes, attr_name, name, location, parent=None):
    return ColorWrapper(mk_scene_attribute_node(nodes, attr_name, name, location, parent))

def SceneVectorAttribute(nodes, attr_name, name, location, parent=None):
    return mk_scene_attribute_node(nodes, attr_name, name, location, parent).outputs["Vector"]

def SceneFloatAttribute(nodes, attr_name, name, location, parent=None):
    return mk_scene_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]

def MaterialColorAttribute(nodes, attr_name, name, location, parent=None):
    return ColorWrapper(mk_material_attribute_node(nodes, attr_name, name, location, parent))

def MaterialVectorAttribute(nodes, attr_name, name, location, parent=None):
    return mk_material_attribute_node(nodes, attr_name, name, location, parent).outputs["Vector"]

def MaterialFloatAttribute(nodes, attr_name, name, location, parent=None):
    return mk_material_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]


# # Could do this as a smarter way to create/organise the nodes...
#
# class NodeOrganizer:
#     pass

# class NodeValue:
#     def __init__(self, socket_output, grid):
#         self.value = socket_output
#         self.grid = grid
        
#     @property
#     def node(self):
#         return self.value.node
    
#     def rename(self, value):
#         self.node.name  = value
#         self.node.label = value



# class FloatNodeValue:
#     def __add__(self, other):
#         pass
    
#     def __sub__(self, other):
#         pass
    
#     def __mul__(self, other):
#         connect = self.grid.connect
#         self_t = type(self)
#         other_t = type(other)
        
#         # Is a Scalar Node
#         if issubclass(other_t, self_t):
#             node = mk_mul_node()
#             connect(self.value,  node.inputs[0])
#             connect(other.value, node.inputs[1])
#             return node.outputs[0]
#         # Is a Vector Node
#         elif issubclass(other_t, VectorNodeValue):
#             node = mk_scale_node()
#             connect(other.value, node.inputs[0])
#             connect(self.value,  node.inputs[3])
#         # Is a scalar value
#         elif other_t in (float, int):
#             node = mk_mul_node()
#             connect(self.value,  node.inputs[0])
#             node.inputs[0].default_value = other
#         # Is a vector value
#         elif hasattr(other_t, "__iter__"):
#             node = mk_scale_node()
#             connect(self.value,  node.inputs[0])
#             node.inputs[0].default_value = other
#         else:
#             raise ValueError("Unsupported operation for types '{self_t}' and '{other_t}'")
            
#     def __div__(self, other):
#         pass


# class VectorNodeValue:
#     def __add__(self, other):
#         pass
    
#     def __sub__(self, other):
#         pass
    
#     def __mul__(self, other):
#         pass
    
#     def __div__(self, other):
#         pass


def create_driver(obj, src, bool_var=None):
    fcurve = obj.driver_add("default_value")
    fcurve.driver.type = "SCRIPTED"
    var = fcurve.driver.variables.new()
    var.name = "var"
    var.type = "SINGLE_PROP"
    target = var.targets[0]
    target.id_type = "MATERIAL"
    target.data_path = "DSCS_MaterialProperties.overlay_strength"
    fcurve.driver.expression = "var"
    if bool_var is not None:
        var = fcurve.driver.variables.new()
        var.name = "bool_var"
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "MATERIAL"
        target.data_path = "DSCS_MaterialProperties.use_overlay_strength"
        fcurve.driver.expression = "var*bool_var"


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
    props = bpy_material.DSCS_MaterialProperties
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
    # build_ambient_occlusion(...)
    # build_ambient_light(...)
    build_specular(props, nodes, connect, shvar)
    build_total_color(props, nodes, connect, shvar)
    # build_fog(...)

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
    connect(shvar.DIFFUSE_ALPHA, mix_alpha.inputs[0])
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
    
    if props.use_vertex_colors:
        vertex_color = nodes.new('ShaderNodeVertexColor')
        vertex_color.parent   = geometry_frame
        vertex_color.location = Vector((0, shvar.TREE_HEIGHT))
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
    if uv_props.use_scroll_speed:
        scroll_speed = nodes.new("ShaderNodeAttribute")
        scroll_speed.attribute_type = "OBJECT"
        scroll_speed.attribute_name = f"active_material.DSCS_MaterialProperties.uv_{idx}.scroll_speed"
        scroll_speed.name  = "Scroll Speed"
        scroll_speed.label = "Scroll Speed"
        scroll_speed.parent = frame
        scroll_speed.location = Vector((offset, -200))

        # if shvar.TIME is None:
        scroll_offset = nodes.new("ShaderNodeVectorMath")
        scroll_offset.operation = "SCALE"
        scroll_offset.name  = "Scroll Offset"
        scroll_offset.label = "Scroll Offset"
        scroll_offset.parent = frame
        scroll_offset.location = Vector((offset + 200, -200))
        connect(scroll_speed.outputs["Vector"], scroll_offset.inputs[0])
        if shvar.TIME is None:
            scroll_offset.inputs[3].default_value = 0.
        else:
            connect(shvar.TIME,                 scroll_offset.inputs[3])
            
        plus_scroll = nodes.new("ShaderNodeVectorMath")
        plus_scroll.operation = "ADD"
        plus_scroll.name  = "+ Scroll"
        plus_scroll.label = "+ Scroll"
        plus_scroll.parent = frame
        plus_scroll.location = Vector((offset + 400, 0))
        connect(UV,                       plus_scroll.inputs[0])
        connect(scroll_offset.outputs[0], plus_scroll.inputs[1])
        
        UV = plus_scroll.outputs[0]
        offset += 600
        tree_height = min(tree_height, -450)
    
    # UV Rotation
    if uv_props.use_rotation:
        rotation = nodes.new("ShaderNodeAttribute")
        rotation.attribute_type = "OBJECT"
        rotation.attribute_name = f"active_material.DSCS_MaterialProperties.uv_{idx}.rotation"
        rotation.name  = "Rotation"
        rotation.label = "Rotation"
        rotation.parent = frame
        rotation.location = Vector((offset, -200))
    
        # Rotation needs to be an rotation about the vector (0., 0., 1.) through the point (0.5, 0.5, 0.0)
        # Probably doable by defining the rotation vector as (0.5, 0.5, 0.) and providing the angle?
        # Rotation plane might also be tangent to the rotation vector, 
        # meanining that the input vector requires offsetting...
        plus_rotation = nodes.new("ShaderNodeVectorRotate")
        plus_rotation.rotation_type = "Z_AXIS"
        plus_rotation.name  = "+ Rotation"
        plus_rotation.label = "+ Rotation"
        plus_rotation.parent = frame
        plus_rotation.location = Vector((offset + 200, 0))
        connect(UV, plus_rotation.inputs[0])
        plus_rotation.inputs[1].default_value = [0.5, 0.5, 0.]
        connect(rotation.outputs["Fac"], plus_rotation.inputs[3])
        
        UV = plus_rotation.outputs[0]
        offset += 400
        tree_height = min(tree_height, -400)

    # UV Offset
    if uv_props.use_offset:
        offset_node = nodes.new("ShaderNodeAttribute")
        offset_node.attribute_type = "OBJECT"
        offset_node.attribute_name = f"active_material.DSCS_MaterialProperties.uv_{idx}.offset"
        offset_node.name  = "Offset"
        offset_node.label = "Offset"
        offset_node.parent = frame
        offset_node.location = Vector((offset, -200))
            
        plus_offset = nodes.new("ShaderNodeVectorMath")
        plus_offset.operation = "ADD"
        plus_offset.name  = "+ Offset"
        plus_offset.label = "+ Offset"
        plus_offset.parent   = frame
        plus_offset.location = Vector((offset+200, 0))
        connect(UV,                            plus_offset.inputs[0])
        connect(offset_node.outputs["Vector"], plus_offset.inputs[1])
        
        UV = plus_offset.outputs[0]
        offset += 400
        tree_height = min(tree_height, -400)

    # UV Scale
    if uv_props.use_scale:
        scale = nodes.new("ShaderNodeAttribute")
        scale.attribute_type = "OBJECT"
        scale.attribute_name = f"active_material.DSCS_MaterialProperties.uv_{idx}.scale"
        scale.name  = "Scale"
        scale.label = "Scale"
        scale.parent = frame
        scale.location = Vector((offset, -200))
        
        plus_scale = nodes.new("ShaderNodeVectorMath")
        plus_scale.operation = "MULTIPLY"
        plus_scale.name  = "+ Scale"
        plus_scale.label = "+ Scale"
        plus_scale.parent   = frame
        plus_scale.location = Vector((offset + 200, 0))
        connect(UV,                      plus_scale.inputs[0])
        connect(scale.outputs["Vector"], plus_scale.inputs[1])
        
        UV = plus_scale.outputs[0]
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
        diffuse_color = nodes.new('ShaderNodeAttribute')
        diffuse_color.attribute_type = "OBJECT"
        diffuse_color.attribute_name = "active_material.DSCS_MaterialProperties.diffuse_color"
        diffuse_color.name  = "Diffuse Color"
        diffuse_color.label = "Diffuse Color"
        diffuse_color.parent = samplers_frame
        diffuse_color.location =  Vector((0, HEIGHT))
        
        NODES_HEIGHT = INCREMENT
        DIFFUSE_COLOR = diffuse_color.outputs["Color"]
        DIFFUSE_ALPHA = diffuse_color.outputs["Alpha"]
    
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
        overlay_strength = nodes.new('ShaderNodeAttribute')
        overlay_strength.attribute_type = "OBJECT"
        overlay_strength.attribute_name = "active_material.DSCS_MaterialProperties.overlay_strength"
        overlay_strength.name  = "OverlayStrength"
        overlay_strength.label = "OverlayStrength"
        overlay_strength.parent = overlay_frame
        overlay_strength.location =  Vector((WIDTH, 0))
        WIDTH += 200
        
        OVERLAY_FACTOR = overlay_strength.outputs["Fac"]
        
        # Overlay color alpha
        overlay_factor = nodes.new('ShaderNodeMath')
        overlay_factor.operation = "MULTIPLY"
        overlay_factor.name  = "* Overlay Color Alpha"
        overlay_factor.label = "* Overlay Color Alpha"
        overlay_factor.parent = overlay_frame
        overlay_factor.location = Vector((200, 0))
        WIDTH += 200
        
        connect(OVERLAY_FACTOR,   overlay_factor.inputs[0])
        overlay_factor.inputs[1].default_value = 1.
        if shvar.OVERLAY_COLOR_SAMPLER_ALPHA is not None:
            connect(shvar.OVERLAY_COLOR_SAMPLER_ALPHA, overlay_factor.inputs[1])
        OVERLAY_FACTOR = overlay_factor.outputs[0]
        
        # Vertex alpha
        if props.use_overlay_vertex_alpha and shvar.VERTEX_ALPHA is not None:
            overlay_factor = nodes.new('ShaderNodeMath')
            overlay_factor.operation = "MULTIPLY"
            overlay_factor.name  = "* Vertex Alpha"
            overlay_factor.label = "* Vertex Alpha"
            overlay_factor.parent = overlay_frame
            overlay_factor.location = Vector((WIDTH, 0))
            WIDTH += 200
                
            connect(OVERLAY_FACTOR,     overlay_factor.inputs[0])
            connect(shvar.VERTEX_ALPHA, overlay_factor.inputs[1])
            OVERLAY_FACTOR = overlay_factor.outputs[0]
        
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + WIDTH + 30)
        shvar.OVERLAY_FACTOR = OVERLAY_FACTOR

def build_parallax(props, nodes, connect, used_images, shvar, column_pos):
    if props.use_parallax_bias_x or props.use_parallax_bias_y:
        column_pos += 100
        
        parallax_frame = nodes.new("NodeFrame")
        parallax_frame.label    = "Parallax"
        parallax_frame.location = Vector((column_pos, shvar.TREE_HEIGHT))
    
        # TODO
        # CREATE PROPERTIES FOR SELECTING MAP
        # SEE IF YOU CAN DEFINE PARALLAX_MAP_TYPE
        # TODO
        # UV SAMPLING: SPLIT/COMBINED
    
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
            
        if parallax_props is not None:
            parallax_sampler.image    = used_images.get(parallax_props.typename)
        attach_UV(parallax_sampler, parallax_props, shvar, connect)
        
        PARALLAX_CHANNEL = parallax_sampler.outputs["Alpha"]
        
        # TODO
        # CHECK IF PARALLAX IS DONE FROM TANGENT AND BITANGENT OR
        # T/B/N X and T/B/N Y
        
        #######################
        # MULTIPLICATIVE BIAS #
        #######################
        parallax_x = nodes.new('ShaderNodeAttribute')
        parallax_x.attribute_type = "OBJECT"
        parallax_x.attribute_name = "active_material.DSCS_MaterialProperties.parallax_bias_x"
        parallax_x.name  = "Parallax Bias X"
        parallax_x.label = "Parallax Bias X"
        parallax_x.parent = parallax_frame
        parallax_x.location = Vector((0, -300))
        
        mul_x = nodes.new('ShaderNodeMath')
        mul_x.operation = "MULTIPLY"
        mul_x.name  = "HEIGHT * Bias X"
        mul_x.label = "HEIGHT * Bias X"
        mul_x.parent = parallax_frame
        mul_x.location = Vector((400, 0))
        
        if PARALLAX_CHANNEL is not None:
            connect(PARALLAX_CHANNEL, mul_x.inputs[0])
        else:
            mul_x.inputs[0].default_value = 0.
        connect(parallax_x.outputs["Fac"], mul_x.inputs[1])
        
        #################
        # ADDITIVE BIAS #
        #################
        parallax_y = nodes.new('ShaderNodeAttribute')
        parallax_y.attribute_type = "OBJECT"
        parallax_y.attribute_name = "active_material.DSCS_MaterialProperties.parallax_bias_y"
        parallax_y.name  = "Parallax Bias Y"
        parallax_y.label = "Parallax Bias Y"
        parallax_y.parent = parallax_frame
        parallax_y.location = Vector((0, -500))
        
        add_y = nodes.new('ShaderNodeMath')
        add_y.operation = "ADD"
        add_y.name  = "(HEIGHT * Bias X) + Bias Y"
        add_y.label = "(HEIGHT * Bias X) + Bias Y"
        add_y.parent = parallax_frame
        add_y.location = Vector((600, 0))
        
        connect(mul_x     .outputs[0],     add_y.inputs[0])
        connect(parallax_y.outputs["Fac"], add_y.inputs[1])
        
        #######################
        # PARALLAX GENERATION #
        #######################
        x_coord = nodes.new('ShaderNodeVectorMath')
        x_coord.operation = "DOT_PRODUCT"
        x_coord.name  = "U Coord"
        x_coord.label = "U Coord"
        connect(shvar.VVIEW,   x_coord.inputs[0])
        connect(shvar.TANGENT, x_coord.inputs[1])
        x_coord.parent = parallax_frame
        x_coord.location = Vector((0, -700))
        
        y_coord = nodes.new('ShaderNodeVectorMath')
        y_coord.operation = "DOT_PRODUCT"
        y_coord.name  = "V Coord"
        y_coord.label = "V Coord"
        connect(shvar.VVIEW,    y_coord.inputs[0])
        connect(shvar.BINORMAL, y_coord.inputs[1])
        y_coord.parent = parallax_frame
        y_coord.location = Vector((0, -900))
        
        parallax_u = nodes.new('ShaderNodeMath')
        parallax_u.operation = "MULTIPLY"
        parallax_u.name  = "Parallax X"
        parallax_u.label = "Parallax X"
        parallax_u.parent = parallax_frame
        parallax_u.location = Vector((800, 0))
        connect(add_y  .outputs[0], parallax_u.inputs[0])
        connect(x_coord.outputs[1], parallax_u.inputs[1])
        
        parallax_v = nodes.new('ShaderNodeMath')
        parallax_v.operation = "MULTIPLY"
        parallax_v.name  = "Parallax Y"
        parallax_v.label = "Parallax Y"
        parallax_v.parent = parallax_frame
        parallax_v.location = Vector((800, -200))
        connect(add_y  .outputs[0], parallax_v.inputs[0])
        connect(x_coord.outputs[1], parallax_v.inputs[1])

        # Output vector
        parallax = nodes.new('ShaderNodeCombineXYZ')
        parallax.name  = "Parallax"
        parallax.label = "UV Parallax"
        parallax.parent = parallax_frame
        parallax.location = Vector((1000, 0))
        connect(parallax_u.outputs[0], parallax.inputs[0])
        connect(parallax_v.outputs[0], parallax.inputs[1])
        
        shvar.PARALLAX = parallax.outputs[0]
        
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
            
            bumpiness = nodes.new('ShaderNodeAttribute')
            bumpiness.attribute_type = "OBJECT"
            bumpiness.attribute_name = f"active_material.DSCS_MaterialProperties.{bump_attr}"
            bumpiness.name  = f"{label}Bumpiness"
            bumpiness.label = f"{label}Bumpiness"
            bumpiness.parent = bump_channel_frame
            bumpiness.location = Vector((0, -300))
        
            half_normal_sampler = nodes.new('ShaderNodeVectorMath')
            half_normal_sampler.operation = "SUBTRACT"
            half_normal_sampler.name  = f"{label} Half Normal"
            half_normal_sampler.label = f"{label} Half Normal"
            connect(sampler_color, half_normal_sampler.inputs[0])
            half_normal_sampler.inputs[1].default_value[0] = 0.5
            half_normal_sampler.inputs[1].default_value[1] = 0.5
            half_normal_sampler.inputs[1].default_value[2] = 0.5
            half_normal_sampler.parent = bump_channel_frame
            half_normal_sampler.location = Vector((0, 0))
                    
            bump_map = nodes.new('ShaderNodeVectorMath')
            bump_map.operation = "SCALE"
            bump_map.name  = f"{label} Bump Map"
            bump_map.label = f"{label} Bump Map"
            connect(half_normal_sampler.outputs[0], bump_map.inputs[0])
            connect(bumpiness.outputs["Fac"],       bump_map.inputs[3])
            bump_map.parent = bump_channel_frame
            bump_map.location = Vector((200, 0))
            
            split_bump_map = nodes.new('ShaderNodeSeparateXYZ')
            split_bump_map.name  = f"Split {label} Bump Map"
            split_bump_map.label = f"Split {label} Bump Map"
            connect(bump_map.outputs[0], split_bump_map.inputs[0])
            split_bump_map.parent = bump_channel_frame
            split_bump_map.location = Vector((400, 0))
                
            x_coord = nodes.new('ShaderNodeVectorMath')
            x_coord.operation = "SCALE"
            x_coord.name  = "Tangent Influence"
            x_coord.label = "Tangent Influence"
            connect(shvar.TANGENT, x_coord.inputs[0])
            connect(split_bump_map.outputs[0], x_coord.inputs[3])
            x_coord.parent = bump_channel_frame
            x_coord.location = Vector((600, 0))
            
            y_coord = nodes.new('ShaderNodeVectorMath')
            y_coord.operation = "SCALE"
            y_coord.name  = "Binormal Influence"
            y_coord.label = "Binormal Influence"
            connect(shvar.BINORMAL, y_coord.inputs[0])
            connect(split_bump_map.outputs[1], y_coord.inputs[3])
            y_coord.parent = bump_channel_frame
            y_coord.location = Vector((600, -200))
            
            full_bump_map = nodes.new('ShaderNodeVectorMath')
            full_bump_map.operation = "ADD"
            full_bump_map.name  = f"Full {label} Bump Map"
            full_bump_map.label = f"Full {label} Bump Map"
            connect(x_coord.outputs[0], full_bump_map.inputs[0])
            connect(y_coord.outputs[0], full_bump_map.inputs[1])
            full_bump_map.parent = bump_channel_frame
            full_bump_map.location = Vector((800, 0))
            
            shvar.TREE_HEIGHT -= 500
            
            return full_bump_map.outputs[0]
        
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
            blended_bump = nodes.new('ShaderNodeMix')
            blended_bump.data_type = "VECTOR"
            blended_bump.blend_type = "MIX"
            blended_bump.clamp_result = False
            blended_bump.clamp_factor = True
            blended_bump.parent = bump_frame
            blended_bump.location = Vector((1000, -450))
            connect(shvar.OVERLAY_FACTOR, blended_bump.inputs[0])
            connect(BUMP,         blended_bump.inputs[4])
            connect(OVERLAY_BUMP, blended_bump.inputs[5])
            EXTRA_OFFSET += 300
            CONTRIB = blended_bump.outputs[1]
        elif BUMP is not None and OVERLAY_BUMP is None:
            CONTRIB = BUMP
        elif BUMP is None and OVERLAY_BUMP is not None:
            CONTRIB = OVERLAY_BUMP
            
        if CONTRIB is not None:
            bumped_normal = nodes.new('ShaderNodeVectorMath')
            bumped_normal.operation = "ADD"
            bumped_normal.name  = "Bumped Normal"
            bumped_normal.label = "Bumped Normal"
            connect(shvar.NORMAL, bumped_normal.inputs[0])
            connect(CONTRIB,      bumped_normal.inputs[1])
            bumped_normal.parent = bump_frame
            bumped_normal.location = Vector((EXTRA_OFFSET + 1000, 0))
            
            normed_normal = nodes.new('ShaderNodeVectorMath')
            normed_normal.operation = "NORMALIZE"
            normed_normal.name  = "Normalized Norm"
            normed_normal.label = "Normalized Normal"
            connect(bumped_normal.outputs[0], normed_normal.inputs[0])
            normed_normal.parent = bump_frame
            normed_normal.location = Vector((EXTRA_OFFSET + 1200, 0))
            
            shvar.NORMAL = normed_normal.outputs[0]

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

        d_strength = nodes.new('ShaderNodeAttribute')
        d_strength.attribute_type = "OBJECT"
        d_strength.attribute_name = "active_material.DSCS_MaterialProperties.distortion_strength"
        d_strength.name  = "DistortionStrength"
        d_strength.label = "DistortionStrength"
        d_strength.parent = distortion_frame
        d_strength.location = Vector((0, 0))
                
        distortion = nodes.new('ShaderNodeVectorMath')
        distortion.operation = "SCALE"
        distortion.name  = "Distortion"
        distortion.label = "Distortion"
        connect(half_normal_sampler.outputs[0], distortion.inputs[0])
        connect(d_strength.outputs["Fac"],      distortion.inputs[2])
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
        
        # Diffuse Texture Contribution
        total_diffuse_texture = nodes.new('ShaderNodeMix')
        total_diffuse_texture.data_type = "RGBA"
        total_diffuse_texture.blend_type = "MIX"
        total_diffuse_texture.clamp_result = False
        total_diffuse_texture.clamp_factor = True
        total_diffuse_texture.parent = diffuse_frame
        total_diffuse_texture.location = Vector((WORKING_COLUMN, ROW_0))
        
        # RGB only
        connect(DIFFUSE_COLOR,                     total_diffuse_texture.inputs[6])
        connect(shvar.OVERLAY_COLOR_SAMPLER_COLOR, total_diffuse_texture.inputs[7])
        if shvar.OVERLAY_FACTOR is not None:
            connect(shvar.OVERLAY_FACTOR,          total_diffuse_texture.inputs["Factor"])
        else:
            total_diffuse_texture.inputs["Factor"].default_value = 0.5
        WORKING_COLUMN += 200
        
        DIFFUSE_COLOR = total_diffuse_texture.outputs[2]
        WORKING_ROW = min(WORKING_ROW, -200)
    
    
    ##################
    # VERTEX COLOURS #
    ##################
    if shvar.VERTEX_COLOR is not None:
        vertex_color_mix = nodes.new('ShaderNodeMix')
        vertex_color_mix.data_type = "RGBA"
        vertex_color_mix.blend_type = "MULTIPLY"
        vertex_color_mix.clamp_result = False
        vertex_color_mix.clamp_factor = True
        vertex_color_mix.parent = diffuse_frame
        vertex_color_mix.location = Vector((WORKING_COLUMN, ROW_0))
    
        connect(DIFFUSE_COLOR,      vertex_color_mix.inputs[6])
        connect(shvar.VERTEX_COLOR, vertex_color_mix.inputs[7])
        vertex_color_mix.inputs["Factor"].default_value = 1.
        WORKING_COLUMN += 200
        
        DIFFUSE_COLOR = vertex_color_mix.outputs[2]
        WORKING_ROW = min(WORKING_ROW, -450)
    
        if props.use_vertex_alpha and shvar.VERTEX_ALPHA is not None:
            vertex_alpha = nodes.new('ShaderNodeMath')
            vertex_alpha.operation = "MULTIPLY"
            vertex_alpha.name  = "* Vertex Alpha"
            vertex_alpha.label = "* Vertex Alpha"
            vertex_alpha.parent = diffuse_frame
            vertex_alpha.location = Vector((WORKING_COLUMN, ROW_0))
                
            connect(DIFFUSE_ALPHA,      vertex_alpha.inputs[0])
            connect(shvar.VERTEX_ALPHA, vertex_alpha.inputs[1])
            WORKING_COLUMN += 200
            DIFFUSE_ALPHA = vertex_alpha
            
     
    #######################
    # FLAT DIFFUSE COLOUR #
    #######################
    if shvar.COLOR_SAMPLER_COLOR is not None:
        # Create flat diffuse color
        if props.use_diffuse_color:
            diffuse_color = nodes.new('ShaderNodeAttribute')
            diffuse_color.attribute_type = "OBJECT"
            diffuse_color.attribute_name = "active_material.DSCS_MaterialProperties.diffuse_color"
            diffuse_color.name  = "Diffuse Color"
            diffuse_color.label = "Diffuse Color"
            diffuse_color.parent = diffuse_frame
            diffuse_color.location = Vector((WORKING_COLUMN, -250))
            
            FLAT_DIFFUSE_COLOR = diffuse_color.outputs["Color"]
            FLAT_DIFFUSE_ALPHA = diffuse_color.outputs["Alpha"]
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
        lightmap_power = nodes.new('ShaderNodeAttribute')
        lightmap_power.attribute_type = "OBJECT"
        lightmap_power.attribute_name = "active_material.DSCS_MaterialProperties.lightmap_power"
        lightmap_power.name  = "LightmapPower"
        lightmap_power.label = "LightmapPower"
        lightmap_power.parent = diffuse_frame
        lightmap_power.location = Vector((WORKING_COLUMN, - 200))
        
        lightmap_strength = nodes.new('ShaderNodeAttribute')
        lightmap_strength.attribute_type = "OBJECT"
        lightmap_strength.attribute_name = "active_material.DSCS_MaterialProperties.lightmap_strength"
        lightmap_strength.name  = "LightmapStrength"
        lightmap_strength.label = "LightmapStrength"
        lightmap_strength.parent = diffuse_frame
        lightmap_strength.location = Vector((WORKING_COLUMN, - 400))

        lightmap_color = nodes.new("ShaderNodeVectorMath")
        lightmap_color.operation = "SCALE"
        lightmap_color.name  = "Lightmap Color"
        lightmap_color.label = "Lightmap Color"
        lightmap_color.parent = diffuse_frame
        lightmap_color.location = Vector((WORKING_COLUMN + 200, -250))
        connect(shvar.LIGHTMAP_SAMPLER_COLOR,  lightmap_color.inputs[0])
        connect(lightmap_power.outputs["Fac"], lightmap_color.inputs[3])
        
        full_lightmap_color = nodes.new('ShaderNodeMix')
        full_lightmap_color.data_type = "RGBA"
        full_lightmap_color.blend_type = "MIX"
        full_lightmap_color.clamp_result = False
        full_lightmap_color.clamp_factor = True
        full_lightmap_color.name  = "Full Lightmap Color"
        full_lightmap_color.label = "Full Lightmap Color"
        full_lightmap_color.parent = diffuse_frame
        full_lightmap_color.location = Vector((WORKING_COLUMN + 400, -250))
        connect(lightmap_strength    .outputs["Fac"], full_lightmap_color.inputs[0])
        full_lightmap_color.inputs[6].default_value[0] = 1.
        full_lightmap_color.inputs[6].default_value[1] = 1.
        full_lightmap_color.inputs[6].default_value[2] = 1.
        connect(lightmap_color.outputs[0], full_lightmap_color.inputs[7])
        
        plus_lightmap_contrib = nodes.new("ShaderNodeVectorMath")
        plus_lightmap_contrib.operation = "MULTIPLY"
        plus_lightmap_contrib.name  = "+ Lightmap"
        plus_lightmap_contrib.label = "+ Lightmap"
        plus_lightmap_contrib.parent = diffuse_frame
        plus_lightmap_contrib.location = Vector((WORKING_COLUMN + 600, -250))
        connect(DIFFUSE_COLOR,                  plus_lightmap_contrib.inputs[0])
        connect(full_lightmap_color.outputs[2], plus_lightmap_contrib.inputs[1])
        
        DIFFUSE_COLOR = plus_lightmap_contrib.outputs[0]
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
        
        ###################
        # SET UP SPECULAR #
        ###################
        # TODO
        # if use_spec_map:
        #     create spec map
        # else:
        #     spec strength
        # if use_overlay_spec_map:
        #     create overlay map
        
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
        
        lambert_term = nodes.new('ShaderNodeVectorMath')
        lambert_term.operation = "DOT_PRODUCT"
        lambert_term.name  = "Lambert Term"
        lambert_term.label = "Lambert Term"
        lambert_term.parent = diffuse_lighting_frame
        lambert_term.location = Vector((WORKING_COLUMN, 0))
        connect(normed_light_dir.outputs[0], lambert_term.inputs[0])
        connect(shvar.NORMAL,                      lambert_term.inputs[1])
        
        # If specular?
        # Specular Intensity vector
        raw_half_vector = nodes.new('ShaderNodeVectorMath')
        raw_half_vector.operation = "ADD"
        raw_half_vector.name  = "Raw Half Vector"
        raw_half_vector.label = "Raw Half Vector"
        raw_half_vector.parent = diffuse_lighting_frame
        raw_half_vector.location = Vector((WORKING_COLUMN, -150))
        connect(normed_light_dir.outputs[0], raw_half_vector.inputs[0])
        connect(shvar.VVIEW,                       raw_half_vector.inputs[1])
        WORKING_COLUMN += 200
        
        half_vector = nodes.new('ShaderNodeVectorMath')
        half_vector.operation = "NORMALIZE"
        half_vector.name  = "Half Vector"
        half_vector.label = "Half Vector"
        half_vector.parent = diffuse_lighting_frame
        half_vector.location = Vector((WORKING_COLUMN, -150))
        connect(raw_half_vector.outputs["Vector"], half_vector.inputs[0])
        WORKING_COLUMN += 200
        
        specular_intensity = nodes.new('ShaderNodeVectorMath')
        specular_intensity.operation = "DOT_PRODUCT"
        specular_intensity.name  = "Specular Intensity"
        specular_intensity.label = "Specular Intensity"
        specular_intensity.parent = diffuse_lighting_frame
        specular_intensity.location = Vector((WORKING_COLUMN, -200))
        connect(half_vector.outputs["Vector"], specular_intensity.inputs[0])
        connect(shvar.NORMAL,                  specular_intensity.inputs[1])
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
            rescaled_u = nodes.new('ShaderNodeMath')
            rescaled_u.operation = "MULTIPLY"
            rescaled_u.name  = "Rescaled U"
            rescaled_u.label = "Rescaled U"
            rescaled_u.parent = toon_shading_frame
            rescaled_u.location = Vector((LOCAL_WORKING_COLUMN, 0))
            connect(lambert_term.outputs[1], rescaled_u.inputs[0])
            rescaled_u.inputs[1].default_value = 0.495
            
            u_coord = nodes.new('ShaderNodeMath')
            u_coord.operation = "ADD"
            u_coord.name  = "V Coord"
            u_coord.label = "V Coord"
            u_coord.parent = toon_shading_frame
            u_coord.location = Vector((LOCAL_WORKING_COLUMN + 200, 0))
            connect(rescaled_u.outputs[0], u_coord.inputs[0])
            u_coord.inputs[1].default_value = 0.500
            
            # If specular?
            # V Coordinate
            rescaled_v = nodes.new('ShaderNodeMath')
            rescaled_v.operation = "MULTIPLY"
            rescaled_v.name  = "Rescaled V"
            rescaled_v.label = "Rescaled V"
            rescaled_v.parent = toon_shading_frame
            rescaled_v.location = Vector((LOCAL_WORKING_COLUMN, -300))
            connect(specular_intensity.outputs[1], rescaled_v.inputs[0])
            rescaled_v.inputs[1].default_value = 0.980
            
            v_coord = nodes.new('ShaderNodeMath')
            v_coord.operation = "ADD"
            v_coord.name  = "V Coord"
            v_coord.label = "V Coord"
            v_coord.parent = toon_shading_frame
            v_coord.location = Vector((LOCAL_WORKING_COLUMN + 200, -300))
            connect(rescaled_v.outputs[0], v_coord.inputs[0])
            v_coord.inputs[1].default_value = 0.010
            
            flipped_v_coord = nodes.new('ShaderNodeMath')
            flipped_v_coord.operation = "SUBTRACT"
            flipped_v_coord.name  = "Flipped V Coord"
            flipped_v_coord.label = "Flipped V Coord"
            flipped_v_coord.parent = toon_shading_frame
            flipped_v_coord.location = Vector((LOCAL_WORKING_COLUMN + 400, -300))
            flipped_v_coord.inputs[0].default_value = 1
            connect(v_coord.outputs[0], flipped_v_coord.inputs[1])
            
            # Output vector
            uv_coord = nodes.new('ShaderNodeCombineXYZ')
            uv_coord.name  = "UV Coords"
            uv_coord.label = "UV Coords"
            uv_coord.parent = toon_shading_frame
            uv_coord.location = Vector((LOCAL_WORKING_COLUMN + 600, -150))
            connect(u_coord        .outputs[0], uv_coord.inputs[0])
            connect(flipped_v_coord.outputs[0], uv_coord.inputs[1])
                    
            clut_sampler = nodes.new('ShaderNodeTexImage')
            clut_sampler.name  = "CLUTSampler"
            clut_sampler.label = "CLUTSampler"
            clut_sampler.image = used_images.get(props.clut_sampler.typename)
            clut_sampler.extension = "EXTEND"
            if clut_sampler.image is not None:
                clut_sampler.image.alpha_mode = "CHANNEL_PACKED"    
            clut_sampler.parent = toon_shading_frame
            clut_sampler.location = Vector((LOCAL_WORKING_COLUMN + 800, -100))
            connect(uv_coord.outputs[0], clut_sampler.inputs["Vector"])
            WORKING_COLUMN += 1100
            
            DIFFUSE_POWER  = clut_sampler.outputs["Color"]
            if props.use_specular_strength:
                    SPECULAR_POWER = clut_sampler.outputs["Alpha"]
                    
            CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -400)
        else:
            # Diffuse Power term
            clamped_lambert_term = nodes.new('ShaderNodeMath')
            clamped_lambert_term.operation = "MAXIMUM"
            clamped_lambert_term.name  = "Clamped Lambert Term"
            clamped_lambert_term.label = "Clamped Lambert Term"
            clamped_lambert_term.parent = toon_shading_frame
            clamped_lambert_term.location = Vector((LOCAL_WORKING_COLUMN, 0))
            connect(lambert_term.outputs[1], clamped_lambert_term.inputs[0])
            clamped_lambert_term.inputs[1].default_value = 0.
            
            lambert_factor = nodes.new('ShaderNodeCombineColor')
            lambert_factor.name  = "Lambert Factor"
            lambert_factor.label = "Lambert Factor"
            lambert_factor.parent = toon_shading_frame
            lambert_factor.location = Vector((LOCAL_WORKING_COLUMN + 200, 0))
            connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Red"])
            connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Green"])
            connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Blue"])
            
            DIFFUSE_POWER = lambert_factor.outputs[0]
            SPEC_HEIGHT = -350
            if props.use_specular:
                # Specular Power Term
                
                spec_power = nodes.new('ShaderNodeAttribute')
                spec_power.attribute_type = "OBJECT"
                spec_power.attribute_name = "active_material.DSCS_MaterialProperties.specular_power"
                spec_power.name  = "SpecularPower"
                spec_power.label = "SpecularPower"
                spec_power.parent = toon_shading_frame
                spec_power.location = Vector((LOCAL_WORKING_COLUMN, SPEC_HEIGHT - 150))
                
                spec_coeff = nodes.new('ShaderNodeMath')
                spec_coeff.operation = "SUBTRACT"
                spec_coeff.name  = "1-d"
                spec_coeff.label = "1-d"
                spec_coeff.parent = toon_shading_frame
                spec_coeff.location = Vector((LOCAL_WORKING_COLUMN, SPEC_HEIGHT - 450))
                spec_coeff.inputs[0].default_value = 1.
                connect(specular_intensity.outputs[1], spec_coeff.inputs[1])
                
                spec_denom = nodes.new('ShaderNodeMath')
                spec_denom.operation = "MULTIPLY_ADD"
                spec_denom.name  = "SpecPow*(1-d) + d"
                spec_denom.label = "SpecPow*(1-d) + d"
                spec_denom.parent = toon_shading_frame
                spec_denom.location = Vector((LOCAL_WORKING_COLUMN + 200, SPEC_HEIGHT - 250))
                spec_denom.inputs[0].default_value = 1.
                connect(spec_coeff.outputs[0],         spec_denom.inputs[0])
                connect(spec_power.outputs["Fac"],     spec_denom.inputs[1])
                connect(specular_intensity.outputs[1], spec_denom.inputs[2])
                
                spec_ratio = nodes.new('ShaderNodeMath')
                spec_ratio.operation = "DIVIDE"
                spec_ratio.name  = "Specular Ratio"
                spec_ratio.label = "Specular Ratio"
                spec_ratio.parent = toon_shading_frame
                spec_ratio.location = Vector((LOCAL_WORKING_COLUMN + 400, SPEC_HEIGHT - 150))
                spec_ratio.inputs[0].default_value = 1.
                connect(specular_intensity.outputs[1], spec_ratio.inputs[0])
                connect(spec_denom.outputs[0],         spec_ratio.inputs[1])
                
                modulated_spec = nodes.new('ShaderNodeMath')
                modulated_spec.operation = "MAXIMUM"
                modulated_spec.name  = "Modulated Specular"
                modulated_spec.label = "Modulated Specular"
                modulated_spec.parent = toon_shading_frame
                modulated_spec.location = Vector((LOCAL_WORKING_COLUMN + 600, SPEC_HEIGHT - 150))
                modulated_spec.inputs[0].default_value = 1.
                connect(spec_ratio.outputs[0], modulated_spec.inputs[0])
                modulated_spec.inputs[1].default_value = 0.
                
                clipped_lambert_term = nodes.new('ShaderNodeMath')
                clipped_lambert_term.operation = "CEIL"
                clipped_lambert_term.name  = "Clipped Lambert Term"
                clipped_lambert_term.label = "Clipped Lambert Term"
                clipped_lambert_term.parent = toon_shading_frame
                clipped_lambert_term.location = Vector((LOCAL_WORKING_COLUMN + 600, SPEC_HEIGHT))
                connect(clamped_lambert_term.outputs[0], clipped_lambert_term.inputs[0])
                
                full_spec_pow = nodes.new('ShaderNodeMath')
                full_spec_pow.operation = "MULTIPLY"
                full_spec_pow.name  = "Full Specular Power"
                full_spec_pow.label = "Full Specular Power"
                full_spec_pow.parent = toon_shading_frame
                full_spec_pow.location = Vector((LOCAL_WORKING_COLUMN + 800, SPEC_HEIGHT))
                connect(clipped_lambert_term.outputs[0], full_spec_pow.inputs[0])
                connect(modulated_spec      .outputs[0], full_spec_pow.inputs[1])
                
                SPECULAR_POWER = full_spec_pow.outputs[0]
                WORKING_COLUMN += 1000
                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, SPEC_HEIGHT - 650)
            else:    
                WORKING_COLUMN += 400
                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, SPEC_HEIGHT)
            
        # Light color
        light_color = SceneColorAttribute(nodes, "dir_light_color", "Light Color", (WORKING_COLUMN, -200), diffuse_lighting_frame)
        
        diffuse_lighting = nodes.new('ShaderNodeMix')
        diffuse_lighting.data_type = "RGBA"
        diffuse_lighting.blend_type = "MULTIPLY"
        diffuse_lighting.clamp_result = False
        diffuse_lighting.clamp_factor = True
        diffuse_lighting.name  = "Diffuse Lighting"
        diffuse_lighting.label = "Diffuse Lighting"
        diffuse_lighting.parent = diffuse_lighting_frame
        diffuse_lighting.location = Vector((WORKING_COLUMN + 200, 0))
        diffuse_lighting.inputs["Factor"].default_value = 1.
        connect(DIFFUSE_POWER,   diffuse_lighting.inputs[6])
        connect(light_color.RGB, diffuse_lighting.inputs[7])
        
        shvar.DIFFUSE_LIGHTING_COLOR = diffuse_lighting.outputs[2]
        
        # TODO: NEEDS TO WORK FOR SPECULAR MAPS TOO!!!!
        if props.use_specular:
            spec_strength = nodes.new('ShaderNodeAttribute')
            spec_strength.attribute_type = "OBJECT"
            spec_strength.attribute_name = "active_material.DSCS_MaterialProperties.specular_strength"
            spec_strength.name  = "SpecularStrength"
            spec_strength.label = "SpecularStrength"
            spec_strength.parent = diffuse_lighting_frame
            spec_strength.location = Vector((WORKING_COLUMN, -480))
            
            SPECULAR_STRENGTH = spec_strength.outputs["Fac"]
            
            
            m_full_spec_power = nodes.new('ShaderNodeMath')
            m_full_spec_power.operation = "MULTIPLY"
            m_full_spec_power.name  = "Modulated Full Spec Power"
            m_full_spec_power.label = "Modulated Full Spec Power"
            m_full_spec_power.parent = diffuse_lighting_frame
            m_full_spec_power.location = Vector((WORKING_COLUMN + 200, -380))
            connect(SPECULAR_POWER,    m_full_spec_power.inputs[0])
            connect(SPECULAR_STRENGTH, m_full_spec_power.inputs[1])
            
            spec_lighting = nodes.new("ShaderNodeVectorMath")
            spec_lighting.operation = "SCALE"
            spec_lighting.name  = "Specular Lighting"
            spec_lighting.label = "Specular Lighting"
            spec_lighting.parent = diffuse_lighting_frame
            spec_lighting.location = Vector((WORKING_COLUMN + 400, -380))
            connect(shvar.DIFFUSE_LIGHTING_COLOR, spec_lighting.inputs[0])
            connect(m_full_spec_power.outputs[0], spec_lighting.inputs[3])
            
            shvar.SPECULAR_LIGHTING_COLOR = spec_lighting.outputs[0]
            
            WORKING_COLUMN += 600
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
            
            
            velvet_strength = nodes.new('ShaderNodeAttribute')
            velvet_strength.attribute_type = "OBJECT"
            velvet_strength.attribute_name = "active_material.DSCS_MaterialProperties.velvet_strength"
            velvet_strength.name  = "VelvetStrength"
            velvet_strength.label = "VelvetStrength"
            velvet_strength.parent = velvet_frame
            velvet_strength.location = Vector((0, -200))
            
            rolloff = nodes.new('ShaderNodeAttribute')
            rolloff.attribute_type = "OBJECT"
            rolloff.attribute_name = "active_material.DSCS_MaterialProperties.rolloff"
            rolloff.name  = "VelvetStrength"
            rolloff.label = "VelvetStrength"
            rolloff.parent = velvet_frame
            rolloff.location = Vector((0, -400))
            
            neg_rolloff = nodes.new('ShaderNodeMath')
            neg_rolloff.operation = "MULTIPLY"
            neg_rolloff.name  = "-Rolloff"
            neg_rolloff.label = "-Rolloff"
            neg_rolloff.parent = velvet_frame
            neg_rolloff.location = Vector((0 + 200, -400))
            connect(rolloff.outputs["Fac"], neg_rolloff.inputs[0])
            neg_rolloff.inputs[1].default_value = -1
            
            surface_color = nodes.new('ShaderNodeAttribute')
            surface_color.attribute_type = "OBJECT"
            surface_color.attribute_name = "active_material.DSCS_MaterialProperties.surface_color"
            surface_color.name  = "SurfaceColor"
            surface_color.label = "SurfaceColor"
            surface_color.parent = velvet_frame
            surface_color.location = Vector((0, -600))
            
            subsurface_color = nodes.new('ShaderNodeAttribute')
            subsurface_color.attribute_type = "OBJECT"
            subsurface_color.attribute_name = "active_material.DSCS_MaterialProperties.subsurface_color"
            subsurface_color.name  = "SubSurfaceColor"
            subsurface_color.label = "SubSurfaceColor"
            subsurface_color.parent = velvet_frame
            subsurface_color.location = Vector((0, -800))
            
            if props.use_fuzzy_spec_color:
                fuzzy_spec_color = nodes.new('ShaderNodeAttribute')
                fuzzy_spec_color.attribute_type = "OBJECT"
                fuzzy_spec_color.attribute_name = "active_material.DSCS_MaterialProperties.fuzzy_spec_color"
                fuzzy_spec_color.name  = "FuzzySpecColor"
                fuzzy_spec_color.label = "FuzzySpecColor"
                fuzzy_spec_color.parent = velvet_frame
                fuzzy_spec_color.location = Vector((0, -1000))
            
            def smoothstep(column_offset, row_offset, a, b, x):  
                smoothstep_1 = nodes.new('ShaderNodeClamp')
                smoothstep_1.name  = "t"
                smoothstep_1.label = "t"
                smoothstep_1.parent = velvet_frame
                smoothstep_1.location = Vector((column_offset, row_offset-100))
                connect(x, smoothstep_1.inputs[0])
                if type(a) in (float, int): smoothstep_1.inputs[1].default_value = a
                else:                       connect(a, smoothstep_1.inputs[1])
                if type(b) in (float, int): smoothstep_1.inputs[2].default_value = b
                else:                       connect(b, smoothstep_1.inputs[2])
                
                smoothstep_2 = nodes.new('ShaderNodeMath')
                smoothstep_2.operation = "MULTIPLY_ADD"
                smoothstep_2.name  = "3 - 2t"
                smoothstep_2.label = "3 - 2t"
                smoothstep_2.parent = velvet_frame
                smoothstep_2.location = Vector((column_offset + 200, row_offset))
                connect(smoothstep_1.outputs[0], smoothstep_2.inputs[0])
                smoothstep_2.inputs[1].default_value = 2.
                smoothstep_2.inputs[2].default_value = 3.
                
                smoothstep_3 = nodes.new('ShaderNodeMath')
                smoothstep_3.operation = "MULTIPLY"
                smoothstep_3.name  = "t^2"
                smoothstep_3.label = "t^2"
                smoothstep_3.parent = velvet_frame
                smoothstep_3.location = Vector((column_offset + 200, row_offset - 200))
                connect(smoothstep_1.outputs[0], smoothstep_3.inputs[0])
                connect(smoothstep_1.outputs[0], smoothstep_3.inputs[1])
                
                smoothstep_4 = nodes.new('ShaderNodeMath')
                smoothstep_4.operation = "MULTIPLY"
                smoothstep_4.name  = "(t^2)*(3-2t)"
                smoothstep_4.label = "(t^2)*(3-2t)"
                smoothstep_4.parent = velvet_frame
                smoothstep_4.location = Vector((column_offset + 400, row_offset-100))
                connect(smoothstep_2.outputs[0], smoothstep_4.inputs[0])
                connect(smoothstep_3.outputs[0], smoothstep_4.inputs[1])
                
                return smoothstep_4.outputs[0]
        
            sublambert_term_1 = smoothstep(400, -200, neg_rolloff.outputs[0], 1.0, lambert_term.outputs[1])
            sublambert_term_2 = smoothstep(400, -600,                    0.0, 1.0, lambert_term.outputs[1])
    
            sublambert_term = nodes.new('ShaderNodeMath')
            sublambert_term.operation = "SUBTRACT"
            sublambert_term.name  = "SubLambert Term"
            sublambert_term.label = "SubLambert Term"
            sublambert_term.parent = velvet_frame
            sublambert_term.location = Vector((1200, -450))
            connect(sublambert_term_1, sublambert_term.inputs[0])
            connect(sublambert_term_2, sublambert_term.inputs[1])
            sublambert_term.use_clamp = True
            
            subcolor_contrib = nodes.new("ShaderNodeVectorMath")
            subcolor_contrib.operation = "SCALE"
            subcolor_contrib.name  = "Subcolor Contribution"
            subcolor_contrib.label = "Subcolor Contribution"
            subcolor_contrib.parent = velvet_frame
            subcolor_contrib.location = Vector((1400, -450))
            connect(subsurface_color.outputs["Color"], subcolor_contrib.inputs[0])
            connect(sublambert_term .outputs[0],       subcolor_contrib.inputs[3])
            
            velvet_subcolor_contrib = nodes.new("ShaderNodeVectorMath")
            velvet_subcolor_contrib.operation = "SCALE"
            velvet_subcolor_contrib.name  = "* Strength"
            velvet_subcolor_contrib.label = "* Strength"
            velvet_subcolor_contrib.parent = velvet_frame
            velvet_subcolor_contrib.location = Vector((1600, 0))
            velvet_subcolor_contrib.inputs[0].default_value[0] = 0.
            velvet_subcolor_contrib.inputs[0].default_value[1] = 0.
            velvet_subcolor_contrib.inputs[0].default_value[2] = 0.
            connect(subcolor_contrib.outputs[0],     velvet_subcolor_contrib.inputs[0])
            connect(velvet_strength .outputs["Fac"], velvet_subcolor_contrib.inputs[3])
            
            plus_diffuse_contrib = nodes.new("ShaderNodeVectorMath")
            plus_diffuse_contrib.operation = "MULTIPLY_ADD"
            plus_diffuse_contrib.name  = "+ Diffuse Subsurface"
            plus_diffuse_contrib.label = "+ Diffuse Subsurface"
            plus_diffuse_contrib.parent = velvet_frame
            plus_diffuse_contrib.location = Vector((1800, 0))
            plus_diffuse_contrib.inputs[0].default_value[0] = 0.
            plus_diffuse_contrib.inputs[0].default_value[1] = 0.
            plus_diffuse_contrib.inputs[0].default_value[2] = 0.
            if shvar.DIFFUSE_LIGHTING_COLOR is not None:
                connect(shvar.DIFFUSE_LIGHTING_COLOR,         plus_diffuse_contrib.inputs[0])
            connect(surface_color          .outputs["Color"], plus_diffuse_contrib.inputs[1])
            connect(velvet_subcolor_contrib.outputs[0],       plus_diffuse_contrib.inputs[2])
            
            shvar.DIFFUSE_LIGHTING_COLOR = plus_diffuse_contrib.outputs[0]
            CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -1000)
            
            if props.use_fuzzy_spec_color and props.use_specular:
                inv_spec_fac = nodes.new('ShaderNodeVectorMath')
                inv_spec_fac.operation = "DOT_PRODUCT"
                inv_spec_fac.name  = "Inverse Specular Factor"
                inv_spec_fac.label = "Inverse Specular Factor"
                inv_spec_fac.parent = velvet_frame
                inv_spec_fac.location = Vector((400, -1000))
                connect(shvar.VVIEW,  inv_spec_fac.inputs[0])
                connect(shvar.NORMAL, inv_spec_fac.inputs[1])
                
                spec_fac = nodes.new('ShaderNodeMath')
                spec_fac.operation = "SUBTRACT"
                spec_fac.name  = "Specular Factor"
                spec_fac.label = "Specular Factor"
                spec_fac.parent = velvet_frame
                spec_fac.location = Vector((600, -1000))
                spec_fac.inputs[0].default_value = 1.
                connect(inv_spec_fac.outputs[1], spec_fac.inputs[1])
                
                velvet_spec_fac = nodes.new('ShaderNodeMath')
                velvet_spec_fac.operation = "MULTIPLY"
                velvet_spec_fac.name  = "Velvet Specular Factor"
                velvet_spec_fac.label = "Velvet Specular Factor"
                velvet_spec_fac.parent = velvet_frame
                velvet_spec_fac.location = Vector((800, -1000))
                connect(spec_fac       .outputs[0],     velvet_spec_fac.inputs[0])
                connect(velvet_strength.outputs["Fac"], velvet_spec_fac.inputs[1])
                
                fuzzy_spec_contrib = nodes.new("ShaderNodeVectorMath")
                fuzzy_spec_contrib.operation = "SCALE"
                fuzzy_spec_contrib.name  = "Subcolor Contribution"
                fuzzy_spec_contrib.label = "Subcolor Contribution"
                fuzzy_spec_contrib.parent = velvet_frame
                fuzzy_spec_contrib.location = Vector((1000, -1000))
                connect(fuzzy_spec_color.outputs["Color"], fuzzy_spec_contrib.inputs[0])
                connect(velvet_spec_fac .outputs[0],       fuzzy_spec_contrib.inputs[3])
                    
                plus_spec_contrib = nodes.new("ShaderNodeVectorMath")
                plus_spec_contrib.operation = "ADD"
                plus_spec_contrib.name  = "+ Specular Subsurface"
                plus_spec_contrib.label = "+ Specular Subsurface"
                plus_spec_contrib.parent = velvet_frame
                plus_spec_contrib.location = Vector((1200, -1000))
                plus_spec_contrib.inputs[0].default_value[0] = 0.
                plus_spec_contrib.inputs[1].default_value[1] = 0.
                plus_spec_contrib.inputs[2].default_value[2] = 0.
                if shvar.SPECULAR_LIGHTING_COLOR is not None:
                    connect(shvar.SPECULAR_LIGHTING_COLOR, plus_spec_contrib.inputs[0])
                connect(fuzzy_spec_contrib.outputs[0],     plus_spec_contrib.inputs[1])
                
                shvar.SPECULAR_LIGHTING_COLOR = plus_spec_contrib.outputs[0]
                CONTRIB_HEIGHT = min(CONTRIB_HEIGHT, -1200)
            
            WORKING_COLUMN += 2000
        
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + WORKING_COLUMN)
        shvar.TREE_HEIGHT += CONTRIB_HEIGHT + FRAME_OFFSET

def build_reflections(props, nodes, connect, used_images, shvar, column_pos):
    if props.use_reflections:
        reflections_frame = nodes.new("NodeFrame")
        reflections_frame.name  = "Reflections"
        reflections_frame.label = "Reflections"
        reflections_frame.location = (column_pos, shvar.TREE_HEIGHT) # Replace with proper tree height
        
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
        
        # TODO: if reflection_map_sphere...
        reflection_texture_frame.label = "Spheremap"
        # else...
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
        
        #######################
        # REFLECTION STRENGTH #
        #######################
        # Reflection Strength
        reflection_strength = nodes.new('ShaderNodeAttribute')
        reflection_strength.attribute_type = "OBJECT"
        reflection_strength.attribute_name = "active_material.DSCS_MaterialProperties.reflection_strength"
        reflection_strength.name  = "ReflectionStrength"
        reflection_strength.label = "ReflectionStrength"
        reflection_strength.parent = reflections_frame
        reflection_strength.location = Vector((0, -600))
        
        REFLECTION_STRENGTH = reflection_strength.outputs["Fac"]
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
            fresnel_exp = nodes.new('ShaderNodeAttribute')
            fresnel_exp.attribute_type = "OBJECT"
            fresnel_exp.attribute_name = "active_material.DSCS_MaterialProperties.fresnel_exp"
            fresnel_exp.name  = "FresnelExp"
            fresnel_exp.label = "FresnelExp"
            fresnel_exp.parent = fresnel_frame
            fresnel_exp.location = Vector((0, -400))
            
            # Inverted Exponent
            inv_fresnel_exp = nodes.new('ShaderNodeMath')
            inv_fresnel_exp.operation = "DIVIDE"
            inv_fresnel_exp.name  = "Inverse FresnelExp"
            inv_fresnel_exp.label = "Inverse FresnelExp"
            inv_fresnel_exp.parent = fresnel_frame
            inv_fresnel_exp.location = Vector((200, -400))
            inv_fresnel_exp.inputs[0].default_value = 1.
            connect(fresnel_exp.outputs["Fac"], inv_fresnel_exp.inputs[1])

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
            fresnel_min = nodes.new('ShaderNodeAttribute')
            fresnel_min.attribute_type = "OBJECT"
            fresnel_min.attribute_name = "active_material.DSCS_MaterialProperties.fresnel_min"
            fresnel_min.name  = "FresnelMin"
            fresnel_min.label = "FresnelMin"
            fresnel_min.parent = fresnel_frame
            fresnel_min.location = Vector((0, -600))
            
            # Minimum Reflection value
            min_reflection_strength = nodes.new('ShaderNodeMath')
            min_reflection_strength.operation = "MULTIPLY"
            min_reflection_strength.name  = "Minimum Reflection Strength"
            min_reflection_strength.label = "Minimum Reflection Strength"
            min_reflection_strength.parent = fresnel_frame
            min_reflection_strength.location = Vector((200, -600))
            connect(REFLECTION_STRENGTH,        min_reflection_strength.inputs[0])
            connect(fresnel_min.outputs["Fac"], min_reflection_strength.inputs[1])
            
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
        reflection_color = nodes.new("ShaderNodeVectorMath")
        reflection_color.operation = "SCALE"
        reflection_color.name  = "Reflection Color"
        reflection_color.label = "Reflection Color"
        reflection_color.parent = reflections_frame
        reflection_color.location = Vector((offset, 0))
        connect(REFLECTION_COLOR,    reflection_color.inputs[0])
        connect(REFLECTION_STRENGTH, reflection_color.inputs[3])
        
        reflection_alpha = nodes.new('ShaderNodeMath')
        reflection_alpha.operation = "MULTIPLY"
        reflection_alpha.name  = "Reflection Alpha"
        reflection_alpha.label = "Reflection Alpha"
        reflection_alpha.parent = reflections_frame
        reflection_alpha.location = Vector((offset, -200))
        connect(REFLECTION_ALPHA,    reflection_alpha.inputs[0])
        connect(REFLECTION_STRENGTH, reflection_alpha.inputs[1])

        shvar.REFLECTION_COLOR = reflection_color.outputs[0]
        shvar.REFLECTION_ALPHA = reflection_alpha.outputs[0]
        
        shvar.TREE_WIDTH = max(shvar.TREE_WIDTH, column_pos + offset)


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
            threshold = nodes.new('ShaderNodeAttribute')
            threshold.attribute_type = "OBJECT"
            threshold.attribute_name = "active_material.DSCS_MaterialProperties.gl_alpha_threshold"
            threshold.name  = "Thresold"
            threshold.label = "Threshold"
            threshold.parent = gl_alpha_frame
            threshold.location = Vector((0, -200))
            THRESHOLD = threshold.outputs["Fac"]
            
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
