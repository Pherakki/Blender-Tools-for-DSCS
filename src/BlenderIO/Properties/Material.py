import bpy


class TextureSampler(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(name="", default=False)
    image:  bpy.props.PointerProperty(type=bpy.types.Image, name="")
    data:   bpy.props.IntVectorProperty(name="Unknown Data", default=(0, 0, 0), size=3)

    uv_map: bpy.props.EnumProperty(name="UV Map", items=[("UV1", "UV1", ""), ("UV2", "UV2", ""), ("UV3", "UV3", "")])


class UnhandledTextureSampler(bpy.types.PropertyGroup):
    image:  bpy.props.PointerProperty(type=bpy.types.Image, name="")
    data:   bpy.props.IntVectorProperty(name="Data", default=(0, 0, 0), size=3)


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
    
    @staticmethod
    def extract_data(prop):
        if   prop.dtype == "FLOAT32":
            data = prop.float32_data
        elif prop.dtype == "FLOAT32VEC2":
            data = prop.float32vec2_data
        elif prop.dtype == "FLOAT32VEC3":
            data = prop.float32vec3_data
        elif prop.dtype == "FLOAT32VEC4":
            data = prop.float32vec4_data
        elif prop.dtype == "TEXTURE":
            data = prop.texture_data
            
        return prop.index, prop.dname, data


def set_shader_name(self, value):
    chunks = value.split("_")
    chunk_lengths = [len(chk) for chk in chunks]
    if len(chunks) == 4 and all(c == 8 for c in chunk_lengths):
        self["shader_name"] = value
    #else:
    #    self.report("ERROR", "Invalid shader name. Shader names must be 4 sets of 8 hexadecimal numbers, with each set separated with an underscore, e.g. '08810000_00000111_00000000_00040000'")

def get_shader_bit(self, chunk_idx, bit):
    chunk = self.shader_name.split("_")[chunk_idx] # 32 bits per chunk
    return (int(chunk, 16) >> (31-bit)) & 1 # Count bits left-to-right in each chunk

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

class MaterialProperties(bpy.types.PropertyGroup):
    flag_0:      bpy.props.BoolProperty(name="Unknown Flag 0", default=False )
    cast_shadow: bpy.props.BoolProperty(name="Cast Shadow",    default=False )
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

    # Should be able to remove this later...
    shader_name: bpy.props.StringProperty(name="Shader Name", default="00000000_00000000_00000000_00000000", get=lambda self: self["shader_name"], set=set_shader_name)
    
    # Properties derived from shader name
    # UV map, active lights, etc...
    use_dir_light: bpy.props.BoolProperty(name="Use Directional Light", get=lambda self: get_shader_bit(self, 1, 12), description="Whether to receive directional lighting. This is determined from the shader name.") # FIX BIT
    use_amb_light: bpy.props.BoolProperty(name="Use Ambient Light",     get=lambda self: get_shader_bit(self, 0, 6), description="Whether to receive ambient lighting. This is determined from the shader name.") # FIX BIT

    # Vertex Attributes
    requires_normals:   bpy.props.BoolProperty(name="Requires Normals",   default=True)
    requires_tangents: bpy.props.BoolProperty(name="Requires Tangents",  default=False)
    requires_binormals: bpy.props.BoolProperty(name="Requires Binormals", default=False)
    
    # Unhandled material uniforms
    unhandled_uniforms:           bpy.props.CollectionProperty(name="Unhandled Uniforms", type=UnhandledMaterialUniform)
    active_unhandled_uniform_idx: bpy.props.IntProperty(options={'HIDDEN'})
    
    #####################
    # MATERIAL UNIFORMS #
    #####################
    
    # UVMap 1
    use_rotation_set_1:     bpy.props.BoolProperty(name="", default=False)
    use_offset_set_1:       bpy.props.BoolProperty(name="", default=False)
    use_scroll_speed_set_1: bpy.props.BoolProperty(name="", default=False)
    use_scale_set_1:        bpy.props.BoolProperty(name="", default=False)
    rotation_set_1:     bpy.props.FloatProperty      (name="RotationSet1",    default=0.)
    offset_set_1:       bpy.props.FloatVectorProperty(name="OffsetSet1",      default=(0., 0.), size=2)
    scroll_speed_set_1: bpy.props.FloatVectorProperty(name="ScrollSpeedSet1", default=(0., 0.), size=2)
    scale_set_1:        bpy.props.FloatVectorProperty(name="ScaleSet1",       default=(0., 0.), size=2)
    
    # UVMap 2
    use_rotation_set_2:     bpy.props.BoolProperty(name="", default=False)
    use_offset_set_2:       bpy.props.BoolProperty(name="", default=False)
    use_scroll_speed_set_2: bpy.props.BoolProperty(name="", default=False)
    use_scale_set_2:        bpy.props.BoolProperty(name="", default=False)
    rotation_set_2:     bpy.props.FloatProperty      (name="RotationSet2",    default=0.)
    offset_set_2:       bpy.props.FloatVectorProperty(name="OffsetSet2",      default=(0., 0.), size=2)
    scroll_speed_set_2: bpy.props.FloatVectorProperty(name="ScrollSpeedSet2", default=(0., 0.), size=2)
    scale_set_2:        bpy.props.FloatVectorProperty(name="ScaleSet2",       default=(0., 0.), size=2)
    
    # UVMap 3
    use_rotation_set_3:     bpy.props.BoolProperty(name="", default=False)
    use_offset_set_3:       bpy.props.BoolProperty(name="", default=False)
    use_scroll_speed_set_3: bpy.props.BoolProperty(name="", default=False)
    use_scale_set_3:        bpy.props.BoolProperty(name="", default=False)
    rotation_set_3:     bpy.props.FloatProperty      (name="RotationSet3",    default=0.)
    offset_set_3:       bpy.props.FloatVectorProperty(name="OffsetSet3",      default=(0., 0.), size=2)
    scroll_speed_set_3: bpy.props.FloatVectorProperty(name="ScrollSpeedSet3", default=(0., 0.), size=2)
    scale_set_3:        bpy.props.FloatVectorProperty(name="ScaleSet3",       default=(0., 0.), size=2)
    
    # Texture Samplers
    color_sampler:          bpy.props.PointerProperty(type=TextureSampler, name="ColorSampler")
    overlay_color_sampler:  bpy.props.PointerProperty(type=TextureSampler, name="OverlayColorSampler")
    normal_sampler:         bpy.props.PointerProperty(type=TextureSampler, name="NormalSampler")
    overlay_normal_sampler: bpy.props.PointerProperty(type=TextureSampler, name="OverlayNormalSampler")
    env_sampler:            bpy.props.PointerProperty(type=TextureSampler, name="EnvSampler")
    envs_sampler:           bpy.props.PointerProperty(type=TextureSampler, name="EnvsSampler")
    clut_sampler:           bpy.props.PointerProperty(type=TextureSampler, name="CLUTSampler")

    # Colours
    use_diffuse_color:    bpy.props.BoolProperty(name="Use Diffuse Color", default=False)
    diffuse_color:        bpy.props.FloatVectorProperty(subtype="COLOR", name="DiffuseColor", default=(1., 1., 1., 1.), size=4, min=0., max=1.) 
    use_vertex_colors:    bpy.props.BoolProperty(name="Use Vertex Colors", default=False)
    use_overlay_strength: bpy.props.BoolProperty(name="Use Overlay Strength", default=False)
    overlay_strength:     bpy.props.FloatProperty(name="OverlayStrength", default=0., min=0., max=1., subtype="FACTOR")

    # Reflections
    use_reflections:      bpy.props.BoolProperty       (name="Use Reflections",    default=False)
    reflection_strength:  bpy.props.FloatProperty      (name="ReflectionStrength", default=0.)
    use_fresnel_min:      bpy.props.BoolProperty       (name="Use Fresnel Min",    default=False)
    fresnel_min:          bpy.props.FloatProperty      (name="FresnelMin",         default=0.5)
    use_fresnel_exp:      bpy.props.BoolProperty       (name="Use Fresnel Exp",    default=False)
    fresnel_exp:          bpy.props.FloatProperty      (name="FresnelExp",         default=1.)


    ###################
    # OPENGL SETTINGS #
    ###################
    use_gl_alpha: bpy.props.BoolProperty(name="Enable Alpha Testing", default=False, get=lambda self: self.get("use_gl_alpha", False), set=gl_alpha_setter)
    use_gl_blend: bpy.props.BoolProperty(name="Enable Blending",      default=False, get=lambda self: self.get("use_gl_blend", False), set=gl_blend_setter)

