import bpy
import os
import shutil

from ...FileReaders.GeomReader.ShaderUniforms import shader_textures


def import_materials(model_data):
    for i, IF_material in enumerate(model_data.materials):
        new_material = bpy.data.materials.new(name=IF_material.name)
        # Unknown data
        new_material['shader_hex'] = IF_material.shader_hex
        new_material['enable_shadows'] = IF_material.enable_shadows

        for nm, value in IF_material.shader_uniforms.items():
            new_material[nm] = value
        for nm, value in IF_material.unknown_data['unknown_material_components'].items():
            new_material[str(nm)] = value

        new_material.use_nodes = True

        # Set some convenience variables
        shader_uniforms = IF_material.shader_uniforms
        nodes = new_material.node_tree.nodes
        connect = new_material.node_tree.links.new

        # Remove the default shader node
        bsdf_node = nodes.get('Principled BSDF')
        nodes.remove(bsdf_node)

        output_node = new_material.node_tree.nodes.get('Material Output')
        new_material.node_tree.links.clear()
        import_material_texture_nodes(nodes, model_data, IF_material.shader_uniforms)

        final_diffuse_node = None
        if 'DiffuseTextureID' in shader_uniforms:
            tex0_img_node = nodes["DiffuseTextureID"]
            tex0_node = nodes.new('ShaderNodeBsdfPrincipled')
            tex0_node.name = "DiffuseShader"
            tex0_node.label = "DiffuseShader"

            # Might be updated by following nodes
            final_diffuse_colour_node = tex0_img_node
            final_alpha_node = tex0_img_node
            if "ToonTextureID" in shader_uniforms:
                toon_texture_node = nodes["ToonTextureID"]
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
            if "DiffuseColour" in shader_uniforms:
                rgba_node = nodes.new('ShaderNodeRGB')
                rgba_node.name = "DiffuseColour"
                rgba_node.label = "DiffuseColour"
                rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColour"]

                mix_node = nodes.new('ShaderNodeMixRGB')
                mix_node.blend_type = 'MULTIPLY'
                connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
                connect(rgba_node.outputs['Color'], mix_node.inputs['Color2'])

                final_diffuse_colour_node = mix_node

            # Vertex Colours
            vertex_colour_input_node = nodes.new('ShaderNodeVertexColor')
            vertex_colour_input_node.name = "VertexColour"
            vertex_colour_input_node.label = "VertexColour"

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

        elif "DiffuseColour" in shader_uniforms:
            rgba_node = nodes.new('ShaderNodeRGB')
            rgba_node.name = "DiffuseColour"
            rgba_node.label = "DiffuseColour"
            rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColour"]

            diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
            diffuse_node.name = "DiffuseColourShader"
            diffuse_node.label = "DiffuseColourShader"

            connect(rgba_node.outputs['Color'], diffuse_node.inputs['Color'])
            final_diffuse_node = diffuse_node

        if final_diffuse_node is not None:
            connect(final_diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

        new_material.use_backface_culling = True
        for key, gl_option_data in IF_material.unknown_data["unknown_material_components"].items():
            if key == 160:  # glAlphaFunc
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
            elif key == 161:  # glEnable(GL_ALPHA_TEST)
                new_material.blend_method = 'CLIP'
            elif key == 166:  # glEnable(GL_CULL_FACE)
                is_active = gl_option_data[0]  # 1 calls glEnable, 0 calls glDisable
                # This option is always set to 0
                new_material.use_backface_culling = is_active


def import_material_texture_nodes(nodes, model_data, mat_shader_uniforms):
    imported_textures = {}
    for nm in shader_textures.keys():
        if nm in mat_shader_uniforms:
            tex_img_node = nodes.new('ShaderNodeTexImage')
            tex_img_node.name = nm
            tex_img_node.label = nm
            set_texture_node_image(tex_img_node, mat_shader_uniforms[nm][0],
                                   model_data.textures[mat_shader_uniforms[nm][0]], imported_textures)


def set_texture_node_image(node, texture_idx, IF_texture, import_memory):
    tex_filename = os.path.split(IF_texture.filepath)[-1]
    dds_loc = IF_texture.filepath
    if texture_idx not in import_memory:
        import_memory[texture_idx] = tex_filename
        bpy.data.images.load(dds_loc)
    node.image = bpy.data.images[tex_filename]
