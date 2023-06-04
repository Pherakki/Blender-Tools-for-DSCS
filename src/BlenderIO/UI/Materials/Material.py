import bpy

from .MaterialPresets import OBJECT_PT_DSCSPresetsPanel


class OBJECT_PT_DSCSMaterialPanel(bpy.types.Panel):
    bl_label       = "DSCS Material"
    bl_idname      = "OBJECT_PT_DSCSMaterialPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.material is not None

    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties

        layout.prop(props, "flag_0")
        layout.prop(props, "cast_shadow")
        layout.prop(props, "flag_2")
        layout.prop(props, "flag_3")
        layout.prop(props, "flag_4")
        layout.prop(props, "flag_5")
        layout.prop(props, "flag_6")
        layout.prop(props, "flag_7")
        layout.prop(props, "flag_8")
        layout.prop(props, "flag_9")
        layout.prop(props, "flag_10")
        layout.prop(props, "flag_11")
        layout.prop(props, "flag_12")
        layout.prop(props, "flag_13")
        layout.prop(props, "flag_14")
        layout.prop(props, "flag_15")
        
        layout.prop(props, "bpy_dtype")
        layout.prop(props, "mat_def_type")
        
    @classmethod
    def register(cls):
        bpy.utils.register_class(OBJECT_PT_DSCSShaderUniformsPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSPresetsPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialOpenGLPanel)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(OBJECT_PT_DSCSShaderUniformsPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSPresetsPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialOpenGLPanel)


class OBJECT_PT_DSCSShaderUniformsPanel(bpy.types.Panel):
    bl_label       = "Shader Uniforms"
    bl_parent_id   = "OBJECT_PT_DSCSMaterialPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        if context.material is None:
            return False
        return context.material.DSCS_MaterialProperties.mat_def_type == "MANUAL"

    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        layout.prop(props, "shader_name")
    
    @classmethod
    def register(cls):
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialScenePropertiesPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialVertexAttributesPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialGeneratedPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialUV1Panel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialUV2Panel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialUV3Panel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialNormalMapPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialDiffusePanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialLightingPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialReflectionPanel)
        bpy.utils.register_class(OBJECT_PT_DSCSMaterialUnrenderedPanel)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialScenePropertiesPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialVertexAttributesPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialGeneratedPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialUV1Panel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialUV2Panel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialUV3Panel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialNormalMapPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialDiffusePanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialLightingPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialReflectionPanel)
        bpy.utils.unregister_class(OBJECT_PT_DSCSMaterialUnrenderedPanel)


class OBJECT_PT_DSCSMaterialScenePropertiesPanel(bpy.types.Panel):
    bl_label       = "Scene Properties"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        scene_props = context.scene.DSCS_SceneProperties
        
        col = layout.column()
        checkbox_row = col.row()
        checkbox_row.prop(props,   "use_dir_light")
        data_col     = col.row()
        data_col.prop(scene_props, "dir_light_direction")
        data_col.enabled = props.use_dir_light
        data_col     = col.row()
        data_col.prop(scene_props, "dir_light_color")
        data_col.enabled = props.use_dir_light
        
        col = layout.column()
        checkbox_row = col.row()
        checkbox_row.prop(props, "use_ambient_light")
        data_col     = col.row()
        data_col.prop(scene_props, "ambient_color")
        data_col.enabled = props.use_ambient_light
        
        col = layout.column()
        checkbox_row = col.row()
        checkbox_row.prop(props, "use_hemisph_light")
        data_col     = col.row()
        data_col.prop(scene_props, "ground_color")
        data_col.enabled = props.use_hemisph_light
        data_col     = col.row()
        data_col.prop(scene_props, "sky_direction")
        data_col.enabled = props.use_hemisph_light
        

class OBJECT_PT_DSCSMaterialVertexAttributesPanel(bpy.types.Panel):
    bl_label       = "Vertex Attributes"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        ctr.prop(props, "requires_normals")
        ctr.prop(props, "requires_tangents")
        ctr.prop(props, "requires_binormals")
        ctr.prop(props, "requires_colors")
        ctr.prop(props, "requires_uv1")
        ctr.prop(props, "requires_uv2")
        ctr.prop(props, "requires_uv3")


class OBJECT_PT_DSCSMaterialGeneratedPanel(bpy.types.Panel):
    bl_label       = "Generated Properties"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        row = ctr.row()
        row.prop(props, "use_time", text="")
        row.prop(props, "time")
        row.active = props.use_time
        

def make_texture_panel(sampler_name, parent_id, get_props, is_mapped):
    class TextureSamplerPanel(bpy.types.Panel):
        bl_label       = ""
        bl_parent_id   = parent_id
        bl_space_type  = 'PROPERTIES'
        bl_region_type = 'WINDOW'
        bl_context     = "material"
        bl_options     = {'DEFAULT_CLOSED'}
        
        @classmethod
        def poll(self, context):
            return context.material is not None
    
        def draw_header(self, context):
            layout = self.layout
            props = get_props(context)
            
            layout.prop(props, "active", text="")
            image_name = props.image.name if props.image is not None else "None"
            layout.label(text=f"{sampler_name}: {image_name}")
            
        def draw(self, context):
            layout = self.layout
            props = get_props(context)
                
            ctr = layout.column()
            ctr.active = props.active
            
            row = ctr.row()
            row.prop_search(props, "image", bpy.data, "images")
            if is_mapped:
                row = ctr.row()
                row.prop(props, "uv_map")
                row = ctr.row()
                row.prop(props, "split_alpha")
            row = ctr.row()
            row.prop(props, "data")
            
    TextureSamplerPanel.__name__ = f"OBJECT_PT_DSCSMaterial{sampler_name}Panel"
    
    return TextureSamplerPanel


def make_uv_panel(idx, prop_getter):
    class OBJECT_PT_DSCSMaterialUVPanel(bpy.types.Panel):
        bl_label       = f"UV Map {idx}"
        bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
        bl_space_type  = 'PROPERTIES'
        bl_region_type = 'WINDOW'
        bl_context     = "material"
        bl_options     = {'DEFAULT_CLOSED'}

        @classmethod
        def poll(self, context):
            return context.material is not None
            
        def draw(self, context):
            mat = context.material
            layout = self.layout
            props = mat.DSCS_MaterialProperties
            uv_props = prop_getter(props)
            
            ctr = layout.column()
            
            row = ctr.row()
            row.prop(props, f"uv_{idx}_is_projection", text="From Screen Space")
            
            row = ctr.row()
            row.prop(uv_props, "use_scroll_speed", text="")
            row.prop(uv_props, "scroll_speed")
            row.active = uv_props.use_scroll_speed
            
            row = ctr.row()
            row.prop(uv_props, "use_rotation", text="")
            row.prop(uv_props, "rotation")
            row.active = uv_props.use_rotation
            
            row = ctr.row()
            row.prop(uv_props, "use_offset", text="")
            row.prop(uv_props, "offset")
            row.active = uv_props.use_offset
            
            row = ctr.row()
            row.prop(uv_props, "use_scale", text="")
            row.prop(uv_props, "scale")
            row.active = uv_props.use_scale
    
    OBJECT_PT_DSCSMaterialUVPanel.__name__ = f"OBJECT_PT_DSCSMaterialUV{idx}Panel"
    
    return OBJECT_PT_DSCSMaterialUVPanel


OBJECT_PT_DSCSMaterialUV1Panel = make_uv_panel(1, lambda props: props.uv_1)
OBJECT_PT_DSCSMaterialUV2Panel = make_uv_panel(2, lambda props: props.uv_2)
OBJECT_PT_DSCSMaterialUV3Panel = make_uv_panel(3, lambda props: props.uv_3)


class OBJECT_PT_DSCSMaterialNormalMapPanel(bpy.types.Panel):
    bl_label       = "Normal Mapping"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    normal_sampler_panel         = make_texture_panel("NormalSampler",        "OBJECT_PT_DSCSMaterialNormalMapPanel", lambda x: x.material.DSCS_MaterialProperties.normal_sampler,         is_mapped=True)
    overlay_normal_sampler_panel = make_texture_panel("OverlayNormalSampler", "OBJECT_PT_DSCSMaterialNormalMapPanel", lambda x: x.material.DSCS_MaterialProperties.overlay_normal_sampler, is_mapped=True)

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        row = ctr.row()
        row.prop(props, "use_bumpiness", text="")
        row.prop(props, "bumpiness")
        row.active = props.use_bumpiness
        
        row = ctr.row()
        row.prop(props, "use_overlay_bumpiness", text="")
        row.prop(props, "overlay_bumpiness")
        row.active = props.use_overlay_bumpiness
        
        row = ctr.row()
        row.prop(props, "use_parallax_bias_x", text="")
        row.prop(props, "parallax_bias_x")
        row.active = props.use_parallax_bias_x
        
        row = ctr.row()
        row.prop(props, "use_parallax_bias_y", text="")
        row.prop(props, "parallax_bias_y")
        row.active = props.use_parallax_bias_y
        
        # row = ctr.row()
        # row.prop(props, "use_distortion", text="")
        # row.prop(props, "distortion_strength")
        # row.active = props.use_distortion
        
        
    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.normal_sampler_panel)
        bpy.utils.register_class(cls.overlay_normal_sampler_panel)
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(cls.normal_sampler_panel)
        bpy.utils.unregister_class(cls.overlay_normal_sampler_panel)


class OBJECT_PT_DSCSMaterialDiffusePanel(bpy.types.Panel):
    bl_label       = "Diffuse Shading"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    color_sampler_panel         = make_texture_panel("ColorSampler",        "OBJECT_PT_DSCSMaterialDiffusePanel", lambda x: x.material.DSCS_MaterialProperties.color_sampler,         is_mapped=True)
    overlay_color_sampler_panel = make_texture_panel("OverlayColorSampler", "OBJECT_PT_DSCSMaterialDiffusePanel", lambda x: x.material.DSCS_MaterialProperties.overlay_color_sampler, is_mapped=True)
    lightmap_sampler_panel      = make_texture_panel("LightSampler",        "OBJECT_PT_DSCSMaterialDiffusePanel", lambda x: x.material.DSCS_MaterialProperties.lightmap_sampler,      is_mapped=True)

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        
        ctr = layout.column()
        row = ctr.row()
        row.prop(props, "use_diffuse_color", text="")
        row.prop(props, "diffuse_color")
        row.active = props.use_diffuse_color
        
        row = ctr.row()
        row.prop(props, "use_diffuse_str_map", text="")
        row.prop(props, "diffuse_str_map_channel")
        row.active = props.use_diffuse_str_map
        
        ctr.prop(props, "requires_colors", text="Use Vertex Colors")
        
        row = ctr.row()
        row.prop(props, "use_overlay_strength", text="")
        row.prop(props, "overlay_strength")
        row.active = props.use_overlay_strength
        
        row = ctr.row()
        row.prop(props, "use_lightmap_strength", text="")
        row.prop(props, "lightmap_strength")
        row.active = props.use_lightmap_strength
        
        row = ctr.row()
        row.prop(props, "use_lightmap_power", text="")
        row.prop(props, "lightmap_power")
        row.active = props.use_lightmap_power
        
    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.color_sampler_panel)
        bpy.utils.register_class(cls.overlay_color_sampler_panel)
        bpy.utils.register_class(cls.lightmap_sampler_panel)
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(cls.color_sampler_panel)
        bpy.utils.unregister_class(cls.overlay_color_sampler_panel)
        bpy.utils.unregister_class(cls.lightmap_sampler_panel)
        

class OBJECT_PT_DSCSMaterialLightingPanel(bpy.types.Panel):
    bl_label       = "Lighting"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    clut_sampler_panel  = make_texture_panel("ClutSampler", "OBJECT_PT_DSCSMaterialLightingPanel", lambda x: x.material.DSCS_MaterialProperties.clut_sampler, is_mapped=False)
    
    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        
        row = ctr.row()
        row.prop(props, "use_specular")
        row.active = props.use_specular
        
        row = ctr.row()
        row.prop(props, "use_specular_strength", text="")
        row.prop(props, "specular_strength")
        row.active = props.use_specular_strength
        
        row = ctr.row()
        row.prop(props, "use_specular_map", text="")
        row.prop(props, "specular_map_channel")
        row.active = props.use_specular_map
        
        row = ctr.row()
        row.prop(props, "use_specular_power", text="")
        row.prop(props, "specular_power")
        row.active = props.use_specular_power
    
        row = ctr.row()
        row.prop(props, "use_velvet_strength", text="")
        row.prop(props, "velvet_strength")
        row.active = props.use_velvet_strength
        
        row = ctr.row()
        row.prop(props, "use_rolloff", text="")
        row.prop(props, "rolloff")
        row.active = props.use_rolloff
        
        row = ctr.row()
        row.prop(props, "use_surface_color", text="")
        row.prop(props, "surface_color")
        row.active = props.use_surface_color
        
        row = ctr.row()
        row.prop(props, "use_subsurface_color", text="")
        row.prop(props, "subsurface_color")
        row.active = props.use_subsurface_color
        
        row = ctr.row()
        row.prop(props, "use_fuzzy_spec_color", text="")
        row.prop(props, "fuzzy_spec_color")
        row.active = props.use_fuzzy_spec_color
        
    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.clut_sampler_panel)
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(cls.clut_sampler_panel)


class OBJECT_PT_DSCSMaterialReflectionPanel(bpy.types.Panel):
    bl_label       = "Reflections"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    env_sampler_panel  = make_texture_panel("EnvSampler",   "OBJECT_PT_DSCSMaterialReflectionPanel", lambda x: x.material.DSCS_MaterialProperties.env_sampler,  is_mapped=False)
    envs_sampler_panel = make_texture_panel("EnvsSampler",  "OBJECT_PT_DSCSMaterialReflectionPanel", lambda x: x.material.DSCS_MaterialProperties.envs_sampler, is_mapped=False)
    
    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        row = ctr.row()
        row.prop(props, "use_reflections", text="")
        row.prop(props, "reflection_strength")
        row.active = props.use_reflections
        
        row = ctr.row()
        row.prop(props, "use_fresnel_min", text="")
        row.prop(props, "fresnel_min")
        row.active = props.use_fresnel_min
        
        row = ctr.row()
        row.prop(props, "use_fresnel_exp", text="")
        row.prop(props, "fresnel_exp")
        row.active = props.use_fresnel_exp
    
    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.env_sampler_panel)
        bpy.utils.register_class(cls.envs_sampler_panel)
        
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(cls.env_sampler_panel)
        bpy.utils.unregister_class(cls.envs_sampler_panel)


class OBJECT_PT_DSCSMaterialUnrenderedPanel(bpy.types.Panel):
    bl_label       = "Unrendered Uniforms"
    bl_parent_id   = "OBJECT_PT_DSCSShaderUniformsPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        row = ctr.row()
        row.prop(props, "use_distortion", text="")
        row.prop(props, "distortion_strength")
        row.active = props.use_distortion
        
        row = ctr.row()
        row.prop(props, "use_fat", text="")
        row.prop(props, "fat")
        row.active = props.use_fat
        
        row = ctr.row()
        row.prop(props, "use_zbias", text="")
        row.prop(props, "zbias")
        row.active = props.use_zbias


class OBJECT_PT_DSCSMaterialOpenGLPanel(bpy.types.Panel):
    bl_label       = "OpenGL Settings"
    bl_parent_id   = "OBJECT_PT_DSCSMaterialPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.material is not None
        
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        ctr = layout.column()
        
        # ALPHA
        row = ctr.row()
        row.prop(props, "use_gl_alpha")
        
        # --ALPHA FUNC
        row = ctr.split(factor=0.1)
        row.separator()
        col = row.column()
        
        row = col.row()
        row.prop(props, "use_gl_alpha_func")
        row.enabled = props.use_gl_alpha
        
        row = col.row()
        datacol = row.column()
        row = datacol.row()
        row.prop(props, "gl_alpha_func")
        if props.gl_alpha_func == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_alpha_invalid_value")
        row = datacol.row()
        row.prop(props, "gl_alpha_threshold")
        datacol.enabled = props.use_gl_alpha and props.use_gl_alpha_func
        
        # BLEND
        row = ctr.row()
        row.prop(props, "use_gl_blend")
        
        # --BLEND FUNC
        # ----SRC
        row = ctr.split(factor=0.1)
        row.separator()
        col = row.column()
        
        row = col.row()
        row.prop(props, "use_gl_blend_func")
        row.enabled = props.use_gl_blend
        
        row = col.row()
        datacol = row.column()
        row = datacol.row()
        row.prop(props, "gl_blend_func_src")
        if props.gl_blend_func_src == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_blend_func_src_invalid_value")
        # ----DST
        row = datacol.row()
        row.prop(props, "gl_blend_func_dst")
        if props.gl_blend_func_dst == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_blend_func_dst_invalid_value")
        datacol.enabled = props.use_gl_blend and props.use_gl_blend_func

        # --BLEND EQUATION
        row = ctr.split(factor=0.1)
        row.separator()
        col = row.column()
        
        row = col.row()
        row.prop(props, "use_gl_blend_eq")
        row.enabled = props.use_gl_blend
        
        row = col.row()
        datacol = row.column()
        row = datacol.row()
        row.prop(props, "gl_blend_eq")
        if props.gl_blend_eq == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_blend_eq_invalid_value")
        datacol.enabled = props.use_gl_blend and props.use_gl_blend_eq
        
        # CULL FACE
        col = ctr.column()
        
        row = col.row()
        row.prop(props, "use_gl_cull_face")
        
        row = col.split(factor=0.1)
        row.separator()
        datacol = row.column()
        row = datacol.row()
        row.prop(props, "gl_cull_face")
        if props.gl_cull_face == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_cull_face_invalid_value")
        datacol.enabled = props.use_gl_cull_face
        
        # DEPTH MASK
        row = ctr.row()
        row.prop(props, "use_gl_depth_mask")
        
        # DEPTH TEST
        row = ctr.row()
        row.prop(props, "use_gl_depth_test")
        
        # --DEPTH FUNC
        row = ctr.split(factor=0.1)
        row.separator()
        col = row.column()
        
        row = col.row()
        row.prop(props, "use_gl_depth_func")
        row.enabled = props.use_gl_depth_test
        
        row = col.row()
        datacol = row.column()
        row = datacol.row()
        row.prop(props, "gl_depth_func")
        if props.gl_depth_func == "INVALID":
            row = datacol.row()
            row.prop(props, "gl_depth_func_invalid_value")
        datacol.enabled = props.use_gl_depth_test and props.use_gl_depth_func
        
        # COLOR MASK
        col = ctr.column()
        
        row = col.row()
        row.prop(props, "use_gl_color_mask")
        
        row = col.split(factor=0.1)
        row.separator()
        datacol = row.column()
        datacol.prop(props, "gl_color_mask_r")
        datacol.prop(props, "gl_color_mask_g")
        datacol.prop(props, "gl_color_mask_b")
        datacol.prop(props, "gl_color_mask_a")
        datacol.enabled = props.use_gl_color_mask