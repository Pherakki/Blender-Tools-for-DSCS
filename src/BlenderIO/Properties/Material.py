import bpy

from ...Core.FileFormats.Geom.GeomInterface import Material
from ..Import.ShaderNodes.BuildTree import rebuild_tree

from_shader_msg = "This is determined from the shader name."

def build_bpy_material(self):
    bpy_mat = self.id_data
    rebuild_tree(bpy_mat, self.get_texture_lookup())

def setting_updated(self, context):
    # Going via id_data allows more than just the MaterialProperties to call
    # this method: we also need to call it on the TextureSamplers parented to
    # the MaterialProperties, for example.
    bpy_mat = self.id_data
    props = bpy_mat.DSCS_MaterialProperties
    if props.bpy_dtype == "ADVANCED":
        props.build_bpy_material()


def get_sampler_active(self, sampler_name):
    material = self.id_data
    nodes = material.node_tree.nodes
    if sampler_name in nodes:
        if nodes[sampler_name].image is not None:
            return True
    return False

def get_sampler_image(self, sampler_name):
    material = self.id_data
    nodes = material.node_tree.nodes
    if sampler_name in nodes:
        if nodes[sampler_name].image is not None:
            return nodes[sampler_name].image.name
    return ''

def set_sampler_image(self, image_name, sampler_name):
    material = self.id_data
    nodes = material.node_tree.nodes
    if sampler_name in nodes:
        if image_name == "":
            return # Prevent image from being removed
            nodes[sampler_name].image = None
        else:
            nodes[sampler_name].image = bpy.data.images[image_name]

def get_sampler_uv(self, uv2_bits, uv3_bits):
    props = self.id_data.DSCS_MaterialProperties
    if get_shader_bit(props, *uv3_bits):
        return 2
    elif get_shader_bit(props, *uv2_bits):
        return 1
    else:
        return 0
    

def make_mapped_texture_sampler(sampler_name, uv2_bits, uv3_bits, split_alpha_bits):
    class TextureSampler(bpy.types.PropertyGroup):
        typename = sampler_name
        
        #active: bpy.props.BoolProperty(name="", default=False, get=lambda self: get_sampler_active(self, sampler_name))
        #image:  bpy.props.StringProperty(name="", get=lambda self: get_sampler_image(self, sampler_name), set=lambda self, value: set_sampler_image(self, value, sampler_name))
        active: bpy.props.BoolProperty(name="", default=False, update=setting_updated)
        image:  bpy.props.PointerProperty(type=bpy.types.Image, name="", update=setting_updated)
        data:   bpy.props.IntVectorProperty(name="Unknown Data", default=(0, 0, 0), size=3)
    
        uv_map: bpy.props.EnumProperty(name="UV Map", items=[("UV1", "UV1", ""), ("UV2", "UV2", ""), ("UV3", "UV3", "")],
                                       get=lambda self: get_sampler_uv(self, uv2_bits, uv3_bits),
                                       description=f"UV Map used by the sampler. {from_shader_msg}")
        split_alpha: bpy.props.BoolProperty(name="Split Alpha",
                                            get=lambda self: not get_shader_bit(self.id_data.DSCS_MaterialProperties, *split_alpha_bits),
                                            description=f"Whether to separately source UV coordinates for the alpha channel from UV1, instead of sourcing all four RGBA channels from the designated UV map. {from_shader_msg}")
    
        uv_1_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV1")
        uv_2_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV2")
        uv_3_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV3")
        
        def extract_data(self, texture_map):
            return [texture_map[self.image], *self.data]
        
    return TextureSampler

def make_texture_sampler(sampler_name):
    class TextureSampler(bpy.types.PropertyGroup):
        typename = sampler_name
        
        #active: bpy.props.BoolProperty(name="", default=False, get=lambda self: get_sampler_active(self, sampler_name))
        #image:  bpy.props.StringProperty(name="", get=lambda self: get_sampler_image(self, sampler_name), set=lambda self, value: set_sampler_image(self, value, sampler_name))
        active: bpy.props.BoolProperty(name="", default=False, update=setting_updated)
        image:  bpy.props.PointerProperty(type=bpy.types.Image, name="", update=setting_updated)
        data:   bpy.props.IntVectorProperty(name="Unknown Data", default=(0, 0, 0), size=3)
    
        uv_map: bpy.props.EnumProperty(name="UV Map", items=[("AUTO", "AUTO", "")])
        
        def extract_data(self, texture_map):
            return [texture_map[self.image], *self.data]
        
    return TextureSampler


class UVTransforms(bpy.types.PropertyGroup):
    use_scroll_speed: bpy.props.BoolProperty(name="", default=False, update=setting_updated)
    use_rotation:     bpy.props.BoolProperty(name="", default=False, update=setting_updated)
    use_offset:       bpy.props.BoolProperty(name="", default=False, update=setting_updated)
    use_scale:        bpy.props.BoolProperty(name="", default=False, update=setting_updated)
    
    scroll_speed: bpy.props.FloatVectorProperty(name="Scroll Speed", default=(0., 0.), size=2)
    rotation:     bpy.props.FloatProperty      (name="Rotation",     default=0.              )
    offset:       bpy.props.FloatVectorProperty(name="Offset",       default=(0., 0.), size=2)
    scale:        bpy.props.FloatVectorProperty(name="Scale",        default=(0., 0.), size=2)

    def set_scroll(self, uniform):
        self.use_scroll_speed = True
        self.scroll_speed = uniform.data
        
    def set_rotation(self, uniform):
        self.use_rotation = True
        self.rotation = uniform.data[0]

    def set_offset(self, uniform):
        self.use_offset = True
        self.offset = uniform.data
        
    def set_scale(self, uniform):
        self.use_scale = True
        self.scale = uniform.data
        
class UnhandledTextureSampler(bpy.types.PropertyGroup):
    image:  bpy.props.PointerProperty(type=bpy.types.Image, name="")
    data:   bpy.props.IntVectorProperty(name="Data", default=(0, 0, 0), size=3)
    
    def extract_data(self, texture_map):
        return [texture_map[self.image.name], *self.data]


class UnhandledMaterialUniform(bpy.types.PropertyGroup):
    index:  bpy.props.IntProperty(name="Index", default=0, min=0, max=255)
    dtype: bpy.props.EnumProperty(items=(
            ("FLOAT32",     "Float32",    "A single 32-bit floating-point number."),
            ("FLOAT32VEC2", "Float32*2",  "A 2-vector of floating-point numbers"  ),
            ("FLOAT32VEC3", "Float32*3",  "A 3-vector of floating-point numbers"  ),
            ("FLOAT32VEC4", "Float32*4",  "A 4-vector of floating-point numbers"  ),
            ("TEXTURE",     "Texture",    "A texture sampler"                     ),
        ), name="", default="FLOAT32")

    float32_data:     bpy.props.FloatProperty(name="")
    float32vec2_data: bpy.props.FloatVectorProperty(name="", size=2)
    float32vec3_data: bpy.props.FloatVectorProperty(name="", size=3)
    float32vec4_data: bpy.props.FloatVectorProperty(name="", size=4)
    texture_data:     bpy.props.PointerProperty(type=UnhandledTextureSampler, name="")
    
    def extract_data(self, texture_map):
        if   self.dtype == "FLOAT32":
            data = [self.float32_data]
        elif self.dtype == "FLOAT32VEC2":
            data = self.float32vec2_data
        elif self.dtype == "FLOAT32VEC3":
            data = self.float32vec3_data
        elif self.dtype == "FLOAT32VEC4":
            data = self.float32vec4_data
        elif self.dtype == "TEXTURE":
            data = self.texture_data.extract_data(texture_map)
        
        return self.index, data


class UnhandledOpenGLSetting(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="Index", subtype="UNSIGNED")
    data:  bpy.props.FloatVectorProperty(name="", size=4)


def set_shader_name(self, value):
    chunks = value.split("_")
    chunk_lengths = [len(chk) for chk in chunks]
    if len(chunks) == 4 and all(c == 8 for c in chunk_lengths):
        self["shader_name"] = value
    #else:
    #    self.report("ERROR", "Invalid shader name. Shader names must be 4 sets of 8 hexadecimal numbers, with each set separated with an underscore, e.g. '08810000_00000111_00000000_00040000'")

def get_shader_bit(self, chunk_idx, byte_idx, bit):
    chunk = self.shader_name.split("_")[chunk_idx] # 32 bits per chunk
    return (int(chunk, 16) >> (bit + (3-byte_idx)*8)) & 1# Count each byte left-to-right, and each bit in the bytes right-to-left


def set_blend_method(self):
    mat = self.id_data
    if self.use_gl_blend:
        mat.blend_method = "BLEND"
    elif self.use_gl_alpha:
        mat.blend_method = "CLIP"
        mat.alpha_threshold = 0.
    else:
        mat.blend_method = "OPAQUE"

def gl_alpha_setter(self, value):
    self["use_gl_alpha"] = value
    set_blend_method(self)

def gl_blend_setter(self, value):
    self["use_gl_blend"] = value 
    set_blend_method(self)


color_sampler_t          = make_mapped_texture_sampler("ColorSampler",         (0, 0, 5), (0, 0, 6), (0, 1, 7))
overlay_color_sampler_t  = make_mapped_texture_sampler("OverlayColorSampler",  (1, 3, 6), (1, 3, 7), (1, 3, 4))
normal_sampler_t         = make_mapped_texture_sampler("NormalSampler",        (0, 0, 1), (0, 0, 2), (0, 0, 3))
overlay_normal_sampler_t = make_mapped_texture_sampler("OverlayNormalSampler", (1, 2, 2), (1, 2, 3), (1, 2, 0))
lightmap_sampler_t       = make_mapped_texture_sampler("LightSampler",         (1, 3, 2), (1, 3, 3), (1, 3, 0))
env_sampler_t            = make_texture_sampler("EnvSampler")
envs_sampler_t           = make_texture_sampler("EnvsSampler")
clut_sampler_t           = make_texture_sampler("CLUTSampler")


def find_diffuse_map_channel(self):
    use_colormap  = get_shader_bit(self, 2, 2, 6)
    use_normalmap = get_shader_bit(self, 2, 2, 7)
    
    if not use_colormap and not use_normalmap:
        return 3 # NormalSamplerR
    elif use_colormap and not use_normalmap:
        return 0 # ColorSamplerA
    elif not use_colormap and use_normalmap:
        return 1 # NormalSamplerA
    else:
        return 2 # LightSamplerA
    
class MaterialProperties(bpy.types.PropertyGroup):
    bpy_dtype: bpy.props.EnumProperty(items=[("BASIC", "Basic", "A basic, minimalist shader that does not try to reproduce in-engine rendering"),
                                             ("ADVANCED", "Advanced", "Guesses the shader tree that should be built based on the currently active properties. Automatically rebuilds the tree if settings and changed. Be mindful that switching material properties on and off may make the material inconsistent with the shader name, which will determine the in-engine shader properties")],
                                      name="Material Preview",
                                      default="BASIC")
    
    flag_0:      bpy.props.BoolProperty(name="Unknown Flag 0", default=False )
    cast_shadow: bpy.props.BoolProperty(name="Cast Shadow",    default=True  )
    flag_2:      bpy.props.BoolProperty(name="Unknown Flag 2", default=False )
    flag_3:      bpy.props.BoolProperty(name="Unknown Flag 3", default=False )
    flag_4:      bpy.props.BoolProperty(name="Unknown Flag 4", default=False )
    flag_5:      bpy.props.BoolProperty(name="Unknown Flag 5", default=False )
    flag_6:      bpy.props.BoolProperty(name="Unknown Flag 6", default=False )
    flag_7:      bpy.props.BoolProperty(name="Unknown Flag 7", default=False )
    flag_8:      bpy.props.BoolProperty(name="Unknown Flag 8", default=False )
    flag_9:      bpy.props.BoolProperty(name="Unknown Flag 9", default=False )
    flag_10:     bpy.props.BoolProperty(name="Unknown Flag 10", default=False )
    flag_11:     bpy.props.BoolProperty(name="Unknown Flag 11", default=False )
    flag_12:     bpy.props.BoolProperty(name="Unknown Flag 12", default=False )
    flag_13:     bpy.props.BoolProperty(name="Unknown Flag 13", default=False )
    flag_14:     bpy.props.BoolProperty(name="Unknown Flag 14", default=False )
    flag_15:     bpy.props.BoolProperty(name="Unknown Flag 15", default=False )

    def get_flags(self):
        res = 0
        res |= self.flag_0      << 0x00
        res |= self.cast_shadow << 0x01
        res |= self.flag_2      << 0x02
        res |= self.flag_3      << 0x03
        res |= self.flag_4      << 0x04
        res |= self.flag_5      << 0x05
        res |= self.flag_6      << 0x06
        res |= self.flag_7      << 0x07
        res |= self.flag_8      << 0x08
        res |= self.flag_9      << 0x09
        res |= self.flag_10     << 0x0A
        res |= self.flag_11     << 0x0B
        res |= self.flag_12     << 0x0C
        res |= self.flag_13     << 0x0D
        res |= self.flag_14     << 0x0E
        res |= self.flag_15     << 0x0F
        return res
    
    flags: bpy.props.IntProperty(name="Flags", get=get_flags)

    # Should be able to remove this later...
    shader_name: bpy.props.StringProperty(name="Shader Name", default="00000000_00000000_00000000_00000000", get=lambda self: self["shader_name"], set=set_shader_name, update=setting_updated)
    
    # Properties derived from shader name
    # UV map, active lights, etc...
    use_dir_light:  bpy.props.BoolProperty(name="Use Directional Light",  get=lambda self: get_shader_bit(self, 0, 3, 0), description=f"Whether to receive directional lighting. {from_shader_msg}.")
    use_hem_light:  bpy.props.BoolProperty(name="Use Hemi-Ambient Light", get=lambda self: get_shader_bit(self, 0, 3, 5), description=f"Whether to receive hemispherical ambient lighting. {from_shader_msg}")
    use_amb_light:  bpy.props.BoolProperty(name="Use Ambient Light",      get=lambda self: get_shader_bit(self, 0, 3, 6), description=f"Whether to receive ambient lighting. {from_shader_msg}")
    
    # Vertex Attributes
    requires_normals:   bpy.props.BoolProperty(name="Requires Normals",   default=True)
    requires_tangents:  bpy.props.BoolProperty(name="Requires Tangents",  default=False)
    requires_binormals: bpy.props.BoolProperty(name="Requires Binormals", default=False)
    requires_colors:    bpy.props.BoolProperty(name="Requires Vertex Colors", default=False)
    requires_uv1:       bpy.props.BoolProperty(name="Requires UV1", default=False)
    requires_uv2:       bpy.props.BoolProperty(name="Requires UV2", default=False)
    requires_uv3:       bpy.props.BoolProperty(name="Requires UV3", default=False)
    
    # Unhandled material uniforms
    unhandled_uniforms:           bpy.props.CollectionProperty(name="Unhandled Uniforms", type=UnhandledMaterialUniform)
    active_unhandled_uniform_idx: bpy.props.IntProperty(options={'HIDDEN'})
    unhandled_settings:           bpy.props.CollectionProperty(name="Unhandled Settings", type=UnhandledOpenGLSetting)
    active_unhandled_setting_idx: bpy.props.IntProperty(options={'HIDDEN'})
    
    #####################
    # MATERIAL UNIFORMS #
    #####################
    
    # UV Transforms
    uv_1_is_projection: bpy.props.BoolProperty(name="UV1 Projection", get=lambda self: get_shader_bit(self.id_data.DSCS_MaterialProperties, 2, 0, 2), description=f"Whether the UV1 is generated from screen-space coordinates rather than vertex UVs. {from_shader_msg}")
    uv_2_is_projection: bpy.props.BoolProperty(name="UV2 Projection", get=lambda self: get_shader_bit(self.id_data.DSCS_MaterialProperties, 2, 0, 3), description=f"Whether the UV2 is generated from screen-space coordinates rather than vertex UVs. {from_shader_msg}")
    uv_3_is_projection: bpy.props.BoolProperty(name="UV3 Projection", get=lambda self: get_shader_bit(self.id_data.DSCS_MaterialProperties, 2, 0, 4), description=f"Whether the UV3 is generated from screen-space coordinates rather than vertex UVs. {from_shader_msg}")
    uv_1: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 1")
    uv_2: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 2")
    uv_3: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 3")
    
    # Texture Samplers
    color_sampler:          bpy.props.PointerProperty(type=color_sampler_t,          name=color_sampler_t         .typename)
    overlay_color_sampler:  bpy.props.PointerProperty(type=overlay_color_sampler_t,  name=overlay_color_sampler_t .typename)
    normal_sampler:         bpy.props.PointerProperty(type=normal_sampler_t,         name=normal_sampler_t        .typename)
    overlay_normal_sampler: bpy.props.PointerProperty(type=overlay_normal_sampler_t, name=overlay_normal_sampler_t.typename)
    lightmap_sampler:       bpy.props.PointerProperty(type=lightmap_sampler_t,       name=lightmap_sampler_t      .typename)
    env_sampler:            bpy.props.PointerProperty(type=env_sampler_t,            name=env_sampler_t           .typename)
    envs_sampler:           bpy.props.PointerProperty(type=envs_sampler_t,           name=envs_sampler_t          .typename)
    clut_sampler:           bpy.props.PointerProperty(type=clut_sampler_t,           name=clut_sampler_t          .typename)

    # Normal/Tex Manipulation
    use_bumpiness:         bpy.props.BoolProperty(name="Use Bumpiness", default=False, update=setting_updated)
    bumpiness:             bpy.props.FloatProperty(name="Bumpiness", default=0.)
    use_overlay_bumpiness: bpy.props.BoolProperty(name="Use Overlay Bumpiness", default=False, update=setting_updated)
    overlay_bumpiness:     bpy.props.FloatProperty(name="Overlay Bumpiness", default=0)
    use_parallax_bias_x:   bpy.props.BoolProperty(name="Use Parallax Bias X", default=False, update=setting_updated)
    parallax_bias_x:       bpy.props.FloatProperty(name="Parallax Bias X", default=0)
    use_parallax_bias_y:   bpy.props.BoolProperty(name="Use Parallax Bias Y", default=False, update=setting_updated)
    parallax_bias_y:       bpy.props.FloatProperty(name="Parallax Bias Y", default=0)
    use_distortion:        bpy.props.BoolProperty(name="Use Distortion", default=False, update=setting_updated)
    distortion_strength:   bpy.props.FloatProperty(name="Distortion Strength", default=0)

    # Colours
    use_diffuse_color:        bpy.props.BoolProperty(name="Use Diffuse Color", default=True, update=setting_updated)
    diffuse_color:            bpy.props.FloatVectorProperty(subtype="COLOR", name="DiffuseColor", default=(1., 1., 1., 1.), size=4, min=0., max=1.) 
    use_vertex_colors:        bpy.props.BoolProperty(name="Use Vertex Colors", default=False, update=setting_updated)
    use_overlay_strength:     bpy.props.BoolProperty(name="Use Overlay Strength", default=False, update=setting_updated)
    overlay_strength:         bpy.props.FloatProperty(name="OverlayStrength", default=0., min=0., max=1., subtype="FACTOR")
    use_vertex_alpha:         bpy.props.BoolProperty(name="Use Vertex Alpha", get=lambda self: get_shader_bit(self, 1, 1, 0))
    use_overlay_vertex_alpha: bpy.props.BoolProperty(name="Use Overlay Vertex Alpha", get=lambda self: get_shader_bit(self, 0, 1, 6))
    use_diffuse_str_map:      bpy.props.BoolProperty(name="Use Diffuse Strength Map", get=lambda self: get_shader_bit(self, 2, 2, 5), description=f"Whether to apply the Diffuse Color variably across the mesh according to a texture. {from_shader_msg}")
    diffuse_str_map_channel:  bpy.props.EnumProperty(name="Diffuse Map Channel", get=find_diffuse_map_channel, description="Which texture and channel to use for the diffuse strength map. {from_shader_msg}",
                                                     items=[(color_sampler_t   .typename + "A", color_sampler_t   .typename + " - Alpha", ""),
                                                            (normal_sampler_t  .typename + "A", normal_sampler_t  .typename + " - Alpha", ""),
                                                            (lightmap_sampler_t.typename + "A", lightmap_sampler_t.typename + " - Alpha", ""),
                                                            (normal_sampler_t  .typename + "R", normal_sampler_t  .typename + " - Red",   "")])

    # Lightmap
    use_lightmap_strength: bpy.props.BoolProperty(name="Use Lightmap Strength", default=False, update=setting_updated)
    lightmap_strength:     bpy.props.FloatProperty(name="Lightmap Strength", default=0.)
    use_lightmap_power:    bpy.props.BoolProperty(name="Use Lightmap Power", default=False, update=setting_updated)
    lightmap_power:       bpy.props.FloatProperty(name="Lightmap Power", default=1.)

    # Specular
    use_specular:          bpy.props.BoolProperty(name="Specular Enabled", get=lambda self: get_shader_bit(self, 0, 2, 0), description=f"Whether the shader has a specular contribution. {from_shader_msg}")
    use_specular_strength: bpy.props.BoolProperty(name="Use Specular Strength", default=False, update=setting_updated)
    specular_strength:     bpy.props.FloatProperty(name="Specular Strength", default=0.)
    use_specular_power:    bpy.props.BoolProperty(name="Use Specular Power", default=False, update=setting_updated)
    specular_power:        bpy.props.FloatProperty(name="Specular Power", default=1.)

    # Reflections
    use_reflections:      bpy.props.BoolProperty       (name="Use Reflections",    default=False, update=setting_updated)
    reflection_strength:  bpy.props.FloatProperty      (name="ReflectionStrength", default=0.)
    use_fresnel_min:      bpy.props.BoolProperty       (name="Use Fresnel Min",    default=False, update=setting_updated)
    fresnel_min:          bpy.props.FloatProperty      (name="FresnelMin",         default=0.5)
    use_fresnel_exp:      bpy.props.BoolProperty       (name="Use Fresnel Exp",    default=False, update=setting_updated)
    fresnel_exp:          bpy.props.FloatProperty      (name="FresnelExp",         default=1.)

    # Subsurface
    use_velvet_strength:  bpy.props.BoolProperty       (name="Use Velvet",          default=False, update=setting_updated)
    use_rolloff:          bpy.props.BoolProperty       (name="Use Rolloff",         default=False, update=setting_updated)
    use_surface_color:    bpy.props.BoolProperty       (name="Use SurfaceCOlor",    default=False, update=setting_updated)
    use_subsurface_color: bpy.props.BoolProperty       (name="Use SubSurfaceColor", default=False, update=setting_updated)
    use_fuzzy_spec_color: bpy.props.BoolProperty       (name="Use FuzzySpecColor",  default=False, update=setting_updated)
    velvet_strength:      bpy.props.FloatProperty      (name="VelvetStrength", default=0.)
    rolloff:              bpy.props.FloatProperty      (name="Rolloff",        default=0.)
    surface_color:        bpy.props.FloatVectorProperty(subtype="COLOR", name="SurfaceColor",    default=(1., 1., 1.), size=3, min=0., max=1.) 
    subsurface_color:     bpy.props.FloatVectorProperty(subtype="COLOR", name="SubSurfaceColor", default=(1., 1., 1.), size=3, min=0., max=1.) 
    fuzzy_spec_color:     bpy.props.FloatVectorProperty(subtype="COLOR", name="FuzzySpecColor",  default=(1., 1., 1.), size=3, min=0., max=1.) 

    # Scene
    use_time:             bpy.props.BoolProperty       (name="Use Time",           default=False, update=setting_updated)
    time:                 bpy.props.FloatProperty      (name="Time",               default=0.)

    ###################
    # OPENGL SETTINGS #
    ###################
    use_gl_alpha: bpy.props.BoolProperty(name="Enable Alpha Testing", default=False, get=lambda self: self.get("use_gl_alpha", False), set=gl_alpha_setter, update=setting_updated)
    gl_alpha_func: bpy.props.EnumProperty(name="Alpha Func",
                                          items=[
                                              ("GL_NEVER",    "Never Pass",  "Equivalent to GL_NEVER"   ),
                                              ("GL_LESS",     "<",           "Equivalent to GL_LESS"    ),
                                              ("GL_LEQUAL",   "<=",          "Equivalent to GL_LEQUAL"  ),
                                              ("GL_EQUAL",    "=",           "Equivalent to GL_EQUAL"   ),
                                              ("GL_NOTEQUAL", "!=",          "Equivalent to GL_NOTEQUAL"),
                                              ("GL_GEQUAL",   ">=",          "Equivalent to GL_GEQUAL"  ),
                                              ("GL_GREATER",  ">",           "Equivalent to GL_GREATER" ),
                                              ("GL_ALWAYS",   "Always Pass", "Equivalent to GL_ALWAYS"  ),
                                              ("INVALID",     "INVALID",     "An invalid input")
                                          ],
                                          default="GL_GREATER",
                                          update=setting_updated)
    
    gl_alpha_invalid_value: bpy.props.IntProperty(name="Invalid Value", default=0)
    gl_alpha_threshold:     bpy.props.FloatProperty(name="Threshold", default=0.5, step=0.1)
    
    use_gl_blend: bpy.props.BoolProperty(name="Enable Blending",      default=False, get=lambda self: self.get("use_gl_blend", False), set=gl_blend_setter, update=setting_updated)

    # # Uniform 0x30
    # diffuse_alpha       = bpy.props.FloatProperty      (name="DiffuseAlpha",       default=1.)
    # specular_params     = bpy.props.FloatVectorProperty(name="SpecularParams",     default=(0., 0.), size=2)
    
    # # Uniform 0x40
    # uniform_0x49           = bpy.props.FloatProperty      (name="Uniform 0x49",         default=0.)
    # glass_params           = bpy.props.FloatVectorProperty(name="GlassParams",          default=(0., 0., 0.), size=3)
    # glass_strength         = bpy.props.FloatProperty      (name="GlassStrength",        default=0.)
    # curvature              = bpy.props.FloatProperty      (name="Curvature",            default=0.)
    # upside_down            = bpy.props.FloatProperty      (name="UpsideDown",           default=0.)
    # parallax_bias          = bpy.props.FloatVectorProperty(name="ParallaxBias",         default=(0., 0.), size=2)
    
    # # Uniform 0x50
    # uniform_0x51         = bpy.props.FloatProperty      (name="Uniform 0x51",     default=0.)
    # uniform_0x52         = bpy.props.FloatProperty      (name="Uniform 0x52",     default=0.)
    # uniform_0x53         = bpy.props.FloatProperty      (name="Uniform 0x53",     default=0.)
    # uniform_56           = bpy.props.FloatProperty      (name="Uniform 0x56",     default=0.)
    # uniform_57           = bpy.props.FloatProperty      (name="Uniform 0x57",     default=0.)
    # scroll_speed_set_2_u = bpy.props.FloatProperty      (name="ScrollSpeedSet2U", default=0.)
    # scroll_speed_set_2_v = bpy.props.FloatProperty      (name="ScrollSpeedSet2V", default=0.)
    # scroll_speed_set_3_u = bpy.props.FloatProperty      (name="ScrollSpeedSet3U", default=0.)
    # scroll_speed_set_3_v = bpy.props.FloatProperty      (name="ScrollSpeedSet3V", default=0.)
    # offset_set_1_u       = bpy.props.FloatProperty      (name="OffsetSet1U", default=0.)
    
    # # Uniform 0x60
    # offset_set_1_v      = bpy.props.FloatProperty      (name="OffsetSet1V", default=0.)
    # offset_set_2_u      = bpy.props.FloatProperty      (name="OffsetSet2U", default=0.)
    # offset_set_2_v      = bpy.props.FloatProperty      (name="OffsetSet2V", default=0.)
    # uniform_0x65        = bpy.props.FloatProperty      (name="Uniform 0x65", default=0.)
    # uniform_0x66        = bpy.props.FloatProperty      (name="Uniform 0x66", default=0.)
    # uniform_0x67        = bpy.props.FloatProperty      (name="Uniform 0x67", default=0.)
    # uniform_0x68        = bpy.props.FloatProperty      (name="Uniform 0x68", default=0.)
    # uniform_0x69        = bpy.props.FloatProperty      (name="Uniform 0x69", default=0.)
    # uniform_0x6A        = bpy.props.FloatProperty      (name="Uniform 0x6A", default=0.)
    # uniform_0x6B        = bpy.props.FloatProperty      (name="Uniform 0x6B", default=0.)
    # uniform_0x6C        = bpy.props.FloatProperty      (name="Uniform 0x6C", default=0.)
    # uniform_0x6D        = bpy.props.FloatProperty      (name="Uniform 0x6D", default=0.)
    # uniform_0x6E        = bpy.props.FloatProperty      (name="Uniform 0x6E", default=0.)
    # uniform_0x6F        = bpy.props.FloatProperty      (name="Uniform 0x6F", default=0.)
    
    # # Uniform 0x70
    # mip_bias           = bpy.props.FloatProperty      (name="MipBias",          default=0.)
    # saturation         = bpy.props.FloatProperty      (name="Saturation",       default=0.)
    # offset_set_3_u     = bpy.props.FloatProperty      (name="OffsetSet3U",      default=0.)
    # offset_set_3_v     = bpy.props.FloatProperty      (name="OffsetSet3V",      default=0.)
    # fat                = bpy.props.FloatProperty      (name="Fat",              default=0.)
    # uniform_0x79       = bpy.props.FloatProperty      (name="Uniform 0x79",     default=0.)
    # uniform_0x7A       = bpy.props.FloatProperty      (name="Uniform 0x7A",     default=0.)
    # uniform_0x7C       = bpy.props.FloatProperty      (name="Uniform 0x7C",     default=0.)
    # uniform_0x7D       = bpy.props.FloatProperty      (name="Uniform 0x7D",     default=0.)
    # uniform_0x7F       = bpy.props.FloatProperty      (name="Uniform 0x7F",     default=0.)
    
    # # Uniform 0x80
    # uniform_0x80       = bpy.props.FloatProperty      (name="Uniform 0x80",    default=0.)
    # scale_set_1_u      = bpy.props.FloatProperty      (name="ScaleSet1U",      default=0.)
    # scale_set_1_v      = bpy.props.FloatProperty      (name="ScaleSet1V",      default=0.)
    # scale_set_2_u      = bpy.props.FloatProperty      (name="ScaleSet1U",      default=0.)
    # scale_set_2_v      = bpy.props.FloatProperty      (name="ScaleSet1V",      default=0.)
    # scale_set_3_u      = bpy.props.FloatProperty      (name="ScaleSet3U",      default=0.)
    # scale_set_3_v      = bpy.props.FloatProperty      (name="ScaleSet3V",      default=0.)
    # uniform_0x8A       = bpy.props.FloatProperty      (name="Uniform 0x8A",    default=0.)
    # uniform_0x8B       = bpy.props.FloatProperty      (name="Uniform 0x8B",    default=0.)
    # uniform_0x8C       = bpy.props.FloatProperty      (name="Uniform 0x8C",    default=0.)
    # z_bias             = bpy.props.FloatProperty      (name="ZBias",           default=0.)
    # inner_grow_a_value = bpy.props.FloatVectorProperty(name="InnerGrowAValue", default=(0., 0., 0.), size=3)
    
    # # Uniform 0x90
    # uniform_0x90 = bpy.props.FloatProperty(name="Uniform 0x90", default=0.)
    # uniform_0x91 = bpy.props.FloatProperty(name="Uniform 0x91", default=0.)
    # uniform_0x92 = bpy.props.FloatProperty(name="Uniform 0x92", default=0.)
    # uniform_0x93 = bpy.props.FloatProperty(name="Uniform 0x93", default=0.)
    # uniform_0x94 = bpy.props.FloatProperty(name="Uniform 0x94", default=0.)
    # uniform_0x95 = bpy.props.FloatProperty(name="Uniform 0x95", default=0.)
    # uniform_0x96 = bpy.props.FloatProperty(name="Uniform 0x96", default=0.)
    # uniform_0x97 = bpy.props.FloatProperty(name="Uniform 0x97", default=0.)
    # uniform_0x98 = bpy.props.FloatProperty(name="Uniform 0x98", default=0.)
    # uniform_0x99 = bpy.props.FloatProperty(name="Uniform 0x99", default=0.)
    # uniform_0x9A = bpy.props.FloatProperty(name="Uniform 0x9A", default=0.)
    # uniform_0x9B = bpy.props.FloatProperty(name="Uniform 0x9B", default=0.)
    # uniform_0x9C = bpy.props.FloatProperty(name="Uniform 0x9C", default=0.)
    # uniform_0x9D = bpy.props.FloatProperty(name="Uniform 0x9D", default=0.)
    # uniform_0x9E = bpy.props.FloatProperty(name="Uniform 0x9E", default=0.)
    # uniform_0x9F = bpy.props.FloatProperty(name="Uniform 0x9F", default=0.)
    
    def set_split_shader_name(self, shader_list):
        self.shader_name = f"{shader_list[0]:0>8x}_{shader_list[1]:0>8x}_{shader_list[2]:0>8x}_{shader_list[3]:0>8x}"
    
    def get_split_shader_name(self):
        return [int(elem, 0x10) for elem in self.shader_name.split("_")]
    
    def get_textures(self):
        texture_names = []
        for sampler in [
                self.color_sampler,
                self.overlay_color_sampler,
                self.normal_sampler,
                self.overlay_normal_sampler,
                self.lightmap_sampler,
                self.env_sampler,
                self.envs_sampler,
                self.clut_sampler]:
            if sampler.active:
                img_name = sampler.image
                if img_name not in texture_names:
                    texture_names.append(sampler.image)
        for u in self.unhandled_uniforms:
            if u.dtype == "TEXTURE":
                if u.texture_data.image is not None:
                    img_name = u.texture_data.image.name
                    if img_name not in texture_names:
                        texture_names.append(img_name)
        return texture_names

    def get_texture_lookup(self):
        texture_lookup = {}
        for sampler in [
                self.color_sampler,
                self.overlay_color_sampler,
                self.normal_sampler,
                self.overlay_normal_sampler,
                self.lightmap_sampler,
                self.env_sampler,
                self.envs_sampler,
                self.clut_sampler]:
            if sampler.active:
                texture_lookup[sampler.typename] = sampler.image
        return texture_lookup
    
    def uv_1_active(self):
        return any((t.uv_1_used for t in self.get_textures()))
    
    def uv_2_active(self):
        return any((t.uv_2_used for t in self.get_textures()))
    
    def uv_3_active(self):
        return any((t.uv_3_used for t in self.get_textures()))
    
    ##########################
    # SHADER UNIFORM SETTERS #
    ##########################
    def set_bumpiness(self, uniform):
        self.use_bumpiness = True
        self.bumpiness = uniform.data[0]
        
    def set_overlay_bumpiness(self, uniform):
        self.use_overlay_bumpiness = True
        self.overlay_bumpiness = uniform.data[0]
        
    def set_parallax_x(self, uniform):
        self.use_parallax_bias_x = True
        self.parallax_bias_x = uniform.data[0]
        
    def set_parallax_y(self, uniform):
        self.use_parallax_bias_y = True
        self.parallax_bias_y = uniform.data[0]
    
    def set_distortion(self, uniform):
        self.use_distortion = True
        self.distortion_strength = uniform.data[0]
    
    def set_diffuse_color(self, uniform):
        self.use_diffuse_color = True
        self.diffuse_color = uniform.data
        
    def set_lightmap_strength(self, uniform):
        self.use_lightmap_strength = True
        self.lightmap_strength = uniform.data[0]
    
    def set_lightmap_power(self, uniform):
        self.use_lightmap_power = True
        self.lightmap_power = uniform.data[0]
    
    def set_spec_str(self, uniform):
        self.use_specular_strength = True
        self.specular_strength = uniform.data[0]
        
    def set_spec_pow(self, uniform):
        self.use_specular_power = True
        self.specular_power = uniform.data[0]
    
    def set_velvet_strength(self, uniform):
        self.use_velvet_strength = True
        self.velvet_strength = uniform.data[0]
    
    def set_rolloff(self, uniform):
        self.use_rolloff = True
        self.rolloff = uniform.data[0]
    
    def set_surface_color(self, uniform):
        self.use_surface_color = True
        self.surface_color = uniform.data
        
    def set_subsurface_color(self, uniform):
        self.use_subsurface_color = True
        self.subsurface_color = uniform.data
            
    def set_fuzzy_spec_color(self, uniform):
        self.use_fuzzy_spec_color = True
        self.fuzzy_spec_color = uniform.data
    
    def set_refl_str(self, uniform):
        self.use_reflections = True
        self.reflection_strength = uniform.data[0]
    
    def set_fres_min(self, uniform):
        self.use_fresnel_min = True
        self.fresnel_min = uniform.data[0]
        
    def set_fres_exp(self, uniform):
        self.use_fresnel_exp = True
        self.fresnel_exp = uniform.data[0]
    
    def set_overlay_str(self, uniform):
        self.use_overlay_strength = True
        self.overlay_strength = uniform.data[0]
        
    def set_time(self, uniform):
        self.use_time = True
        self.time = uniform.data[0]
    
    ##########################
    # OPENGL SETTING SETTERS #
    ##########################
    def set_gl_alpha_func(self, setting):
        gl_enum = int(setting.data[0])
        self.gl_alpha_threshold = setting.data[1]

        if   gl_enum == 0x200: self.gl_alpha_func = "GL_NEVER"
        elif gl_enum == 0x201: self.gl_alpha_func = "GL_LESS"
        elif gl_enum == 0x202: self.gl_alpha_func = "GL_EQUAL"
        elif gl_enum == 0x203: self.gl_alpha_func = "GL_LEQUAL"
        elif gl_enum == 0x204: self.gl_alpha_func = "GL_GREATER"
        elif gl_enum == 0x205: self.gl_alpha_func = "GL_NOTEQUAL"
        elif gl_enum == 0x206: self.gl_alpha_func = "GL_GEQUAL"
        elif gl_enum == 0x207: self.gl_alpha_func = "GL_ALWAYS"
        else:
            self.gl_alpha_func = "INVALID"
            self.gl_alpha_invalid_value = gl_enum
        
    def build_bpy_material(self):
        build_bpy_material(self)
