import bpy

from ...Core.FileFormats.Geom.GeomInterface import Material


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

def make_texture_sampler(sampler_name):
    class TextureSampler(bpy.types.PropertyGroup):
        typename = sampler_name
        
        active: bpy.props.BoolProperty(name="", default=False, get=lambda self: get_sampler_active(self, sampler_name))
        image:  bpy.props.StringProperty(name="", get=lambda self: get_sampler_image(self, sampler_name), set=lambda self, value: set_sampler_image(self, value, sampler_name))
        data:   bpy.props.IntVectorProperty(name="Unknown Data", default=(0, 0, 0), size=3)
    
        uv_map: bpy.props.EnumProperty(name="UV Map", items=[("UV1", "UV1", ""), ("UV2", "UV2", ""), ("UV3", "UV3", "")])
    
        uv_1_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV1")
        uv_2_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV2")
        uv_3_used: bpy.props.BoolProperty(name="", get=lambda self: self.uv_map=="UV3")
        
        def extract_data(self, texture_map):
            return [texture_map[self.image], *self.data]
        
    return TextureSampler


class UVTransforms(bpy.types.PropertyGroup):
    use_scroll_speed: bpy.props.BoolProperty(name="", default=False)
    use_rotation:     bpy.props.BoolProperty(name="", default=False)
    use_offset:       bpy.props.BoolProperty(name="", default=False)
    use_scale:        bpy.props.BoolProperty(name="", default=False)
    
    scroll_speed: bpy.props.FloatVectorProperty(name="Scroll Speed", default=(0., 0.), size=2)
    rotation:     bpy.props.FloatProperty      (name="Rotation",     default=0.              )
    offset:       bpy.props.FloatVectorProperty(name="Offset",       default=(0., 0.), size=2)
    scale:        bpy.props.FloatVectorProperty(name="Scale",        default=(0., 0.), size=2)


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
    return (int(chunk, 16) >> (bit + (3-byte_idx)*4)) & 1# Count each byte left-to-right, and each bit in the bytes right-to-left

def set_blend_method(self):
    mat = self.id_data
    if self.use_gl_alpha or self.use_gl_blend:
        mat.blend_method = "BLEND"
    else:
        mat.blend_method = "OPAQUE"

def gl_alpha_setter(self, value):
    self["use_gl_alpha"] = value
    set_blend_method(self)

def gl_blend_setter(self, value):
    self["use_gl_blend"] = value 
    set_blend_method(self)

def build_bpy_material(self):
    bpy_mat = self.id_data
    # Build tree...

def setting_updated(self, context):
    if self.bpy_dtype == "ADVANCED":
        self.build_bpy_material()

color_sampler_t          = make_texture_sampler("ColorSampler")
overlay_color_sampler_t  = make_texture_sampler("OverlayColorSampler")
normal_sampler_t         = make_texture_sampler("NormalSampler")
overlay_normal_sampler_t = make_texture_sampler("OverlayNormalSampler")
env_sampler_t            = make_texture_sampler("EnvSampler")
envs_sampler_t           = make_texture_sampler("EnvsSampler")
clut_sampler_t           = make_texture_sampler("CLUTSampler")


class MaterialProperties(bpy.types.PropertyGroup):
    bpy_dtype = bpy.props.EnumProperty(items=[("BASIC", "Basic", "A basic, minimalist shader that does not try to reproduce in-engine rendering"),
                                              ("ADVANCED", "Advanced", "Guesses the shader tree that should be built based on the currently active properties. Automatically rebuilds the tree if settings and changed. Be mindful that switching material properties on and off may make the material inconsistent with the shader name, which will determine the in-engine shader properties")])
    
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
    shader_name: bpy.props.StringProperty(name="Shader Name", default="00000000_00000000_00000000_00000000", get=lambda self: self["shader_name"], set=set_shader_name)
    
    # Properties derived from shader name
    # UV map, active lights, etc...
    use_dir_light:  bpy.props.BoolProperty(name="Use Directional Light",  get=lambda self: get_shader_bit(self, 0, 3, 0), description="Whether to receive directional lighting. This is determined from the shader name.")
    use_hem_light:  bpy.props.BoolProperty(name="Use Hemi-Ambient Light", get=lambda self: get_shader_bit(self, 0, 3, 5), description="Whether to receive hemispherical ambient lighting. This is determined from the shader name.")
    use_amb_light:  bpy.props.BoolProperty(name="Use Ambient Light",      get=lambda self: get_shader_bit(self, 0, 3, 6), description="Whether to receive ambient lighting. This is determined from the shader name.")
    
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
    uv_1: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 1")
    uv_2: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 2")
    uv_3: bpy.props.PointerProperty(type=UVTransforms, name="UV Map 3")
    
    # Texture Samplers
    color_sampler:          bpy.props.PointerProperty(type=color_sampler_t,          name=color_sampler_t         .typename)
    overlay_color_sampler:  bpy.props.PointerProperty(type=overlay_color_sampler_t,  name=overlay_color_sampler_t .typename)
    normal_sampler:         bpy.props.PointerProperty(type=normal_sampler_t,         name=normal_sampler_t        .typename)
    overlay_normal_sampler: bpy.props.PointerProperty(type=overlay_normal_sampler_t, name=overlay_normal_sampler_t.typename)
    env_sampler:            bpy.props.PointerProperty(type=env_sampler_t,            name=env_sampler_t           .typename)
    envs_sampler:           bpy.props.PointerProperty(type=envs_sampler_t,           name=envs_sampler_t          .typename)
    clut_sampler:           bpy.props.PointerProperty(type=clut_sampler_t,           name=clut_sampler_t          .typename)

    # Colours
    use_diffuse_color:    bpy.props.BoolProperty(name="Use Diffuse Color", default=True, update=setting_updated)
    diffuse_color:        bpy.props.FloatVectorProperty(subtype="COLOR", name="DiffuseColor", default=(1., 1., 1., 1.), size=4, min=0., max=1.) 
    use_vertex_colors:    bpy.props.BoolProperty(name="Use Vertex Colors", default=False, update=setting_updated)
    use_overlay_strength: bpy.props.BoolProperty(name="Use Overlay Strength", default=False, update=setting_updated)
    overlay_strength:     bpy.props.FloatProperty(name="OverlayStrength", default=0., min=0., max=1., subtype="FACTOR")

    # Reflections
    use_reflections:      bpy.props.BoolProperty       (name="Use Reflections",    default=False, update=setting_updated)
    reflection_strength:  bpy.props.FloatProperty      (name="ReflectionStrength", default=0.)
    use_fresnel_min:      bpy.props.BoolProperty       (name="Use Fresnel Min",    default=False, update=setting_updated)
    fresnel_min:          bpy.props.FloatProperty      (name="FresnelMin",         default=0.5)
    use_fresnel_exp:      bpy.props.BoolProperty       (name="Use Fresnel Exp",    default=False, update=setting_updated)
    fresnel_exp:          bpy.props.FloatProperty      (name="FresnelExp",         default=1.)


    ###################
    # OPENGL SETTINGS #
    ###################
    use_gl_alpha: bpy.props.BoolProperty(name="Enable Alpha Testing", default=False, get=lambda self: self.get("use_gl_alpha", False), set=gl_alpha_setter)
    use_gl_blend: bpy.props.BoolProperty(name="Enable Blending",      default=False, get=lambda self: self.get("use_gl_blend", False), set=gl_blend_setter)

    
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
    
    def set_diffuse_color(self, uniform):
        self.use_diffuse_color = True
        self.diffuse_color = uniform.data
    
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
    
    def build_bpy_material(self):
        build_bpy_material(self)
