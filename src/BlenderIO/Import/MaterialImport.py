import os

import bpy


def import_materials(ni, gi, path, rename_imgs, use_custom_nodes):
    texture_bank = {}
    import_images(gi, texture_bank, path)
    
    materials = []
    for material_name, material in zip(ni.material_names, gi.materials):
        bpy_material = bpy.data.materials.new(name=material_name)
        materials.append(bpy_material)
        props = bpy_material.DSCS_MaterialProperties

        # Load up any custom properties we need
        props.set_split_shader_name(material.shader_file)
        bpy_material.use_backface_culling = True
        
        def add_flag(is_true, name):
            setattr(props, name, is_true)

        add_flag(bool((material.flags >>  0) & 1), "flag_0")
        add_flag(bool((material.flags >>  1) & 1), "cast_shadow")
        add_flag(bool((material.flags >>  2) & 1), "flag_2")
        add_flag(bool((material.flags >>  3) & 1), "flag_3")
        add_flag(bool((material.flags >>  4) & 1), "flag_4")
        add_flag(bool((material.flags >>  5) & 1), "flag_5")
        add_flag(bool((material.flags >>  6) & 1), "flag_6")
        add_flag(bool((material.flags >>  7) & 1), "flag_7")
        add_flag(bool((material.flags >>  8) & 1), "flag_8")
        add_flag(bool((material.flags >>  9) & 1), "flag_9")
        add_flag(bool((material.flags >> 10) & 1), "flag_10")
        add_flag(bool((material.flags >> 11) & 1), "flag_11")
        add_flag(bool((material.flags >> 12) & 1), "flag_12")
        add_flag(bool((material.flags >> 13) & 1), "flag_13")
        add_flag(bool((material.flags >> 14) & 1), "flag_14")
        add_flag(bool((material.flags >> 15) & 1), "flag_15")


        # # Import shader text
        # load_shader_text(path, bpy_material['shader_hex'], "_vp.shad", shader_bank)
        # load_shader_text(path, bpy_material['shader_hex'], "_fp.shad", shader_bank)
        
        # Import extra material data
        used_images = {}
        props.bpy_dtype = "BASIC"
        import_shader_uniforms(material, props, texture_bank, used_images)
        import_opengl_settings(material, props, bpy_material)
        
        # Set up nodes
        create_shader_nodes(path, bpy_material, material, gi, texture_bank, used_images)
        props.bpy_dtype = "ADVANCED"
        props.build_bpy_material()
        
        bpy_material.update_tag()
        
    return materials


def import_images(gi, texture_bank, path):
    for idx, texture_name in enumerate(gi.textures):
        img_path = os.path.join(path, "images", texture_name + ".img")
        if os.path.isfile(img_path):
            texture_bank[idx] = bpy.data.images.load(img_path)
            texture_bank[idx].name = os.path.splitext(texture_bank[idx].name)[0]


def import_shader_uniforms(material, props, texture_bank, used_images):    
    def is_tex(uniform, idx):
        return uniform.index == idx and uniform.is_texture
    
    def is_vec(uniform, idx, size):
        return uniform.index == idx and len(uniform.data) == size and not uniform.is_texture
    
    def is_float(uniform, idx):
        return is_vec(uniform, idx, 1)

    def mk_tex(sampler, uniform):
        img = texture_bank[uniform.data[0]]
        used_images[sampler.typename] = img
        sampler.active = True
        sampler.image = img
        sampler.data = uniform.data[1:4]
    
    for uniform in material.shader_uniforms:
        # Normal Mapping
        if   is_tex  (uniform, 0x35):    mk_tex(props.normal_sampler, uniform)
        elif is_tex  (uniform, 0x45):    mk_tex(props.overlay_normal_sampler, uniform)
        elif is_float(uniform, 0x36):    props.set_bumpiness(uniform)
        elif is_float(uniform, 0x46):    props.set_overlay_bumpiness(uniform)
        elif is_float(uniform, 0x4F):    props.set_parallax_x(uniform)
        elif is_float(uniform, 0x50):    props.set_parallax_y(uniform)
        elif is_float(uniform, 0x64):    props.set_distortion(uniform)
        
        # Diffuse
        elif is_tex  (uniform, 0x32):    mk_tex(props.color_sampler, uniform)
        elif is_tex  (uniform, 0x44):    mk_tex(props.overlay_color_sampler, uniform)
        elif is_vec  (uniform, 0x33, 4): props.set_diffuse_color(uniform)
        elif is_float(uniform, 0x47):    props.set_overlay_str(uniform)
        elif is_tex  (uniform, 0x43):    mk_tex(props.lightmap_sampler, uniform)
        elif is_float(uniform, 0x71):    props.set_lightmap_power(uniform)
        elif is_float(uniform, 0x72):    props.set_lightmap_strength(uniform)
        
        # Lighting
        elif is_tex  (uniform, 0x48):    mk_tex(props.clut_sampler, uniform)
        elif is_float(uniform, 0x38):    props.set_spec_str(uniform)
        elif is_float(uniform, 0x39):    props.set_spec_pow(uniform)
        
        # Reflection
        elif is_tex  (uniform, 0x3A):    mk_tex(props.env_sampler, uniform)
        elif is_float(uniform, 0x3B):    props.set_refl_str(uniform)
        elif is_float(uniform, 0x3C):    props.set_fres_min(uniform)
        elif is_float(uniform, 0x3D):    props.set_fres_exp(uniform)
        
        # Subsurface
        elif is_vec  (uniform, 0x3E, 3): props.set_surface_color(uniform)
        elif is_vec  (uniform, 0x3F, 3): props.set_subsurface_color(uniform)
        elif is_vec  (uniform, 0x40, 3): props.set_fuzzy_spec_color(uniform)
        elif is_float(uniform, 0x41):    props.set_rolloff(uniform)
        elif is_float(uniform, 0x42):    props.set_velvet_strength(uniform)
        
        # UV transforms
        elif is_vec  (uniform, 0x55, 2): props.uv_1.set_scroll(uniform)
        elif is_vec  (uniform, 0x58, 2): props.uv_2.set_scroll(uniform)
        elif is_vec  (uniform, 0x5B, 2): props.uv_3.set_scroll(uniform)
        elif is_float(uniform, 0x78):    props.uv_1.set_rotation(uniform)
        elif is_float(uniform, 0x7B):    props.uv_2.set_rotation(uniform)
        elif is_float(uniform, 0x7E):    props.uv_3.set_rotation(uniform) 
        elif is_vec  (uniform, 0x5E, 2): props.uv_1.set_offset(uniform)
        elif is_vec  (uniform, 0x61, 2): props.uv_2.set_offset(uniform)
        elif is_vec  (uniform, 0x74, 2): props.uv_3.set_offset(uniform)
        elif is_vec  (uniform, 0x81, 2): props.uv_1.set_scale(uniform)
        elif is_vec  (uniform, 0x84, 2): props.uv_2.set_scale(uniform)
        elif is_vec  (uniform, 0x87, 2): props.uv_3.set_scale(uniform)
        
        # Scene Properties
        elif is_float(uniform, 0x54):    props.set_time(uniform)
        
        # Anything not explicitly handled
        else:
            bpy_uniform = props.unhandled_uniforms.add()
            bpy_uniform.index = uniform.index
            if uniform.is_texture:
                bpy_uniform.dtype = "TEXTURE"
                bpy_uniform.texture_data.image = texture_bank[uniform.data[0]]
                bpy_uniform.texture_data.data = uniform.data[1:4]
            else:
                if   len(uniform.data) == 1:
                    bpy_uniform.dtype = "FLOAT32"
                    bpy_uniform.float32_data = uniform.data[0]
                elif len(uniform.data) == 2:
                    bpy_uniform.dtype = "FLOAT32VEC2"
                    bpy_uniform.float32vec2_data = uniform.data
                elif len(uniform.data) == 3:
                    bpy_uniform.dtype = "FLOAT32VEC3"
                    bpy_uniform.float32vec3_data = uniform.data
                elif len(uniform.data) == 4:
                    bpy_uniform.dtype = "FLOAT32VEC4"
                    bpy_uniform.float32vec4_data = uniform.data
                else:
                    raise Exception("Invalid float count")


def import_opengl_settings(material, props, bpy_material):
    for setting in material.opengl_settings:
        if    setting.index == 0xA0: props.set_gl_alpha_func(setting)
        elif  setting.index == 0xA1: props.use_gl_alpha = bool(setting.data[0])
        #elif setting.index == 0xA2: pass # glBlendFunc
        #elif setting.index == 0xA3: pass # glBlendEquationSeparate
        elif setting.index == 0xA4: props.use_gl_blend = bool(setting.data[0])
        #elif setting.index == 0xA5: pass # glCullFace
        elif setting.index == 0xA6: bpy_material.use_backface_culling = bool(setting.data[0])
        #elif setting.index == 0xA7: pass # glDepthFunc
        #elif setting.index == 0xA8: pass # glDepthMask
        #elif setting.index == 0xA9: pass # GL_DEPTH_TEST
        #elif setting.index == 0xAA: pass # glPolygonOffset
        #elif setting.index == 0xAB: pass # GL_POLYGON_OFFSET_FILL
        #elif setting.index == 0xAC: pass # glColorMask
        else:
            bpy_setting = props.unhandled_settings.add()
            bpy_setting.index = setting.index
            bpy_setting.data  = setting.data
        
        
def create_shader_nodes(path, bpy_material, material, gi, texture_bank, used_images):
        bpy_material.use_nodes = True
        nodes   = bpy_material.node_tree.nodes
        connect = bpy_material.node_tree.links.new
        props = bpy_material.DSCS_MaterialProperties

        # ########################
        # # DIFFUSE CONTRIBUTION #
        # ########################
        # main_group = nodes.new("ShaderNodeGroup")
        # main_group.node_tree = bpy.data.node_groups['DSCS Shader']
        
        # color_sampler_uvs = nodes.new("ShaderNodeGroup")
        # color_sampler_uvs.name  = "ColorSampler UVs"
        # color_sampler_uvs.label = "ColorSampler UVs"
        # #color_sampler_uvs.node_tree = bpy.data.node_groups["DSCS ColorSampler UV"]
        
        # color_sampler = nodes.new('ShaderNodeTexImage')
        # color_sampler.name  = "ColorSampler"
        # color_sampler.label = "ColorSampler"
        # color_sampler.image = used_images.get(props.color_sampler.typename)
        
        # overlay_color_sampler_uvs = nodes.new("ShaderNodeGroup")
        # overlay_color_sampler_uvs.name  = "OverlayColorSampler UVs"
        # overlay_color_sampler_uvs.label = "OverlayColorSampler UVs"
        # #overlay_color_sampler_uvs.node_tree = bpy.data.node_groups["DSCS OverlayColorSampler UV"]
        
        # overlay_color_sampler = nodes.new('ShaderNodeTexImage')
        # overlay_color_sampler.name  = "OverlayColorSampler"
        # overlay_color_sampler.label = "OverlayColorSampler"
        # overlay_color_sampler.image = used_images.get(props.overlay_color_sampler.typename)
        
        # #connect(color_sampler_uvs.outputs["UV"], color_sampler.inputs["Vector"])
        # connect(color_sampler.outputs["Color"], main_group.inputs["ColorSampler"])
        # connect(color_sampler.outputs["Alpha"], main_group.inputs["ColorSamplerAlpha"])
        # #connect(overlay_color_sampler_uvs.outputs["UV"], overlay_color_sampler.inputs["Vector"])
        # connect(overlay_color_sampler.outputs["Color"], main_group.inputs["OverlayColorSampler"])
        # connect(overlay_color_sampler.outputs["Alpha"], main_group.inputs["OverlayColorSamplerAlpha"])

        # ########
        # # CLUT #
        # ########
        # clut_uvs = nodes.new("ShaderNodeGroup")
        # clut_uvs.node_tree = bpy.data.node_groups['DSCS CLUT UV']
        
        # clut_sampler = nodes.new('ShaderNodeTexImage')
        # clut_sampler.name  = "CLUTSampler"
        # clut_sampler.label = "CLUTSampler"
        # clut_sampler.image = used_images.get(props.clut_sampler.typename)
        # clut_sampler.extension = "EXTEND"
        # if clut_sampler.image is not None:
        #     clut_sampler.image.alpha_mode = "CHANNEL_PACKED"

        # connect(clut_uvs.outputs["UV"], clut_sampler.inputs["Vector"])
        # connect(clut_sampler.outputs["Color"],                main_group.inputs["CLUTSampler"])
        # connect(clut_sampler.outputs["Alpha"],                main_group.inputs["CLUTSamplerAlpha"])
        # connect(clut_uvs    .outputs["Lambert Term"],         main_group.inputs["Lambert Term"])
        # connect(clut_uvs    .outputs["Reflection Intensity"], main_group.inputs["Reflection Intensity"])

        
        # ##############
        # # REFLECTION #
        # ##############
        # refl_uvs = nodes.new("ShaderNodeGroup")
        # refl_uvs.node_tree = bpy.data.node_groups['DSCS Reflection UV']
        
        # refl_sampler = nodes.new('ShaderNodeTexImage')
        # refl_sampler.name  = "EnvSampler"
        # refl_sampler.label = "EnvSampler"
        # refl_sampler.image = used_images.get(props.env_sampler.typename)
        
        # connect(refl_uvs    .outputs["UV"],    refl_sampler.inputs["Vector"])
        # connect(refl_sampler.outputs["Color"], main_group  .inputs["EnvSampler"])
        # connect(refl_sampler.outputs["Alpha"], main_group  .inputs["EnvSamplerAlpha"])
        
        # ##########
        # # OUTPUT #
        # ##########
        # bsdf_node = nodes.get('Principled BSDF')
        # nodes.remove(bsdf_node)
        
        # mat_out = nodes.get('Material Output')
        # connect(main_group.outputs["Shader"], mat_out.inputs["Surface"])

        # main_group               .location = (-200, 300)
        # #color_sampler_uvs        .location = (-700, 100)
        # color_sampler            .location = (-500, 300)
        # #overlay_color_sampler_uvs.location = (-700, -200)
        # overlay_color_sampler    .location = (-500, 0)
        # clut_sampler             .location = (-500, -300)
        # clut_uvs                 .location = (-700, -300)
        # refl_sampler             .location = (-500, -600)
        # refl_uvs                 .location = (-700, -600)
        

# def load_shader_text(path, shader_name, suffix, shader_bank):
#     shader_name = shader_name + suffix
#     if shader_name not in shader_bank:
#         shader_path = os.path.join(path, "shaders", shader_name)
#         if os.path.isfile(shader_path):
#             shader_bank.add(shader_name)
#             with open(os.path.join(shader_path), 'r') as F:
#                 text = bpy.data.texts.new(shader_name)
#                 text.from_string(F.read())
