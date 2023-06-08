import bpy
import struct

from ...Utilities.Hash import dscs_hash_string
from ..IOHelpersLib.Animations import create_fcurves, create_fcurve
from ..IOHelpersLib.Animations import parent_relative_to_bind_relative
from ..IOHelpersLib.Animations import parent_relative_to_bind_relative_preblend
from ..IOHelpersLib.Context    import safe_active_object_switch, set_active_obj
from ..Utils.BoneUtils import boneY_to_boneX_matrix, upY_to_upZ_matrix

from mathutils import Matrix, Quaternion


@safe_active_object_switch
def import_base_animation(directory, name_prefix, armature, ni, base_anim):
    armature.animation_data_create()
    set_active_obj(armature)
    
    bpy.ops.object.mode_set(mode="POSE")
    rotations = convert_to_mathutils_quats(base_anim)
    construct_nla_action("base", name_prefix, armature, build_base_fcurves,
                         base_anim.locations, rotations, base_anim.scales,
                         base_anim.float_channels,
                         ni.bone_names, base_anim.playback_rate, "REPLACE")
    bpy.ops.object.mode_set(mode="OBJECT")


@safe_active_object_switch
def import_animations(directory, name_prefix, armature, ni, ais):
    # Need to remove dependence on NameInterface for separate anim import
    armature.animation_data_create()
    set_active_obj(armature)
    
    bpy.ops.object.mode_set(mode="POSE")    
    for animation_name, animation_data in list(ais.items()):
        track_name = animation_name[len(name_prefix)+1:]  # +1 to also remove the underscore
        rotations = convert_to_mathutils_quats(animation_data)
        construct_nla_action(track_name, animation_name, armature, build_blend_fcurves,
                             animation_data.locations, rotations, animation_data.scales,
                             animation_data.float_channels,
                             ni.bone_names, animation_data.playback_rate, "COMBINE")
    bpy.ops.object.mode_set(mode="OBJECT")

#########
# UTILS #
#########

# Need to move this elsewhere
def is_constraint_child_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "CHILD_OF":
                if constr.target == parent_obj:
                    return True
    return False

def is_copy_transforms_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "COPY_TRANSFORMS":
                if constr.target == parent_obj:
                    return True
    return False

def find_bpy_objects(obj_list, parent_obj, predicates):
    out = []
    for obj in obj_list:
        if any((obj.parent == parent_obj,
               is_constraint_child_of(obj, parent_obj),
               is_copy_transforms_of(obj, parent_obj))) \
        and all([p(obj) for p in predicates]):
            out.append(obj)
    return out


# Now here are the real methods
def convert_to_mathutils_quats(anim):
    return {k: {k2: Quaternion([r[3], r[0], r[1], r[2]])  for k2, r in rdata.items()} for k, rdata in anim.rotations.items()}

# DISGUSTING
# SET UP A PROPER LIST OF OBJECTS FOR SHADER UNIFORMS, YOU FILTHY ANIMAL
HANDLED_UNIFORMS = [0x33, 0x36, 0x38, 0x39, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F,
                    0x40, 0x41, 0x42, 0x46, 0x47, 0x4F,
                    0x50, 0x55, 0x58, 0x5B, 0x5E,
                    0x61, 0x64, 
                    0x71, 0x72, 0x74, 0x77, 0x78, 0x7B, 0x7E, 
                    0x81, 0x84, 0x87, 0x8D]

def construct_nla_action(track_name, action_name, armature, method, positions, rotations, scales, float_channels, bone_names, playback_rate, blend_type):
    action = bpy.data.actions.new(action_name)

    for positions, rotations, scales, bone_name in zip(positions.values(),
                                                       rotations.values(),
                                                       scales.values(),
                                                       bone_names):
        method(action, armature, bone_name, 1, positions, rotations, scales)

    armature.animation_data.action = action
    track = armature.animation_data.nla_tracks.new()
    track.name = track_name
    track.mute = True
    nla_strip = track.strips.new(action.name, int(action.frame_range[0]), action)
    nla_strip.scale = 24 / playback_rate
    nla_strip.blend_type = blend_type
    armature.animation_data.action = None

    ##################
    # FLOAT CHANNELS #
    ##################
    props = action.DSCS_AnimationProperties
    skel_float_channels = armature.data.DSCS_ModelProperties.float_channels
    material_hashes = {struct.unpack('i', struct.pack('I', dscs_hash_string(mesh.active_material.name)))[0]: mesh.active_material for mesh in [obj for obj in armature.children if obj.type == "MESH"] if mesh.active_material is not None}
    
    material_fcurves = {}
    camera_fcurves = {}
    light_fcurves = {}
    unhandled_fcurves = {}
    
    for fc_idx, fc in float_channels.items():
        # Locate the float channel data
        if fc_idx < len(skel_float_channels):
            skel_fc = skel_float_channels[fc_idx]
            idx = skel_fc.channel
            array_idx = skel_fc.array_idx
            
            # Figure out if it's a material, camera, or light...
            if (skel_fc.obj_hash in material_hashes) and (idx in HANDLED_UNIFORMS):
                bpy_material = material_hashes[skel_fc.obj_hash]
                mname = bpy_material.name
                if mname not in material_fcurves: material_fcurves[mname] = {}
                if idx not in material_fcurves[mname]: material_fcurves[mname][idx] = {}
                material_fcurves[mname][idx][array_idx] = fc
                
            # elif skel_fc.obj_hash in camera_hashes:
            #     fc_type = "CAMERA"
            # elif skel_fc.obj_hash in light_hashes:
            #     fc_type = "LIGHT"
            else:
                unhandled_fcurves[fc_idx] = fc
        else:
            unhandled_fcurves[fc_idx] = fc
    
    #######################
    # MATERIAL ANIMATIONS #
    #######################
    def mk_group(action, name):
        if name not in action.groups:
            actiongroup = action.groups.new(name)
        else:
            actiongroup = action.groups[name]
        return actiongroup
    
    def mk_fcurves(group_name, rna_path, fcs):
        actiongroup = mk_group(action, group_name)
        for arr_idx, fc in fcs.items():
            create_fcurve(action, actiongroup, f'DSCS_MaterialProperties.{rna_path}', "LINEAR", fps, fc.keys(), fc.values(), arr_idx)
        
    fps = 1
    for mat_name, fcurves in material_fcurves.items():
        # Skip if the fcurves are empty
        if not any(len(fc) for _, fcs in fcurves.items() for _, fc in fcs.items()):
            continue
        
        bpy_material = bpy.data.materials[mat_name]
        bpy_material.animation_data_create()
        action = bpy.data.actions.new(f"{action_name}_{bpy_material.name}")
        
        
        for idx, fcs in fcurves.items():     
            # Assign the animation
            if   idx == 0x33: mk_fcurves("DiffuseColor",       "diffuse_color",       fcs)
            elif idx == 0x36: mk_fcurves("Bumpiness",          "bumpiness",           fcs)
            elif idx == 0x38: mk_fcurves("SpecularStrength",   "specular_strength",   fcs)
            elif idx == 0x39: mk_fcurves("SpecularPower",      "specular_power",      fcs)
            elif idx == 0x3B: mk_fcurves("ReflectionStrength", "reflection_strength", fcs)
            elif idx == 0x3C: mk_fcurves("FresnelMin",         "fresnel_min",         fcs)
            elif idx == 0x3D: mk_fcurves("FresnelExp",         "fresnel_exp",         fcs)
            elif idx == 0x3E: mk_fcurves("SurfaceColor",       "surface_color",       fcs)
            elif idx == 0x3F: mk_fcurves("SubSurfaceColor",    "subsurface_color",    fcs)
            elif idx == 0x40: mk_fcurves("FuzzySpecColor",     "fuzzy_spec_color",    fcs)
            elif idx == 0x41: mk_fcurves("Rolloff",            "rolloff",             fcs)
            elif idx == 0x42: mk_fcurves("VelvetStrength",     "velvet_strength",     fcs)
            elif idx == 0x46: mk_fcurves("OverlayBumpiness",   "overlay_bumpiness",   fcs)
            elif idx == 0x47: mk_fcurves("OverlayStrength",    "overlay_strength",    fcs)
            elif idx == 0x4F: mk_fcurves("Parallax Bias X",    "parallax_bias_x",     fcs)
            elif idx == 0x50: mk_fcurves("Parallax Bias Y",    "parallax_bias_y",     fcs)
            elif idx == 0x55: mk_fcurves("UV1 - Scroll",       "uv_1.scroll",         fcs)
            elif idx == 0x58: mk_fcurves("UV2 - Scroll",       "uv_2.scroll",         fcs)
            elif idx == 0x5B: mk_fcurves("UV3 - Scroll",       "uv_3.scroll",         fcs)
            elif idx == 0x5E: mk_fcurves("UV1 - Offset",       "uv_1.offset",         fcs)
            elif idx == 0x61: mk_fcurves("UV2 - Offset",       "uv_2.offset",         fcs)
            elif idx == 0x64: mk_fcurves("Distortion",         "distortion",          fcs)
            elif idx == 0x71: mk_fcurves("LightmapPower",      "lightmap_power",      fcs)
            elif idx == 0x72: mk_fcurves("Lightmap trength",   "lightmap_strength",   fcs)
            elif idx == 0x74: mk_fcurves("UV3 - Offset",       "uv_3.offset",         fcs)
            elif idx == 0x77: mk_fcurves("Fat",                "fat",                 fcs)
            elif idx == 0x78: mk_fcurves("UV1 - Rotation",     "uv_1.rotation",       fcs)
            elif idx == 0x7B: mk_fcurves("UV2 - Rotation",     "uv_2.rotation",       fcs)
            elif idx == 0x7E: mk_fcurves("UV3 - Rotation",     "uv_3.rotation",       fcs)
            elif idx == 0x81: mk_fcurves("UV1 - Scale",        "uv_1.scale",          fcs)
            elif idx == 0x84: mk_fcurves("UV2 - Scale",        "uv_2.scale",          fcs)
            elif idx == 0x87: mk_fcurves("UV3 - Scale",        "uv_3.scale",          fcs)
            elif idx == 0x8D: mk_fcurves("ZBias",              "zbias",               fcs)
            else:
                raise NotImplementedError(f"CRITICAL INTERNAL ERROR: UNHANDLED MATERIAL UNIFORM INDEX '{idx}'")
            bpy.context.scene.frame_set(0)
        
        track = bpy_material.animation_data.nla_tracks.new()
        track.name = track_name
        track.mute = True
        nla_strip = track.strips.new(track_name, int(action.frame_range[0]), action)
        nla_strip.scale = 24 / playback_rate
        nla_strip.blend_type = blend_type
        bpy_material.animation_data.action = None
    
    
    # If there was an error somewhere that prevented the channel being loaded...
    for fc_idx, fc in unhandled_fcurves.items():
        bpy_fc = props.float_channels.add()
        bpy_fc.channel_idx = fc_idx
        for f, v in fc.items():
            bpy_kf = bpy_fc.keyframes.add()
            bpy_kf.frame = f
            bpy_kf.value = v
    

def build_base_fcurves(action, armature, bone_name, fps, positions, rotations, scales):
    # Set up action data
    actiongroup = action.groups.new(bone_name)
    
    bpy_bone = armature.data.bones[bone_name]
    b_positions, \
    b_rotations, \
    b_scales = parent_relative_to_bind_relative(bpy_bone, 
                                                positions.values(), 
                                                rotations.values(), 
                                                scales.values(),
                                                upY_to_upZ_matrix.inverted(),
                                                Matrix.Identity(4))

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", fps, rotations.keys(), b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", fps, positions.keys(), b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", fps, scales   .keys(), b_scales,    [0, 1, 2]   )


def build_blend_fcurves(action, armature, bone_name, fps, positions, rotations, scales):
    # Set up action data
    actiongroup = action.groups.new(bone_name)

    # Get the matrices required to convert animations from DSCS -> Blender
    bpy_bone = armature.data.bones[bone_name]
    b_positions, \
    b_rotations, \
    b_scales = parent_relative_to_bind_relative_preblend(bpy_bone, 
                                                          positions.values(), 
                                                          rotations.values(), 
                                                          scales.values(),
                                                          upY_to_upZ_matrix.inverted(),
                                                          Matrix.Identity(4))

    # Create animations
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].rotation_quaternion', "BEZIER", fps, rotations.keys(), b_rotations, [0, 1, 2, 3])
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].location',            "LINEAR", fps, positions.keys(), b_positions, [0, 1, 2]   )
    create_fcurves(action, actiongroup, f'pose.bones["{bone_name}"].scale',               "LINEAR", fps, scales   .keys(), b_scales,    [0, 1, 2]   )
