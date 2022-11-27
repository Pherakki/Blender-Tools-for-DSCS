import os

import bpy


def import_materials(ni, gi, path, rename_imgs, use_custom_nodes):
    texture_bank = {}
    shader_bank = set()
    materials = []
    for material_name, material in zip(ni.material_names, gi.materials):
        bpy_material = bpy.data.materials.new(name=material_name)
        materials.append(bpy_material)

        # Load up any custom properties we need
        bpy_material['shader_hex'] = f"{material.shader_file[0]:0>8x}_{material.shader_file[1]:0>8x}_{material.shader_file[2]:0>8x}_{material.shader_file[3]:0>8x}"

        def add_flag(is_true, name):
            if is_true:
                bpy_material[name] = is_true

        add_flag(bool((material.flags >> 0) & 1), "flag_0")
        add_flag(bool((material.flags >> 1) & 1), "enable_shadows")
        add_flag(bool((material.flags >> 2) & 1), "flag_2")
        add_flag(bool((material.flags >> 3) & 1), "flag_3")
        add_flag(bool((material.flags >> 4) & 1), "flag_4")
        add_flag(bool((material.flags >> 5) & 1), "flag_5")
        add_flag(bool((material.flags >> 6) & 1), "flag_6")
        add_flag(bool((material.flags >> 7) & 1), "flag_7")
        add_flag(bool((material.flags >> 8) & 1), "flag_8")
        add_flag(bool((material.flags >> 9) & 1), "flag_9")
        add_flag(bool((material.flags >> 10) & 1), "flag_10")
        add_flag(bool((material.flags >> 11) & 1), "flag_11")
        add_flag(bool((material.flags >> 12) & 1), "flag_12")
        add_flag(bool((material.flags >> 13) & 1), "flag_13")
        add_flag(bool((material.flags >> 14) & 1), "flag_14")
        add_flag(bool((material.flags >> 15) & 1), "flag_15")

        # Set up nodes
        create_shader_nodes(path, bpy_material, material, gi, texture_bank)

        # # Import shader text
        # load_shader_text(path, bpy_material['shader_hex'], "_vp.shad", shader_bank)
        # load_shader_text(path, bpy_material['shader_hex'], "_fp.shad", shader_bank)
    return materials


def create_shader_nodes(path, bpy_material, material, gi, texture_bank):
        bpy_material.use_nodes = True
        nodes   = bpy_material.node_tree.nodes
        connect = bpy_material.node_tree.links.new

        # Import textures
        for shader_uniform in material.shader_uniforms:
            if shader_uniform.index == 0x32:
                texture_idx = shader_uniform.data[0]
                if texture_idx not in texture_bank:
                    texture_name = gi.textures[shader_uniform.data[0]]

                    img_path = os.path.join(path, "images", texture_name + ".img")
                    if os.path.isfile(img_path):
                        texture_bank[texture_idx] = bpy.data.images.load(img_path)

                bsdf_node = nodes.get('Principled BSDF')
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.name = "ColorSampler"
                tex_node.label = "ColorSampler"
                tex_node.image = texture_bank.get(texture_idx, None)

                connect(tex_node.outputs["Color"], bsdf_node.inputs["Base Color"])

                # We'll put back the other shader stuff later
                break


# def load_shader_text(path, shader_name, suffix, shader_bank):
#     shader_name = shader_name + suffix
#     if shader_name not in shader_bank:
#         shader_path = os.path.join(path, "shaders", shader_name)
#         if os.path.isfile(shader_path):
#             shader_bank.add(shader_name)
#             with open(os.path.join(shader_path), 'r') as F:
#                 text = bpy.data.texts.new(shader_name)
#                 text.from_string(F.read())
