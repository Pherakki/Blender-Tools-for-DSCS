import bpy
import os
import shutil

from ...FileReaders.GeomReader.ShaderUniforms import shader_textures
from ...Utilities.OpenGLResources import id_to_glfunc, glBool_options, glEnable_options, glBlendFunc_options, glBlendEquationSeparate_options, glCullFace_options, glComparison_options

from ...Utilities.Paths import normalise_abs_path


def import_materials(model_data, rename_imgs, use_custom_nodes):
    for i, IF_material in enumerate(model_data.materials):
        new_material = bpy.data.materials.new(name=IF_material.name)
        # Unknown data
        new_material['shader_hex'] = IF_material.shader_hex
        new_material['enable_shadows'] = IF_material.enable_shadows

        for nm, value in IF_material.shader_uniforms.items():
            new_material[nm] = value

        new_material.use_nodes = True

        if use_custom_nodes:
            generate_material_nodes(model_data, new_material, IF_material, rename_imgs)
        else:
            # Set some convenience variables
            shader_uniforms = IF_material.shader_uniforms
            nodes = new_material.node_tree.nodes
            connect = new_material.node_tree.links.new

            # Remove the default shader node
            bsdf_node = nodes.get('Principled BSDF')
            imported_textures = {}

            diff_tex_name = 'ColorSampler'
            if diff_tex_name in shader_uniforms:
                diff_tex = shader_uniforms[diff_tex_name]
                tex_img_node = nodes.new('ShaderNodeTexImage')
                tex_img_node.name = diff_tex_name
                tex_img_node.label = diff_tex_name
                set_texture_node_image(tex_img_node, shader_uniforms[diff_tex_name][0],
                                       model_data.textures[shader_uniforms[diff_tex_name][0]], imported_textures, rename_imgs)

                tex0_img_node = nodes["ColorSampler"]
                connect(tex0_img_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                connect(tex0_img_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])

        #########################################
        # IMPLEMENT OR STORE THE OPENGL OPTIONS #
        #########################################
        new_material.use_backface_culling = True
        for key, gl_option_data in IF_material.unknown_data["unknown_material_components"].items():
            gl_func = id_to_glfunc[key]
            if gl_func == "glAlphaFunc":
                input_alpha_threshold = gl_option_data[1]
                gl_enum = gl_option_data[0]
                if gl_enum == 0x200:  # GL_NEVER
                    new_material.alpha_threshold = 1.
                elif gl_enum == 0x201:  # GL_LESS
                    new_material.alpha_threshold = 1 - input_alpha_threshold
                elif gl_enum == 0x202:  # GL_EQUAL
                    print("WARNING! GL_EQUAL IS UNSUPPORTED!")
                    new_material.alpha_threshold = 0.
                elif gl_enum == 0x203:  # GL_LEQUAL
                    new_material.alpha_threshold = 1 - input_alpha_threshold
                elif gl_enum == 0x204:  # GL_GREATER (always used by DSCS models)
                    new_material.alpha_threshold = input_alpha_threshold
                elif gl_enum == 0x205:  # GL_NOTEQUAL
                    print("WARNING! GL_NOTEQUAL IS UNSUPPORTED!")
                    new_material.alpha_threshold = 0.
                elif gl_enum == 0x206:  # GL_GEQUAL
                    new_material.alpha_threshold = input_alpha_threshold
                elif gl_enum == 0x207:  # GL_ALWAYS
                    new_material.alpha_threshold = 0.
                else:
                    assert 0, f"Unknown GL_ENUM \'{hex(gl_enum)}\' encounted in glAlphaTest."

            elif gl_func == "GL_ALPHA_TEST":
                new_material.blend_method = 'CLIP'

            elif gl_func == "glBlendFunc":
                src_blend_factor_enum = glBlendFunc_options[gl_option_data[0]]  # Always GL_SOURCE_ALPHA
                dst_blend_factor_enum = glBlendFunc_options[gl_option_data[1]]  # GL_ZERO or GL_ONE
                new_material["glBlendFunc"] = [src_blend_factor_enum, dst_blend_factor_enum]

            elif gl_func == "glBlendEquationSeparate":
                rgba_blend_factor_enum = glBlendEquationSeparate_options[gl_option_data[0]]  # GL_FUNC_REVERSE_SUBTRACT or GL_FUNC_ADD
                new_material["glBlendEquationSeparate"] = rgba_blend_factor_enum

            elif gl_func == "GL_BLEND":
                new_material["GL_BLEND"] = glEnable_options[gl_option_data[0]]

            elif gl_func == "glCullFace":
                new_material["glCullFace"] = glCullFace_options[gl_option_data[0]]

            elif gl_func == "GL_CULL_FACE":
                # This option is always set to 0
                new_material.use_backface_culling = gl_option_data[0]

            elif gl_func == "glDepthFunc":
                new_material["glDepthFunc"] = glComparison_options[gl_option_data[0]]

            elif gl_func == "glDepthMask":
                new_material["glDepthMask"] = glBool_options[gl_option_data[0]]

            elif gl_func == "GL_DEPTH_TEST":
                # This option is always set to 0
                new_material["GL_DEPTH_TEST"] = glEnable_options[gl_option_data[0]]

            elif gl_func == "glColorMask":
                new_material["glColorMask"] = [glBool_options[opt] for opt in gl_option_data[:4]]

            else:
                print("Unrecognised openGL option \'{key}\'.")


def import_material_texture_nodes(nodes, model_data, mat_shader_uniforms, rename_dds):
    imported_textures = {}
    for nm in shader_textures.keys():
        if nm in mat_shader_uniforms:
            tex_img_node = nodes.new('ShaderNodeTexImage')
            tex_img_node.name = nm
            tex_img_node.label = nm
            set_texture_node_image(tex_img_node, mat_shader_uniforms[nm][0],
                                   model_data.textures[mat_shader_uniforms[nm][0]], imported_textures, rename_dds)


def set_texture_node_image(node, texture_idx, IF_texture, import_memory, rename_dds):
    tex_filename = os.path.split(IF_texture.filepath)[-1]
    dds_loc = IF_texture.filepath
    if rename_dds:
        dds_folder = "renamed_dds_imgs"
        use_filename = os.path.splitext(tex_filename)[0] + '.dds'
        dds_loc = os.path.dirname(dds_loc)
        dds_loc = os.path.join(dds_loc, dds_folder)
        dds_loc = normalise_abs_path(dds_loc)
        if not os.path.exists(dds_loc):
            os.mkdir(dds_loc)
        dds_loc = os.path.join(dds_loc, use_filename)
        dds_loc = normalise_abs_path(dds_loc)
        shutil.copy2(IF_texture.filepath, dds_loc)
    else:
        use_filename = tex_filename
    if texture_idx not in import_memory:
        import_memory[texture_idx] = use_filename
        bpy.data.images.load(dds_loc)
    node.image = bpy.data.images[use_filename]


def generate_material_nodes(model_data, new_material, IF_material, rename_imgs):
    # Set some convenience variables
    shader_uniforms = IF_material.shader_uniforms
    nodes = new_material.node_tree.nodes
    connect = new_material.node_tree.links.new

    # Remove the default shader node
    bsdf_node = nodes.get('Principled BSDF')
    nodes.remove(bsdf_node)

    output_node = new_material.node_tree.nodes.get('Material Output')
    new_material.node_tree.links.clear()
    import_material_texture_nodes(nodes, model_data, IF_material.shader_uniforms, rename_imgs)

    final_diffuse_node = None
    if 'ColorSampler' in shader_uniforms:
        tex0_img_node = nodes["ColorSampler"]
        tex0_node = nodes.new('ShaderNodeBsdfPrincipled')
        tex0_node.name = "DiffuseShader"
        tex0_node.label = "DiffuseShader"

        # Might be updated by following nodes
        final_diffuse_colour_node = tex0_img_node
        final_alpha_node = tex0_img_node
        if "CLUTSampler" in shader_uniforms:
            toon_texture_node = nodes["CLUTSampler"]
            toon_node = nodes.new('ShaderNodeBsdfToon')
            toon_node.name = "ToonShader"
            toon_node.label = "ToonShader"
            connect(toon_texture_node.outputs['Color'], toon_node.inputs['Color'])

            converter_node = nodes.new('ShaderNodeShaderToRGB')
            connect(toon_node.outputs['BSDF'], converter_node.inputs['Shader'])

            mix_node = new_material.node_tree.nodes.new('ShaderNodeMixRGB')
            mix_node.blend_type = 'MULTIPLY'

            connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
            connect(converter_node.outputs['Color'], mix_node.inputs['Color2'])

            final_diffuse_colour_node = mix_node
        if "DiffuseColor" in shader_uniforms:
            rgba_node = nodes.new('ShaderNodeRGB')
            rgba_node.name = "DiffuseColor"
            rgba_node.label = "DiffuseColor"
            rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColor"]

            mix_node = nodes.new('ShaderNodeMixRGB')
            mix_node.blend_type = 'MULTIPLY'
            connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
            connect(rgba_node.outputs['Color'], mix_node.inputs['Color2'])

            final_diffuse_colour_node = mix_node

        # Vertex Colours
        vertex_colour_input_node = nodes.new('ShaderNodeVertexColor')
        vertex_colour_input_node.name = "VertexColor"
        vertex_colour_input_node.label = "VertexColor"

        mix_node = nodes.new('ShaderNodeMixRGB')
        mix_node.blend_type = 'MULTIPLY'
        connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
        connect(vertex_colour_input_node.outputs['Color'], mix_node.inputs['Color2'])
        final_diffuse_colour_node = mix_node

        alpha_mix_node = nodes.new('ShaderNodeMath')
        alpha_mix_node.operation = "MULTIPLY"
        connect(final_alpha_node.outputs['Alpha'], alpha_mix_node.inputs[0])
        connect(vertex_colour_input_node.outputs['Alpha'], alpha_mix_node.inputs[1])
        final_alpha_node = alpha_mix_node
        connect(final_alpha_node.outputs['Value'], tex0_node.inputs['Alpha'])

        if "SpecularStrength" in shader_uniforms:
            specular_value = nodes.new('ShaderNodeValue')
            specular_value.name = 'SpecularStrength'
            specular_value.label = 'SpecularStrength'
            specular_value.outputs['Value'].default_value = shader_uniforms["SpecularStrength"][0]
            connect(specular_value.outputs['Value'], tex0_node.inputs['Specular'])
        connect(final_diffuse_colour_node.outputs['Color'], tex0_node.inputs['Base Color'])
        final_diffuse_node = tex0_node

    elif "DiffuseColor" in shader_uniforms:
        rgba_node = nodes.new('ShaderNodeRGB')
        rgba_node.name = "DiffuseColor"
        rgba_node.label = "DiffuseColor"
        rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColor"]

        diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse_node.name = "DiffuseColorShader"
        diffuse_node.label = "DiffuseColorShader"

        connect(rgba_node.outputs['Color'], diffuse_node.inputs['Color'])
        final_diffuse_node = diffuse_node

    if final_diffuse_node is not None:
        connect(final_diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])
