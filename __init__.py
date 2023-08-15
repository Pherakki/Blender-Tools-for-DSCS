bl_info = {
        "name": "Media.Vision Import/Export (.name)",
        "description": "Imports model and animation files from Media.Vision titles.",
        "author": "Pherakki",
        "version": (0, 2, "dev"),
        "blender": (2, 80, 0),
        "location": "File > Import, File > Export",
        "warning": "",
        "wiki_url": "https://github.com/Pherakki/Blender-Tools-for-DSCS",
        "tracker_url": "https://github.com/Pherakki/Blender-Tools-for-DSCS/issues",
        "category": "Import-Export",
        }


def init_bpy():
    import bpy
    #from .BlenderIO.Import import ImportDSCS#, ImportMegido
    from .src.BlenderIO.Import.Operator import ImportDSCS, ImportDSCS_PS#, ImportMegido
    from .src.BlenderIO.Import.Menu     import MVImportSubmenu, menu_func_import
    from .src.BlenderIO.Export.Operator import ExportDSCS#, ExportMegido
    from .src.BlenderIO.Export.Menu     import MVExportSubmenu, menu_func_export
    
    from .src.BlenderIO.Properties.Animation import DSCSKeyframe
    from .src.BlenderIO.Properties.Animation import DSCSAnimFloatChannel
    from .src.BlenderIO.Properties.Animation import AnimationProperties
    from .src.BlenderIO.Properties.Bone     import BoneProperties
    from .src.BlenderIO.Properties.Camera   import CameraProperties
    from .src.BlenderIO.Properties.Collider import RagdollProperties,         \
                                                   BoxColliderProperties,     \
                                                   ComplexColliderProperties, \
                                                   ColliderProperties
    from .src.BlenderIO.Properties.Light    import LightProperties
    from .src.BlenderIO.Properties.Material import MaterialProperties,       \
                                                   color_sampler_t,          \
                                                   overlay_color_sampler_t,  \
                                                   normal_sampler_t,         \
                                                   overlay_normal_sampler_t, \
                                                   lightmap_sampler_t,       \
                                                   env_sampler_t,            \
                                                   envs_sampler_t,           \
                                                   clut_sampler_t,           \
                                                   UnhandledOpenGLSetting,   \
                                                   UnhandledMaterialUniform, \
                                                   UnhandledTextureSampler,  \
                                                   UVTransforms
    from .src.BlenderIO.Properties.Mesh     import MeshProperties
    from .src.BlenderIO.Properties.Model    import ModelProperties, DSCSSkelFloatChannel
    from .src.BlenderIO.Properties.Scene    import SceneProperties
    from .src.BlenderIO.Properties.Util     import UtilProperties
    from .src.BlenderIO.UI.Bone  import OBJECT_PT_DSCSBonePanel
    from .src.BlenderIO.UI.Camera import OBJECT_PT_DSCSCameraPanel
    from .src.BlenderIO.UI.Light import OBJECT_PT_DSCSLightPanel
    from .src.BlenderIO.UI.Mesh import OBJECT_PT_DSCSMeshPanel
    from .src.BlenderIO.UI.Materials.Material import OBJECT_PT_DSCSMaterialPanel
    from .src.BlenderIO.UI.Materials.UnhandledMaterialUniforms import OBJECT_UL_DSCSMaterialUniformUIList
    from .src.BlenderIO.UI.Materials.UnhandledMaterialUniforms import OBJECT_PT_DSCSMaterialUnhandledUniformsPanel
    from .src.BlenderIO.UI.Materials.UnhandledOpenGLSettings   import OBJECT_UL_DSCSOpenGLUIList
    from .src.BlenderIO.UI.Materials.UnhandledOpenGLSettings   import OBJECT_PT_DSCSMaterialUnhandledSettingsPanel
    from .src.BlenderIO.UI.Model  import OBJECT_PT_DSCSModelPanel
    from .src.BlenderIO.Utils.ErrorLog import ImportErrorLog
    
    CLASSES = (
        ImportDSCS,
        ImportDSCS_PS,
        ExportDSCS,
        MVImportSubmenu,
        MVExportSubmenu,
        UnhandledOpenGLSetting,
        UnhandledTextureSampler,
        UnhandledMaterialUniform,
        UVTransforms,
        color_sampler_t,
        overlay_color_sampler_t,
        normal_sampler_t,
        overlay_normal_sampler_t,
        lightmap_sampler_t,
        env_sampler_t,
        envs_sampler_t,
        clut_sampler_t,
        DSCSKeyframe,
        DSCSAnimFloatChannel,
        DSCSSkelFloatChannel,
        RagdollProperties,
        BoxColliderProperties,
        ComplexColliderProperties,
        OBJECT_PT_DSCSBonePanel,
        OBJECT_PT_DSCSCameraPanel,
        OBJECT_PT_DSCSLightPanel,
        OBJECT_PT_DSCSMeshPanel,
        OBJECT_PT_DSCSMaterialPanel,
        OBJECT_UL_DSCSMaterialUniformUIList,
        OBJECT_PT_DSCSMaterialUnhandledUniformsPanel,
        OBJECT_UL_DSCSOpenGLUIList,
        OBJECT_PT_DSCSMaterialUnhandledSettingsPanel,
        OBJECT_PT_DSCSModelPanel,
    )
    
    PROP_GROUPS = (
        (bpy.types.Armature, "DSCS_ModelProperties",     ModelProperties    ),
        (bpy.types.Action,   "DSCS_AnimationProperties", AnimationProperties),
        (bpy.types.Bone,     "DSCS_BoneProperties",      BoneProperties     ),
        (bpy.types.Camera,   "DSCS_CameraProperties",    CameraProperties   ),
        (bpy.types.Object,   "DSCS_ColliderProperties",  ColliderProperties ),
        (bpy.types.Light,    "DSCS_LightProperties",     LightProperties    ),
        (bpy.types.Material, "DSCS_MaterialProperties",  MaterialProperties ),
        (bpy.types.Mesh,     "DSCS_MeshProperties",      MeshProperties     ),
        (bpy.types.Scene,    "DSCS_SceneProperties",     SceneProperties    ),
        (bpy.types.Object,   "DSCS_UtilProperties",      UtilProperties     ),
    )
    
    LIST_ITEMS = (
        (bpy.types.TOPBAR_MT_file_import, menu_func_import),
        (bpy.types.TOPBAR_MT_file_export, menu_func_export)
    )
    
    MODULES = (
        ImportErrorLog,
    )
    
    return CLASSES, PROP_GROUPS, LIST_ITEMS, MODULES


def register():
    import bpy
    
    CLASSES, PROP_GROUPS, LIST_ITEMS, MODULES = init_bpy()
    
    # blender_version = bpy.app.version_string  # Can use this string to switch version-dependent Blender API codes
    # Note for later: multi-language support can be implemented by checking
    #     - bpy.context.preferences.view.language
    #     - bpy.context.preferences.view.use_translate_interface
    #     - bpy.context.preferences.view.use_translate_new_dataname
    #     - bpy.context.preferences.view.use_translate_tooltips
    for classtype in CLASSES:
        bpy.utils.register_class(classtype)
    
    for obj, name, prop_type in PROP_GROUPS:
        bpy.utils.register_class(prop_type)
        setattr(obj, name, bpy.props.PointerProperty(type=prop_type))
        
    for obj, elem in LIST_ITEMS:
        obj.append(elem)
    
    for module in MODULES:
        module.register()


def unregister():
    import bpy
    
    CLASSES, PROP_GROUPS, LIST_ITEMS, MODULES = init_bpy()
    
    for classtype in CLASSES[::-1]:
        bpy.utils.unregister_class(classtype)
    
    for obj, name, prop_type in PROP_GROUPS[::-1]:
        delattr(obj, name)
        bpy.utils.unregister_class(prop_type)
        
    for obj, elem in LIST_ITEMS:
        obj.remove(elem)
        
    for module in MODULES:
        module.unregister()
