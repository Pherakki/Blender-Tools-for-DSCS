import os

import bpy

from .ShaderNodes.BuildTree import define_node_group
from .ShaderNodes.BuildTree import define_clut_uv_node_group
from .ShaderNodes.BuildTree import define_refl_uv_node_group


def import_materials(ni, gi, path, rename_imgs, use_custom_nodes):
    texture_bank = {}
    import_images(gi, texture_bank, path)
    define_node_group()
    define_clut_uv_node_group()
    define_refl_uv_node_group()
    
    materials = []
    for material_name, material in zip(ni.material_names, gi.materials):
        bpy_material = bpy.data.materials.new(name=material_name)
        materials.append(bpy_material)
        props = bpy_material.DSCS_MaterialProperties

        # Load up any custom properties we need
        props.shader_name = f"{material.shader_file[0]:0>8x}_{material.shader_file[1]:0>8x}_{material.shader_file[2]:0>8x}_{material.shader_file[3]:0>8x}"
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
        import_shader_uniforms(material, props, texture_bank)
        import_opengl_settings(material, props, bpy_material)
        
        # Set up nodes
        create_shader_nodes(path, bpy_material, material, gi, texture_bank)
        
    return materials


def import_images(gi, texture_bank, path):
    for idx, texture_name in enumerate(gi.textures):
        img_path = os.path.join(path, "images", texture_name + ".img")
        if os.path.isfile(img_path):
            texture_bank[idx] = bpy.data.images.load(img_path)


def import_shader_uniforms(material, props, texture_bank):
    for uniform in material.shader_uniforms:
        if uniform.index == 0x32:
            props.color_sampler.active = True
            props.color_sampler.image = texture_bank[uniform.data[0]]
            props.color_sampler.data = uniform.data[1:4]
            # Set UV by parsing shader name
        elif uniform.index == 0x33:
            props.use_diffuse_color = True
            props.diffuse_color = uniform.data
        elif uniform.index == 0x3A:
            props.env_sampler.active = True
            props.env_sampler.image = texture_bank[uniform.data[0]]
            props.env_sampler.data = uniform.data[1:4]
        elif uniform.index == 0x3B:
            props.use_reflections = True
            props.reflection_strength = uniform.data[0]
        elif uniform.index == 0x3C:
            props.use_fresnel_min = True
            props.fresnel_min = uniform.data[0]
        elif uniform.index == 0x3D:
            props.use_fresnel_exp = True
            props.fresnel_exp = uniform.data[0]
        elif uniform.index == 0x44:
            props.overlay_color_sampler.active = True
            props.overlay_color_sampler.image = texture_bank[uniform.data[0]]
            props.overlay_color_sampler.data = uniform.data[1:4]
            # Set UV by parsing shader name
        elif uniform.index == 0x47:
            props.use_overlay_strength = True
            props.overlay_strength = uniform.data
        elif uniform.index == 0x48:
            props.clut_sampler.active = True
            props.clut_sampler.image = texture_bank[uniform.data[0]]
            props.clut_sampler.data = uniform.data[1:4]
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
        if   setting.index == 0xA0: pass # glAlphaFunc
        elif setting.index == 0xA1: props.use_gl_alpha = bool(setting.data[0])
        elif setting.index == 0xA2: pass # glBlendFunc
        elif setting.index == 0xA3: pass # glBlendEquationSeparate
        elif setting.index == 0xA4: props.use_gl_blend = bool(setting.data[0])
        elif setting.index == 0xA5: pass # glCullFace
        elif setting.index == 0xA6: bpy_material.use_backface_culling = bool(setting.data[0])
        elif setting.index == 0xA7: pass # glDepthFunc
        elif setting.index == 0xA8: pass # glDepthMask
        elif setting.index == 0xA9: pass # GL_DEPTH_TEST
        elif setting.index == 0xAA: pass # glPolygonOffset
        elif setting.index == 0xAB: pass # GL_POLYGON_OFFSET_FILL
        elif setting.index == 0xAC: pass # glColorMask
        else:
            assert 0 # Add to unhandled settings    
        
        
def create_shader_nodes(path, bpy_material, material, gi, texture_bank):
        bpy_material.use_nodes = True
        nodes   = bpy_material.node_tree.nodes
        connect = bpy_material.node_tree.links.new
        props = bpy_material.DSCS_MaterialProperties

        ########################
        # DIFFUSE CONTRIBUTION #
        ########################
        main_group = nodes.new("ShaderNodeGroup")
        main_group.node_tree = bpy.data.node_groups['DSCS Shader']
        
        color_sampler = nodes.new('ShaderNodeTexImage')
        color_sampler.name  = "ColorSampler"
        color_sampler.label = "ColorSampler"
        color_sampler.image = props.color_sampler.image
        
        overlay_color_sampler = nodes.new('ShaderNodeTexImage')
        overlay_color_sampler.name  = "OverlayColorSampler"
        overlay_color_sampler.label = "OverlayColorSampler"
        overlay_color_sampler.image = props.overlay_color_sampler.image
        
        connect(color_sampler.outputs["Color"], main_group.inputs["ColorSampler"])
        connect(color_sampler.outputs["Alpha"], main_group.inputs["ColorSamplerAlpha"])
        connect(overlay_color_sampler.outputs["Color"], main_group.inputs["OverlayColorSampler"])
        connect(overlay_color_sampler.outputs["Alpha"], main_group.inputs["OverlayColorSamplerAlpha"])

        ########
        # CLUT #
        ########
        clut_uvs = nodes.new("ShaderNodeGroup")
        clut_uvs.node_tree = bpy.data.node_groups['DSCS CLUT UV']
        
        clut_sampler = nodes.new('ShaderNodeTexImage')
        clut_sampler.name  = "CLUTSampler"
        clut_sampler.label = "CLUTSampler"
        clut_sampler.image = props.clut_sampler.image
        clut_sampler.extension = "EXTEND"
        if clut_sampler.image is not None: # Move this to import...
            clut_sampler.image.alpha_mode = "CHANNEL_PACKED"

        connect(clut_uvs.outputs["UV"], clut_sampler.inputs["Vector"])
        connect(clut_sampler.outputs["Color"],                main_group.inputs["CLUTSampler"])
        connect(clut_sampler.outputs["Alpha"],                main_group.inputs["CLUTSamplerAlpha"])
        connect(clut_uvs    .outputs["Lambert Term"],         main_group.inputs["Lambert Term"])
        connect(clut_uvs    .outputs["Reflection Intensity"], main_group.inputs["Reflection Intensity"])

        ##############
        # REFLECTION #
        ##############
        refl_uvs = nodes.new("ShaderNodeGroup")
        refl_uvs.node_tree = bpy.data.node_groups['DSCS Reflection UV']
        
        refl_sampler = nodes.new('ShaderNodeTexImage')
        refl_sampler.name  = "EnvSampler"
        refl_sampler.label = "EnvSampler"
        refl_sampler.image = props.env_sampler.image
        
        connect(refl_uvs    .outputs["UV"],    refl_sampler.inputs["Vector"])
        connect(refl_sampler.outputs["Color"], main_group  .inputs["EnvSampler"])
        connect(refl_sampler.outputs["Alpha"], main_group  .inputs["EnvSamplerAlpha"])
        
        ##########
        # OUTPUT #
        ##########
        bsdf_node = nodes.get('Principled BSDF')
        nodes.remove(bsdf_node)
        
        mat_out = nodes.get('Material Output')
        connect(main_group.outputs["Shader"], mat_out.inputs["Surface"])

        main_group           .location = (-200, 300)
        color_sampler        .location = (-500, 300)
        overlay_color_sampler.location = (-500, 0)
        clut_sampler         .location = (-500, -300)
        clut_uvs             .location = (-700, -300)
        refl_sampler         .location = (-500, -600)
        refl_uvs             .location = (-700, -600)
        

# def load_shader_text(path, shader_name, suffix, shader_bank):
#     shader_name = shader_name + suffix
#     if shader_name not in shader_bank:
#         shader_path = os.path.join(path, "shaders", shader_name)
#         if os.path.isfile(shader_path):
#             shader_bank.add(shader_name)
#             with open(os.path.join(shader_path), 'r') as F:
#                 text = bpy.data.texts.new(shader_name)
#                 text.from_string(F.read())
