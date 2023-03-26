import os

import bpy


def define_node_group():
    
    # "Bool",
    #         "Collection",
    #         "Color",
    #         "Float",
    #         "FloatAngle",
    #         "FloatDistance",
    #         "FloatFactor",
    #         "FloatPercentage",
    #         "FloatTime",
    #         "FloatTimeAbsolute",
    #         "FloatUnsigned",
    #         "Geometry",
    #         "Image",
    #         "Int",
    #         "IntFactor",
    #         "IntPercentage",
    #         "IntUnsigned",
    #         "Material",
    #         "Object",
    #         "Shader",
    #         "String",
    #         "Texture",
    #         "Vector",
    #         "VectorAcceleration",
    #         "VectorDirection",
    #         "VectorEuler",
    #         "VectorTranslation",
    #         "VectorVelocity",
    #         "VectorXYZ"#, "Virtual"
    
    # create a group
    dscs_node = bpy.data.node_groups.new('DSCS Shader', 'ShaderNodeTree')
    
    # create group inputs
    inputs = dscs_node.nodes.new('NodeGroupInput')
    inputs.location = (-350,0)
    dscs_node.inputs.new('NodeSocketTexture','Diffuse')
    dscs_node.inputs.new('NodeSocketVector','Diffuse UV')
    dscs_node.inputs.new('NodeSocketTexture','Normal')
    dscs_node.inputs.new('NodeSocketVector','Normal UV')
    dscs_node.inputs.new('NodeSocketTexture','Light')
    dscs_node.inputs.new('NodeSocketVector','Light UV')
    dscs_node.inputs.new('NodeSocketTexture','Diffuse Overlay')
    dscs_node.inputs.new('NodeSocketVector','Diffuse Overlay UV')
    dscs_node.inputs.new('NodeSocketTexture','Normal Overlay')
    dscs_node.inputs.new('NodeSocketVector','Normal Overlay UV')
    dscs_node.inputs.new('NodeSocketFloatPercentage','Tex Layer Ratio')
    
    # create group outputs
    outputs = dscs_node.nodes.new('NodeGroupOutput')
    outputs.location = (300,0)
    dscs_node.outputs.new('NodeSocketFloat','out_result')
    
    # create three math nodes in a group
    node_add = dscs_node.nodes.new('ShaderNodeMath')
    node_add.operation = 'ADD'
    node_add.location = (100,0)
    
    node_greater = dscs_node.nodes.new('ShaderNodeMath')
    node_greater.operation = 'GREATER_THAN'
    node_greater.label = 'greater'
    node_greater.location = (-100,100)
    
    node_less = dscs_node.nodes.new('ShaderNodeMath')
    node_less.operation = 'LESS_THAN'
    node_less.label = 'less'
    node_less.location = (-100,-100)
    
    # link nodes together
    dscs_node.links.new(node_add.inputs[0], node_greater.outputs[0])
    dscs_node.links.new(node_add.inputs[1], node_less.outputs[0])
    
    # # link inputs
    # dscs_node.links.new(inputs.outputs['in_to_greater'], node_greater.inputs[0])
    # dscs_node.links.new(inputs.outputs['in_to_less'], node_less.inputs[0])
    
    # #link output
    # dscs_node.links.new(node_add.outputs[0], outputs.inputs['out_result'])


def import_materials(ni, gi, path, rename_imgs, use_custom_nodes):
    texture_bank = {}
    shader_bank = set()
    materials = []
    for material_name, material in zip(ni.material_names, gi.materials):
        bpy_material = bpy.data.materials.new(name=material_name)
        materials.append(bpy_material)

        # Load up any custom properties we need
        bpy_material.DSCS_MaterialProperties.shader_name = f"{material.shader_file[0]:0>8x}_{material.shader_file[1]:0>8x}_{material.shader_file[2]:0>8x}_{material.shader_file[3]:0>8x}"
        bpy_material.use_backface_culling = True
        
        def add_flag(is_true, name):
            setattr(bpy_material.DSCS_MaterialProperties, name, is_true)

        add_flag(bool((material.flags >> 0) & 1), "flag_0")
        add_flag(bool((material.flags >> 1) & 1), "cast_shadow")
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
                # groupnode = nodes.new('ShaderNodeGroup')
                # groupnode.node_tree = bpy.data.node_groups['DSCS Shader']
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
