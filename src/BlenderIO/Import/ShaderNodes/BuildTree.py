import bpy
from mathutils import Vector


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
    


def define_node_group():
    dscs_shader = bpy.data.node_groups.new("DSCS Shader", "ShaderNodeTree")
    
    nodes = dscs_shader.nodes
    links = dscs_shader.links
    connect = links.new
    
    # create group inputs
    group_inputs = dscs_shader.nodes.new('NodeGroupInput')
    inputs = dscs_shader.inputs
    inputs.new('NodeSocketColor','ColorSampler')
    inputs.new('NodeSocketFloat','ColorSamplerAlpha')
    inputs.new('NodeSocketColor','OverlayColorSampler')
    inputs.new('NodeSocketFloat','OverlayColorSamplerAlpha')
    inputs.new('NodeSocketColor','CLUTSampler')
    inputs.new('NodeSocketFloat','CLUTSamplerAlpha')
    inputs.new('NodeSocketFloat','Lambert Term')
    inputs.new('NodeSocketFloat','Reflection Intensity')
    inputs.new('NodeSocketColor','EnvSampler')
    inputs.new('NodeSocketFloat','EnvSamplerAlpha')
    group_inputs.location = (-500,0)
    
    
    ########################
    # DIFFUSE CONTRIBUTION #
    ########################
    diffuse_anchor = Vector((-300, 0))

    # Overlay strength
    overlay_factor_anchor = diffuse_anchor + Vector((0, -250))
    overlay_strength = nodes.new('ShaderNodeAttribute')
    overlay_strength.attribute_type = "OBJECT"
    overlay_strength.attribute_name = "active_material.DSCS_MaterialProperties.overlay_strength"
    overlay_strength.name  = "OverlayStrength"
    overlay_strength.label = "OverlayStrength"
    overlay_strength.location = overlay_factor_anchor + Vector((-200, -150))
    
    use_overlay_strength = nodes.new('ShaderNodeAttribute')
    use_overlay_strength.attribute_type = "OBJECT"
    use_overlay_strength.attribute_name = "active_material.DSCS_MaterialProperties.use_overlay_strength"
    use_overlay_strength.name  = "UseOverlayStrength"
    use_overlay_strength.label = "UseOverlayStrength"
    use_overlay_strength.location = overlay_factor_anchor + Vector((-200, -350))
    
    total_overlay_strength = nodes.new('ShaderNodeMath')
    total_overlay_strength.operation = "MULTIPLY"
    total_overlay_strength.name  = "Total Overlay Strength"
    total_overlay_strength.label = "Total Overlay Strength"
    total_overlay_strength.location = overlay_factor_anchor + Vector((0, -150))
    
    overlay_factor = nodes.new('ShaderNodeMath')
    overlay_factor.operation = "MULTIPLY"
    overlay_factor.name  = "Overlay Factor"
    overlay_factor.label = "Overlay Factor"
    overlay_factor.location = overlay_factor_anchor + Vector((200, 0))
    
    connect(overlay_strength      .outputs["Fac"],                      total_overlay_strength.inputs[0])
    connect(use_overlay_strength  .outputs["Fac"],                      total_overlay_strength.inputs[1])
    connect(group_inputs          .outputs["OverlayColorSamplerAlpha"], overlay_factor        .inputs[0])
    connect(total_overlay_strength.outputs["Value"],                    overlay_factor        .inputs[1])
    
    # Diffuse Texture Contribution
    total_diffuse_texture = nodes.new('ShaderNodeMix')
    total_diffuse_texture.data_type = "RGBA"
    total_diffuse_texture.blend_type = "MIX"
    total_diffuse_texture.clamp_result = False
    total_diffuse_texture.clamp_factor = True
    total_diffuse_texture.location = diffuse_anchor + Vector((400, 0))
    
    connect(group_inputs  .outputs["ColorSampler"],        total_diffuse_texture.inputs[6]) # A_Color
    connect(group_inputs  .outputs["OverlayColorSampler"], total_diffuse_texture.inputs[7]) # B_Color
    connect(overlay_factor.outputs["Value"],               total_diffuse_texture.inputs["Factor"])
    
    # Vertex Colours
    vertex_color_anchor = diffuse_anchor + Vector((400, -250))
    
    use_vertex_colors = nodes.new('ShaderNodeAttribute')
    use_vertex_colors.attribute_type = "OBJECT"
    use_vertex_colors.attribute_name = "active_material.DSCS_MaterialProperties.use_vertex_colors"
    use_vertex_colors.name  = "Use Vertex Colors"
    use_vertex_colors.label = "Use Vertex Colors"
    use_vertex_colors.location = vertex_color_anchor + Vector((0, 0))
    
    vertex_color = nodes.new('ShaderNodeVertexColor')
    vertex_color.location = vertex_color_anchor + Vector((0, -200))
    
    total_vertex_color = nodes.new('ShaderNodeMix')
    total_vertex_color.data_type = "RGBA"
    total_vertex_color.blend_type = "MULTIPLY"
    total_vertex_color.clamp_result = False
    total_vertex_color.clamp_factor = True
    total_vertex_color.location = vertex_color_anchor + Vector((200, 0))
    
    vertex_color_mix = nodes.new('ShaderNodeMix')
    vertex_color_mix.data_type = "RGBA"
    vertex_color_mix.blend_type = "MULTIPLY"
    vertex_color_mix.clamp_result = False
    vertex_color_mix.clamp_factor = True
    vertex_color_mix.location = vertex_color_anchor + Vector((400, 250))
    
    total_vertex_color.inputs[6].default_value = [1., 1., 1., 1.] # A_Color
    connect(vertex_color     .outputs["Color"], total_vertex_color.inputs[7]) # B_Color
    connect(use_vertex_colors.outputs["Fac"],   total_vertex_color.inputs["Factor"])
    
    connect(total_diffuse_texture.outputs[2], vertex_color_mix.inputs[6]) # Result, A_Color
    connect(total_vertex_color   .outputs[2], vertex_color_mix.inputs[7]) # Result, B_Color
    vertex_color_mix.inputs["Factor"].default_value = 1.
    
    
    # Diffuse Color
    diffuse_color_anchor = vertex_color_anchor + Vector((400, 0))
    
    use_diffuse_color = nodes.new('ShaderNodeAttribute')
    use_diffuse_color.attribute_type = "OBJECT"
    use_diffuse_color.attribute_name = "active_material.DSCS_MaterialProperties.use_diffuse_color"
    use_diffuse_color.name  = "Use Diffuse Color"
    use_diffuse_color.label = "Use Diffuse Color"
    use_diffuse_color.location = diffuse_color_anchor + Vector((0, 0))
    
    diffuse_color = nodes.new('ShaderNodeAttribute')
    diffuse_color.attribute_type = "OBJECT"
    diffuse_color.attribute_name = "active_material.DSCS_MaterialProperties.diffuse_color"
    diffuse_color.name  = "Diffuse Color"
    diffuse_color.label = "Diffuse Color"
    diffuse_color.location = diffuse_color_anchor + Vector((0, -200))
    
    total_diffuse_color = nodes.new('ShaderNodeMix')
    total_diffuse_color.data_type = "RGBA"
    total_diffuse_color.blend_type = "MULTIPLY"
    total_diffuse_color.clamp_result = False
    total_diffuse_color.clamp_factor = True
    total_diffuse_color.location = diffuse_color_anchor + Vector((200, 0))
     
    diffuse_contribution = nodes.new('ShaderNodeMix')
    diffuse_contribution.data_type = "RGBA"
    diffuse_contribution.blend_type = "MULTIPLY"
    diffuse_contribution.clamp_result = False
    diffuse_contribution.clamp_factor = True
    diffuse_contribution.name  = "Diffuse Contribution"
    diffuse_contribution.label = "Diffuse Contribution"
    diffuse_contribution.inputs["Factor"].default_value = 1.
    diffuse_contribution.location = diffuse_color_anchor + Vector((400, 250))
    
    total_diffuse_color.inputs[6].default_value = [1., 1., 1., 1.] # A_Color
    connect(diffuse_color     .outputs["Color"], total_diffuse_color.inputs[7]) # B_Color
    connect(use_diffuse_color.outputs["Fac"],   total_diffuse_color.inputs["Factor"])
    
    connect(vertex_color_mix   .outputs[2], diffuse_contribution.inputs[6]) # Result, A_Color
    connect(total_diffuse_color.outputs[2], diffuse_contribution.inputs[7]) # Result, B_Color
    total_diffuse_color.inputs["Factor"].default_value = 1.
    
    
    working_result = diffuse_contribution.outputs[2]
    
    ##############################
    # DIFFUSE ALPHA CONTRIBUTION #
    ##############################
    
    
    ####################
    # DIFFUSE LIGHTING #
    ####################
    clut_anchor = Vector((-300, -800))
    
    use_clut = nodes.new('ShaderNodeAttribute')
    use_clut.attribute_type = "OBJECT"
    use_clut.attribute_name = "active_material.DSCS_MaterialProperties.clut_sampler.active"
    use_clut.name  = "Use CLUT"
    use_clut.label = "Use CLUT"
    use_clut.location = clut_anchor + Vector((0, 0))
    
    clamped_lambert_term = nodes.new('ShaderNodeMath')
    clamped_lambert_term.operation = "MAXIMUM"
    clamped_lambert_term.name  = "Clamped Lambert Term"
    clamped_lambert_term.label = "Clamped Lambert Term"
    clamped_lambert_term.location = clut_anchor + Vector((0, -200))
    connect(group_inputs.outputs["Lambert Term"], clamped_lambert_term.inputs[0])
    clamped_lambert_term.inputs[1].default_value = 0.
    
    lambert_factor = nodes.new('ShaderNodeCombineColor')
    lambert_factor.name  = "Lambert Factor"
    lambert_factor.label = "Lambert Factor"
    lambert_factor.location = clut_anchor + Vector((200, -200))
    connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Red"])
    connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Green"])
    connect(clamped_lambert_term.outputs[0], lambert_factor.inputs["Blue"])
    
    diffuse_lighting = nodes.new('ShaderNodeMix')
    diffuse_lighting.data_type = "RGBA"
    diffuse_lighting.blend_type = "MIX"
    diffuse_lighting.clamp_result = False
    diffuse_lighting.clamp_factor = True
    diffuse_lighting.name  = "Diffuse Lighting"
    diffuse_lighting.label = "Diffuse Lighting"
    diffuse_lighting.location = clut_anchor + Vector((400, -200))
    connect(use_clut            .outputs["Fac"], diffuse_lighting.inputs["Factor"])
    connect(lambert_factor.outputs[0],           diffuse_lighting.inputs[6])
    connect(group_inputs.outputs["CLUTSampler"], diffuse_lighting.inputs[7])
    
    light_color = nodes.new('ShaderNodeCombineColor')
    light_color.name  = "Light Color"
    light_color.label = "Light Color"
    light_color.location = clut_anchor + Vector((400, -400))
    light_color.inputs["Red"].default_value = 1.
    light_color.inputs["Green"].default_value = 1.
    light_color.inputs["Blue"].default_value = 1.
    
    diffuse_lighting_color = nodes.new('ShaderNodeMix')
    diffuse_lighting_color.data_type = "RGBA"
    diffuse_lighting_color.blend_type = "MULTIPLY"
    diffuse_lighting_color.clamp_result = False
    diffuse_lighting_color.clamp_factor = True
    diffuse_lighting_color.name  = "Diffuse Lighting Color"
    diffuse_lighting_color.label = "Diffuse Lighting Color"
    diffuse_lighting_color.location = clut_anchor + Vector((600, -200))
    diffuse_lighting_color.inputs["Factor"].default_value = 1.
    connect(diffuse_lighting.outputs[2], diffuse_lighting_color.inputs[6])
    connect(light_color     .outputs[0], diffuse_lighting_color.inputs[7])
    
    #####################
    # SPECULAR LIGHTING #
    #####################
    
    
    ###############
    # REFLECTIONS #
    ###############
    reflections_anchor = Vector((1200, -800))
    
    # Reflection Strength
    use_reflections = nodes.new('ShaderNodeAttribute')
    use_reflections.attribute_type = "OBJECT"
    use_reflections.attribute_name = "active_material.DSCS_MaterialProperties.use_reflections"
    use_reflections.name  = "Use Reflections"
    use_reflections.label = "Use Reflections"
    use_reflections.location = reflections_anchor + Vector((0, 0))
    
    raw_reflection_strength = nodes.new('ShaderNodeAttribute')
    raw_reflection_strength.attribute_type = "OBJECT"
    raw_reflection_strength.attribute_name = "active_material.DSCS_MaterialProperties.reflection_strength"
    raw_reflection_strength.name  = "Input Reflection Strength"
    raw_reflection_strength.label = "Input Reflection Strength"
    raw_reflection_strength.location = reflections_anchor + Vector((0, -200))
    
    reflection_strength = nodes.new('ShaderNodeMath')
    reflection_strength.operation = "MULTIPLY"
    reflection_strength.name  = "Reflection Strength"
    reflection_strength.label = "Reflection Strength"
    reflection_strength.location = reflections_anchor + Vector((200, -50))
    connect(use_reflections        .outputs["Fac"], reflection_strength.inputs[0])
    connect(raw_reflection_strength.outputs["Fac"], reflection_strength.inputs[1])
    
    # Fresnel Min
    use_fresnel_min = nodes.new('ShaderNodeAttribute')
    use_fresnel_min.attribute_type = "OBJECT"
    use_fresnel_min.attribute_name = "active_material.DSCS_MaterialProperties.use_fresnel_min"
    use_fresnel_min.name  = "Use FresnelMin"
    use_fresnel_min.label = "Use FresnelMin"
    use_fresnel_min.location = reflections_anchor + Vector((0, -400))
    
    raw_fresnel_min = nodes.new('ShaderNodeAttribute')
    raw_fresnel_min.attribute_type = "OBJECT"
    raw_fresnel_min.attribute_name = "active_material.DSCS_MaterialProperties.fresnel_min"
    raw_fresnel_min.name  = "Input FresnelMin"
    raw_fresnel_min.label = "Input FresnelMin"
    raw_fresnel_min.location = reflections_anchor + Vector((0, -600))
    
    fresnel_min = nodes.new('ShaderNodeMix')
    fresnel_min.data_type = "FLOAT"
    fresnel_min.blend_type = "MIX"
    fresnel_min.clamp_result = False
    fresnel_min.clamp_factor = True
    fresnel_min.location = reflections_anchor + Vector((200, -450))
    connect(use_fresnel_min.outputs["Fac"],   fresnel_min.inputs[0])
    fresnel_min.inputs[2].default_value = 1.
    connect(raw_fresnel_min.outputs[0], fresnel_min.inputs[3])
    
    # Fresnel Exp
    use_fresnel_exp = nodes.new('ShaderNodeAttribute')
    use_fresnel_exp.attribute_type = "OBJECT"
    use_fresnel_exp.attribute_name = "active_material.DSCS_MaterialProperties.use_fresnel_exp"
    use_fresnel_exp.name  = "Use FresnelExp"
    use_fresnel_exp.label = "Use FresnelExp"
    use_fresnel_exp.location = reflections_anchor + Vector((0, -600))
    
    raw_fresnel_exp = nodes.new('ShaderNodeAttribute')
    raw_fresnel_exp.attribute_type = "OBJECT"
    raw_fresnel_exp.attribute_name = "active_material.DSCS_MaterialProperties.fresnel_exp"
    raw_fresnel_exp.name  = "Input FresnelExp"
    raw_fresnel_exp.label = "Input FresnelExp"
    raw_fresnel_exp.location = reflections_anchor + Vector((0, -800))
    
    fresnel_exp = nodes.new('ShaderNodeMix')
    fresnel_exp.data_type = "FLOAT"
    fresnel_exp.blend_type = "MIX"
    fresnel_exp.clamp_result = False
    fresnel_exp.clamp_factor = True
    fresnel_exp.location = reflections_anchor + Vector((200, -650))
    connect(use_fresnel_exp.outputs["Fac"],   fresnel_exp.inputs[0])
    fresnel_exp.inputs[2].default_value = 1.
    connect(raw_fresnel_exp.outputs[0], fresnel_exp.inputs[3])
    
    # Minimum Reflection value
    min_reflection_strength = nodes.new('ShaderNodeMath')
    min_reflection_strength.operation = "MULTIPLY"
    min_reflection_strength.name  = "Minimum Reflection Strength"
    min_reflection_strength.label = "Minimum Reflection Strength"
    min_reflection_strength.location = reflections_anchor + Vector((400, -150))
    connect(reflection_strength.outputs[0], min_reflection_strength.inputs[0])
    connect(fresnel_min        .outputs[0], min_reflection_strength.inputs[1])
    
    # Inverted Exponent
    inv_fresnel_exp = nodes.new('ShaderNodeMath')
    inv_fresnel_exp.operation = "DIVIDE"
    inv_fresnel_exp.name  = "Inverse FresnelExp"
    inv_fresnel_exp.label = "Inverse FresnelExp"
    inv_fresnel_exp.location = reflections_anchor + Vector((400, -650))
    inv_fresnel_exp.inputs[0].default_value = 1.
    connect(fresnel_exp        .outputs[0], inv_fresnel_exp.inputs[1])
    
    # Interpolation Value
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.name  = "Geometry"
    geometry.label = "Geometry"
    geometry.location = reflections_anchor + Vector((0, -1000))
    
    incident_angle = nodes.new("ShaderNodeVectorMath")
    incident_angle.operation = "DOT_PRODUCT"
    incident_angle.name  = "Incident Angle"
    incident_angle.label = "Incident Angle"
    incident_angle.location = reflections_anchor + Vector((200, -1000))
    connect(geometry.outputs["Incoming"], incident_angle.inputs[0])
    connect(geometry.outputs["Normal"],   incident_angle.inputs[1])
    
    abs_incident_angle = nodes.new("ShaderNodeMath")
    abs_incident_angle.operation = "ABSOLUTE"
    abs_incident_angle.name  = "Abs Incident Angle"
    abs_incident_angle.label = "Abs Incident Angle"
    abs_incident_angle.location = reflections_anchor + Vector((400, -1000))
    connect(incident_angle.outputs[1], abs_incident_angle.inputs[0])
    
    interpolation_value = nodes.new("ShaderNodeMath")
    interpolation_value.operation = "POWER"
    interpolation_value.name  = "Interpolation Value"
    interpolation_value.label = "Interpolation Value"
    interpolation_value.location = reflections_anchor + Vector((600, -1000))
    connect(abs_incident_angle.outputs[0], interpolation_value.inputs[0])
    connect(inv_fresnel_exp.outputs[0], interpolation_value.inputs[1])
    
    # Fresnel Effect Reflection Strength
    fresnel_effect = nodes.new('ShaderNodeMix')
    fresnel_effect.data_type = "FLOAT"
    fresnel_effect.blend_type = "MIX"
    fresnel_effect.clamp_result = False
    fresnel_effect.clamp_factor = True
    fresnel_effect.name  = "Fresnel Effect Reflection Strength"
    fresnel_effect.label = "Fresnel Effect Reflection Strength"
    fresnel_effect.location = reflections_anchor + Vector((800, -850))
    connect(interpolation_value    .outputs[0], fresnel_effect.inputs[0])
    connect(reflection_strength    .outputs[0], fresnel_effect.inputs[2])
    connect(min_reflection_strength.outputs[0], fresnel_effect.inputs[3])
    
    # Reflection Color
    reflection_color = nodes.new("ShaderNodeVectorMath")
    reflection_color.operation = "SCALE"
    reflection_color.name  = "Reflection"
    reflection_color.label = "Reflection"
    reflection_color.location = reflections_anchor + Vector((1000, -850))
    connect(group_inputs  .outputs["EnvSampler"], reflection_color.inputs[0])
    connect(fresnel_effect.outputs["Result"],     reflection_color.inputs[3])
    
    
    
    ################
    # FINAL COLOUR #
    ################
    results_anchor = Vector((1000, 0))
    
    # + Diffuse Lighting
    use_dir_lights = nodes.new('ShaderNodeAttribute')
    use_dir_lights.attribute_type = "OBJECT"
    use_dir_lights.attribute_name = "active_material.DSCS_MaterialProperties.use_dir_light"
    use_dir_lights.name  = "Use Directional Lighting"
    use_dir_lights.label = "Use Directional Lighting"
    use_dir_lights.location = results_anchor + Vector((0, 200))
    
    plus_diff_light = nodes.new('ShaderNodeMix')
    plus_diff_light.data_type = "RGBA"
    plus_diff_light.blend_type = "MULTIPLY"
    plus_diff_light.clamp_result = False
    plus_diff_light.clamp_factor = True
    plus_diff_light.name  = "+ Diffuse Lighting"
    plus_diff_light.label = "+ Diffuse Lighting"
    plus_diff_light.location = results_anchor + Vector((200, 0))
    connect(use_dir_lights        .outputs["Fac"], plus_diff_light.inputs["Factor"])
    connect(working_result,                        plus_diff_light.inputs[6])
    connect(diffuse_lighting_color.outputs[2],     plus_diff_light.inputs[7])
    
    working_result = plus_diff_light.outputs[2]
    
    # + Reflections
    plus_reflection = nodes.new("ShaderNodeVectorMath")
    plus_reflection.operation ="ADD"
    plus_reflection.name  = "+ Reflection"
    plus_reflection.label = "+ Reflection"
    plus_reflection.location = plus_diff_light.location + Vector((400, 0))
    connect(working_result,              plus_reflection.inputs[0])
    connect(reflection_color.outputs[0], plus_reflection.inputs[1])
    
    working_result = plus_reflection.outputs[0]
    
    ###########
    # glBlend #
    ###########
    glblend_anchor = Vector((2500, 0))
    
    glblend_frame = nodes.new("NodeFrame")
    glblend_frame.label = "glBlend"
    glblend_frame.location = glblend_anchor
    
    rgb_split = nodes.new("ShaderNodeSeparateColor")
    rgb_split.parent = glblend_frame
    rgb_split.location = Vector((0, 0))
    connect(working_result, rgb_split.inputs[0])
    
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
    
    ###################
    # POST-PROCESSING #
    ###################
    
    # + glBlend
    use_gl_blend = nodes.new('ShaderNodeAttribute')
    use_gl_blend.attribute_type = "OBJECT"
    use_gl_blend.attribute_name = "active_material.DSCS_MaterialProperties.use_gl_blend"
    use_gl_blend.name  = "Use glBlend"
    use_gl_blend.label = "Use glBlend"
    use_gl_blend.location = results_anchor + Vector((600, 200))
    
    gl_blend_shader = nodes.new("ShaderNodeMixShader")
    gl_blend_shader.location = results_anchor + Vector((800, 0))
    connect(use_gl_blend.outputs["Fac"], gl_blend_shader.inputs[0])
    connect(working_result,              gl_blend_shader.inputs[1])
    connect(rgb_shader  .outputs[0],     gl_blend_shader.inputs[2])
    
    working_result = gl_blend_shader.outputs[0]
    
    ##########
    # EXPORT #
    ##########
    
    # create group outputs
    group_outputs = dscs_shader.nodes.new('NodeGroupOutput')
    group_outputs.location = results_anchor + Vector((1000,0))
    dscs_shader.outputs.new('NodeSocketShader','Shader')
    
    connect(working_result, group_outputs.inputs['Shader'])


def define_clut_uv_node_group():
    clut_uv = bpy.data.node_groups.new("DSCS CLUT UV", "ShaderNodeTree")
    
    nodes = clut_uv.nodes
    links = clut_uv.links
    connect = links.new
    
    # create group inputs
    group_inputs = clut_uv.nodes.new('NodeGroupInput')
    inputs = clut_uv.inputs
    group_inputs.location = (-500,0)
    
    # create group outputs
    group_outputs = clut_uv.nodes.new('NodeGroupOutput')
    group_outputs.location = (1100,0)
    clut_uv.outputs.new('NodeSocketVector','UV')
    clut_uv.outputs.new('NodeSocketFloat','Lambert Term')
    clut_uv.outputs.new('NodeSocketFloat','Reflection Intensity')
    
    
    ##################
    # UV CALCULATION #
    ##################
    clut_uv_anchor = Vector((-300, 0))

    # Basic vectors
    dirlight_anchor = clut_uv_anchor
    light_direction = nodes.new('ShaderNodeVectorMath')
    light_direction.operation = "NORMALIZE"
    light_direction.name  = "Light Direction"
    light_direction.label = "Light Direction"
    light_direction.inputs[0].default_value[0] = +1.
    light_direction.inputs[0].default_value[1] = -1.
    light_direction.inputs[0].default_value[2] = +1.
    light_direction.location = dirlight_anchor + Vector((0, 0))
    
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.name  = "Geometry"
    geometry.label = "Geometry"
    geometry.location = dirlight_anchor + Vector((0, -300))
    
    lambert_term = nodes.new('ShaderNodeVectorMath')
    lambert_term.operation = "DOT_PRODUCT"
    lambert_term.name  = "Lambert Term"
    lambert_term.label = "Lambert Term"
    lambert_term.location = dirlight_anchor + Vector((200, 0))
    connect(light_direction.outputs["Vector"], lambert_term.inputs[0])
    connect(geometry       .outputs["Normal"], lambert_term.inputs[1])
    
    raw_half_vector = nodes.new('ShaderNodeVectorMath')
    raw_half_vector.operation = "ADD"
    raw_half_vector.name  = "Raw Half Vector"
    raw_half_vector.label = "Raw Half Vector"
    raw_half_vector.location = dirlight_anchor + Vector((200, -150))
    connect(light_direction.outputs["Vector"],   raw_half_vector.inputs[0])
    connect(geometry       .outputs["Incoming"], raw_half_vector.inputs[1])
    
    half_vector = nodes.new('ShaderNodeVectorMath')
    half_vector.operation = "NORMALIZE"
    half_vector.name  = "Half Vector"
    half_vector.label = "Half Vector"
    half_vector.location = dirlight_anchor + Vector((400, -150))
    connect(raw_half_vector.outputs["Vector"], half_vector.inputs[0])
    
    reflection_intensity = nodes.new('ShaderNodeVectorMath')
    reflection_intensity.operation = "DOT_PRODUCT"
    reflection_intensity.name  = "Reflection Intensity"
    reflection_intensity.label = "Reflection Intensity"
    reflection_intensity.location = dirlight_anchor + Vector((600, -200))
    connect(half_vector.outputs["Vector"], reflection_intensity.inputs[0])
    connect(geometry   .outputs["Normal"], reflection_intensity.inputs[1])
    
    # U Coordinate
    rescaled_u = nodes.new('ShaderNodeMath')
    rescaled_u.operation = "MULTIPLY"
    rescaled_u.name  = "Rescaled U"
    rescaled_u.label = "Rescaled U"
    rescaled_u.location = dirlight_anchor + Vector((800, 100))
    connect(lambert_term.outputs[1], rescaled_u.inputs[0])
    rescaled_u.inputs[1].default_value = 0.495
    
    u_coord = nodes.new('ShaderNodeMath')
    u_coord.operation = "ADD"
    u_coord.name  = "V Coord"
    u_coord.label = "V Coord"
    u_coord.location = dirlight_anchor + Vector((1000, 100))
    connect(rescaled_u.outputs[0], u_coord.inputs[0])
    u_coord.inputs[1].default_value = 0.500
    
    # V Coordinate
    rescaled_v = nodes.new('ShaderNodeMath')
    rescaled_v.operation = "MULTIPLY"
    rescaled_v.name  = "Rescaled V"
    rescaled_v.label = "Rescaled V"
    rescaled_v.location = dirlight_anchor + Vector((800, -200))
    connect(reflection_intensity.outputs[1], rescaled_v.inputs[0])
    rescaled_v.inputs[1].default_value = 0.980
    
    v_coord = nodes.new('ShaderNodeMath')
    v_coord.operation = "ADD"
    v_coord.name  = "V Coord"
    v_coord.label = "V Coord"
    v_coord.location = dirlight_anchor + Vector((1000, -200))
    connect(rescaled_v.outputs[0], v_coord.inputs[0])
    v_coord.inputs[1].default_value = 0.010
    
    # Output vector
    
    uv_coord = nodes.new('ShaderNodeCombineXYZ')
    uv_coord.name  = "UV Coords"
    uv_coord.label = "UV Coords"
    uv_coord.location = dirlight_anchor + Vector((1200, -50))
    connect(u_coord.outputs[0], uv_coord.inputs[0])
    connect(v_coord.outputs[0], uv_coord.inputs[1])
    
    # link output
    connect(uv_coord            .outputs[0], group_outputs.inputs['UV'])
    connect(lambert_term        .outputs[1], group_outputs.inputs['Lambert Term'])
    connect(reflection_intensity.outputs[1], group_outputs.inputs['Reflection Intensity'])


def define_refl_uv_node_group():
    refl_uv = bpy.data.node_groups.new("DSCS Reflection UV", "ShaderNodeTree")
    
    nodes = refl_uv.nodes
    links = refl_uv.links
    connect = links.new
    
    # create group inputs
    group_inputs = refl_uv.nodes.new('NodeGroupInput')
    inputs = refl_uv.inputs
    group_inputs.location = (-500,0)
    
    # create group outputs
    group_outputs = refl_uv.nodes.new('NodeGroupOutput')
    group_outputs.location = (800,0)
    refl_uv.outputs.new('NodeSocketVector','UV')
    
    ##################
    # UV CALCULATION #
    ##################
    refl_uv_anchor = Vector((0, 0))

    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.name  = "Geometry"
    geometry.label = "Geometry"
    geometry.location = refl_uv_anchor + Vector((0, -300))
    
    reflection_vector = nodes.new('ShaderNodeVectorMath')
    reflection_vector.operation = "REFLECT"
    reflection_vector.name  = "Reflection Vector"
    reflection_vector.label = "Reflection Vector"
    reflection_vector.location = refl_uv_anchor + Vector((200, 0))
    connect(geometry.outputs["Incoming"], reflection_vector.inputs[0])
    connect(geometry.outputs["Normal"],   reflection_vector.inputs[1])
    
    u_coordinate = nodes.new('ShaderNodeVectorMath')
    u_coordinate.operation = "DOT_PRODUCT"
    u_coordinate.name  = "U Coordinate"
    u_coordinate.label = "U Coordinate"
    u_coordinate.location = refl_uv_anchor + Vector((400, 0))
    connect(reflection_vector.outputs["Vector"], u_coordinate.inputs[0])
    u_coordinate.inputs[1].default_value[0] = -1.
    u_coordinate.inputs[1].default_value[1] =  1.
    u_coordinate.inputs[1].default_value[2] =  0.
    
    v_coordinate = nodes.new('ShaderNodeVectorMath')
    v_coordinate.operation = "DOT_PRODUCT"
    v_coordinate.name  = "V Coordinate"
    v_coordinate.label = "V Coordinate"
    v_coordinate.location = refl_uv_anchor + Vector((400, -300))
    connect(reflection_vector.outputs["Vector"], v_coordinate.inputs[0])
    v_coordinate.inputs[1].default_value[0] =  0.
    v_coordinate.inputs[1].default_value[1] =  1.
    v_coordinate.inputs[1].default_value[2] = -1.
    
    uv_coord = nodes.new('ShaderNodeCombineXYZ')
    uv_coord.name  = "UV Coords"
    uv_coord.label = "UV Coords"
    uv_coord.location = refl_uv_anchor + Vector((600, 0))
    connect(u_coordinate.outputs[1], uv_coord.inputs[0])
    connect(v_coordinate.outputs[1], uv_coord.inputs[1])
    
    # link output
    connect(uv_coord.outputs[0], group_outputs.inputs['UV'])
