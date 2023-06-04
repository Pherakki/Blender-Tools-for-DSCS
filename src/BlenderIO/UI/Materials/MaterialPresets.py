import bpy


diffuse_preset = {
    "name": "Diffuse",
    "available_weights": [0, 1, 2, 3, 4],
    "shader_name": "088100c1_00880111_00000000_00040000",
    "textures": ["color_sampler", "clut_sampler"],
    "uniforms": ["diffuse_color"],
    "active_uniforms": ["use_diffuse_color"],
    "attributes": ["normal", "UV1"]
}

specular_preset = {
    "name": "Specular",
    "available_weights": [0, 1, 2, 3, 4],
    "shader_name": "088101c1_00880111_00000000_00040000",
    "textures": ["color_sampler", "clut_sampler"],
    "uniforms": ["diffuse_color", "specular_strength"],
    "active_uniforms": ["use_diffuse_color", "use_specular_strength"],
    "attributes": ["normal", "UV1"]
}

reflection_preset = {
    "name": "Reflection",
    "available_weights": [0, 1, 2, 3, 4],
    "shader_name": "088101c1_00881111_00000000_00040000",
    "textures": ["color_sampler", "clut_sampler", "env_sampler"],
    "uniforms": ["diffuse_color", "specular_strength", "reflection_strength"],
    "active_uniforms": ["use_diffuse_color", "use_specular_strength", "use_reflections"],
    "attributes": ["normal", "UV1"]
}

outline_preset = {
    "name": "Outline",
    "available_weights": [0, 1, 2, 3, 4],
    "shader_name": "08800000_00000111_00040000_00040000",
    "textures": [],
    "uniforms": ["diffuse_color", "fat"],
    "active_uniforms": ["use_diffuse_color", "use_fat"],
    "attributes": ["normal"],
    "recommended_settings": {
        "diffuse_color": [0.33, 0.1749, 0.132, 1.0],
        "fat": 0.
    }
}


class Preset:
    def __init__(self, preset_def):
        self.preset = preset_def
           
    def get_name(self):
        return self.preset["name"]
    
    def available_weights(self):
        return self.preset.get("available_weights", [])
    
    def get_shader_name(self):
        return self.preset["shader_name"]
    
    def get_display_textures(self):
        return self.preset.get("textures", [])
        
    def get_display_props(self):
        return self.preset.get("uniforms", [])
    
    def get_active_props(self):
        return self.preset.get("active_uniforms", [])
    
    def get_attributes(self):
        return self.preset.get("attributes", [])
    
    def get_recommended_settings(self):
        return self.preset.get("recommended_settings")
    

presets = {p["name"]: Preset(p) for p in [diffuse_preset, specular_preset, reflection_preset, outline_preset]}


class SetPreset(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_idname = 'blender_dscstools.set_preset'
    bl_label = '<ERROR>'
    preset_id: bpy.props.StringProperty()
    
    @property
    def preset(self):
        return presets[self.preset_id]
    
    @classmethod
    def poll(cls, context):
        return context.material is not None
        
    def init_operator(self, context):
        material = context.material
        props = material.DSCS_MaterialProperties
        props.unset_all_uniforms()
        
        return props

    def execute(self, context):
        props = self.init_operator(context)
        preset = self.preset
        
        
        props.preset_id   = preset.get_name()
        props.shader_name = preset.get_shader_name()
        
        for attr in preset.get_attributes():
            if   attr == "normal":   props.requires_normals   = True
            elif attr == "tangent":  props.requires_tangets   = True
            elif attr == "binormal": props.requires_binormals = True
            elif attr == "color":    props.requires_colors    = True
            elif attr == "UV1":      props.requires_uv1s      = True
            elif attr == "UV2":      props.requires_uv2s      = True
            elif attr == "UV3":      props.requires_uv3s      = True
        
        for texture in preset.get_display_textures():
            texture_props = getattr(props, texture)
            texture_props.active = True
        
        for uniform in preset.get_active_props():
            setattr(props, uniform, True)
        
        return {'FINISHED'}

class SetPresetRecommendedSettings(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_idname = 'blender_dscstools.set_preset_settings'
    bl_label = 'Use Recommended'
    preset_id: bpy.props.StringProperty()

    @property
    def preset(self):
        return presets[self.preset_id]
    
    def execute(self, context):
        material = context.material
        props = material.DSCS_MaterialProperties
        
        preset = self.preset
        
        for uniform, value in preset.get_recommended_settings().items():
            setattr(props, uniform, value)

        # Just to get the nodes to realise they need to redraw
        for uniform in preset.get_active_props():
            setattr(props, uniform, True)
        
            
        return {'FINISHED'}


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
            if context.material is None:
                return False
            return get_props(context).active
    
        def draw_header(self, context):
            layout = self.layout
            props = get_props(context)
            
            has_img = props.image is not None
            image_name = props.image.name if has_img else "None"
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
            
    TextureSamplerPanel.__name__ = f"OBJECT_PT_DSCSMaterialPreset{sampler_name}Panel"
    
    return TextureSamplerPanel


class OBJECT_PT_DSCSPresetsPanel(bpy.types.Panel):
    bl_label       = "Preset"
    bl_idname      = "OBJECT_PT_DSCSPresetsPanel"
    bl_parent_id   = "OBJECT_PT_DSCSMaterialPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        if context.material is None:
            return False
        return context.material.DSCS_MaterialProperties.mat_def_type == "PRESET"

    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        def make_op(ui, pid):
            row = ui.row()
            preset = presets[pid]
            op = row.operator(SetPreset.bl_idname, text=pid, depress=pid == props.preset_id)
            op.preset_id = pid
        
        for pid in presets:
            make_op(layout, pid)
    
    @classmethod
    def register(cls):
        bpy.utils.register_class(SetPreset)
        bpy.utils.register_class(SetPresetRecommendedSettings)
        bpy.utils.register_class(OBJECT_PT_DSCSPresetsUniformsPanel)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(SetPreset)
        bpy.utils.unregister_class(SetPresetRecommendedSettings)
        bpy.utils.unregister_class(OBJECT_PT_DSCSPresetsUniformsPanel)
        

class OBJECT_PT_DSCSPresetsUniformsPanel(bpy.types.Panel):
    bl_label = "Uniforms"
    bl_idname = "OBJECT_PT_DSCSPresetsUniformsPanel"
    bl_parent_id = OBJECT_PT_DSCSPresetsPanel.bl_idname
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
            
    color_sampler_panel          = make_texture_panel("ColorSampler",         "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.color_sampler,         is_mapped=True)
    overlay_color_sampler_panel  = make_texture_panel("OverlayColorSampler",  "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.overlay_color_sampler, is_mapped=True)
    lightmap_sampler_panel       = make_texture_panel("LightSampler",         "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.lightmap_sampler,      is_mapped=True)
    normal_sampler_panel         = make_texture_panel("NormalSampler",        "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.normal_sampler,         is_mapped=True)
    overlay_normal_sampler_panel = make_texture_panel("OverlayNormalSampler", "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.overlay_normal_sampler, is_mapped=True)
    clut_sampler_panel           = make_texture_panel("ClutSampler",          "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.clut_sampler, is_mapped=False)
    env_sampler_panel            = make_texture_panel("EnvSampler",           "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.env_sampler,  is_mapped=False)
    envs_sampler_panel           = make_texture_panel("EnvsSampler",          "OBJECT_PT_DSCSPresetsUniformsPanel", lambda x: x.material.DSCS_MaterialProperties.envs_sampler, is_mapped=False)

    
    @classmethod
    def poll(self, context):
        if context.material is None:
            return False
        return context.material.DSCS_MaterialProperties.preset_id in presets
    
    def draw(self, context):
        mat = context.material
        layout = self.layout
        props = mat.DSCS_MaterialProperties
        
        preset = presets[props.preset_id]
        
        if preset.get_recommended_settings() is not None:
            op = layout.operator(SetPresetRecommendedSettings.bl_idname)
            op.preset_id = preset.get_name()
        
        # for texture in preset.get_textures():
        #     if texture == "color_sampler":
                
        
        for uniform in preset.get_display_props():
            layout.prop(props, uniform)
            
    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.color_sampler_panel)
        bpy.utils.register_class(cls.overlay_color_sampler_panel)
        bpy.utils.register_class(cls.lightmap_sampler_panel)
        bpy.utils.register_class(cls.normal_sampler_panel)
        bpy.utils.register_class(cls.overlay_normal_sampler_panel)
        bpy.utils.register_class(cls.clut_sampler_panel)
        bpy.utils.register_class(cls.env_sampler_panel)
        bpy.utils.register_class(cls.envs_sampler_panel)
            
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(cls.color_sampler_panel)
        bpy.utils.unregister_class(cls.overlay_color_sampler_panel)
        bpy.utils.unregister_class(cls.lightmap_sampler_panel)
        bpy.utils.unregister_class(cls.normal_sampler_panel)
        bpy.utils.unregister_class(cls.overlay_normal_sampler_panel)
        bpy.utils.unregister_class(cls.clut_sampler_panel)
        bpy.utils.unregister_class(cls.env_sampler_panel)
        bpy.utils.unregister_class(cls.envs_sampler_panel)
