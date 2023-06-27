import numpy as np
import bpy
from mathutils import Matrix, Quaternion

from ...Utilities.Hash import dscs_hash_string
from ...Core.FileFormats.Anim.AnimInterface import AnimInterface
from ..IOHelpersLib.Animations import extract_fcurves
from ..IOHelpersLib.Animations import synchronised_quat_bone_data_from_fcurves
from ..IOHelpersLib.Animations import synchronised_quat_object_transforms_from_fcurves
from ..IOHelpersLib.Animations import bind_relative_to_parent_relative
from ..IOHelpersLib.Animations import bind_relative_to_parent_relative_preblend
from ..IOHelpersLib.Maths import rational_approx_brute_force
from ..Utils.BoneUtils import MODEL_TRANSFORMS
from ..Utils.ModelComponents import get_child_materials


def extract_base_anim(bpy_armature_obj, errorlog, bpy_to_dscs_bone_map):
    if bpy_armature_obj.animation_data is None:
        errorlog.log_warning_message("No animation data present for '{bpy_armature_obj.name}': using bind pose as base animation")
        ai = AnimInterface()
    elif "base" not in bpy_armature_obj.animation_data.nla_tracks:
        errorlog.log_warning_message("No NLA track called 'base' found for '{bpy_armature_obj.name}': using bind pose as base animation")
        ai = AnimInterface()
    else:
        base_anim_track = bpy_armature_obj.animation_data.nla_tracks["base"]
        ai = extract_anim_channels(bpy_armature_obj, base_anim_track, {}, {}, {}, {}, errorlog, is_base=True)
        # FIX ME: PASS FLOAT CHANNELS...
        ai = transform_to_animation(bpy_armature_obj, "base", bpy_to_dscs_bone_map, errorlog, ai[0], {})
    # Load up data for any missing indices from the armature
    for bone in bpy_armature_obj.data.bones:
        bone_idx = bpy_to_dscs_bone_map[bone.name]
        
        has_pos = bone_idx in ai.locations
        has_rot = bone_idx in ai.rotations
        has_scl = bone_idx in ai.scales
        # Skip bone if it's fully accounted for
        if all((has_pos, has_rot, has_scl)):
            continue
        
        # Else, get the bind pose transform and use that...
        # since that's what Blender falls back to.
        # Although here we will of course be transforming to parent-relative
        # coordinates.
        parent = bone.parent
        if parent is None:
            parent_matrix = Matrix.Identity(4)
        else:
            parent_matrix = parent.matrix_local
            
        # Need to shove the axis permutation matrices in here to make this
        # fully general.
        # Should really cook up a "transformer" class that can be used to do
        # this stuff instead of randomly passing matrices around?!!
        pos, quat, scale = (parent_matrix.inverted() @ bone.matrix_local).decompose()
        
        if not has_pos: ai.locations[bone_idx] = {0: [pos.x, pos.y, pos.z]}
        if not has_rot: ai.rotations[bone_idx] = {0: [quat.x, quat.y, quat.z, quat.w]}
        if not has_scl: ai.scales   [bone_idx] = {0: [scale.x, scale.y, scale.z]}
        
    return ai

def extract_all_anim_channels(bpy_armature_object, errorlog, bpy_to_dscs_bone_map):
    ais = {}
    
    all_tracks = set()
    # Extract armature animations
    armature_anims = {}
    anim_data = bpy_armature_object.animation_data
    if anim_data is not None:
        for track in anim_data.nla_tracks:
            armature_anims[track.name] = track
    all_tracks.update(armature_anims.keys())
    
    # Extract material animations
    material_anims = {}
    for material_name in get_child_materials(bpy_armature_object):
        bpy_material = bpy.data.materials[material_name]
        anim_data = bpy_material.animation_data
        if anim_data is not None:
            for track in anim_data.nla_tracks:
                track_name = track.name
                if track_name not in material_anims: material_anims[track_name] = {}
                material_anims[track_name][material_name] = track
    all_tracks.update(material_anims.keys())
    
    # TODO: Extract camera animations
    camera_anims = {}
    
    # TODO: Extract light animations
    light_anims = {}
    
    # TODO: Extract unhandled animations
    unhandled_anims = {}
    
    for track_name in sorted(all_tracks):
        if track_name == "base":
            continue
        ai = extract_anim_channels(bpy_armature_object, 
                                   armature_anims .get(track_name), 
                                   material_anims .get(track_name, {}), 
                                   camera_anims   .get(track_name, {}), 
                                   light_anims    .get(track_name, {}), 
                                   unhandled_anims.get(track_name, {}), 
                                   errorlog,
                                   is_base=False)
        if ai is not None:
            ais[track_name] = ai
    
    return ais


def optimise_base_anim(ai):
    """
    Optimise the base animation by dropping any animation channels with less
    than two frames, since these are already loaded into constant skeleton data.
    """
    ai.locations      = {idx: data for idx, data in ai.locations     .items() if len(data) > 1}
    ai.rotations      = {idx: data for idx, data in ai.rotations     .items() if len(data) > 1}
    ai.scales         = {idx: data for idx, data in ai.scales        .items() if len(data) > 1}
    ai.float_channels = {idx: data for idx, data in ai.float_channels.items() if len(data) > 1}


def extract_anim_channels(bpy_armature_obj, nla_track, material_anims, camera_anims, light_anims, unhandled_anims, errorlog, is_base):
    if is_base:
        transform = bind_relative_to_parent_relative
    else:
        transform = bind_relative_to_parent_relative_preblend
    
    #############
    # BONE DATA #
    #############
    # TODO: Add support for multiple strips... just merge the keyframes into one big anim...
    node_transforms = get_bone_data(nla_track, bpy_armature_obj, 
                                    transform,
                                    MODEL_TRANSFORMS,
                                    errorlog)
    
    #################
    # MATERIAL DATA #
    #################
    handled_float_transforms = {}
    for mat_name, nla_track in material_anims.items():
        bpy_material = bpy.data.materials.get(mat_name)
        if bpy_material is None:
            continue
        handled_float_transforms[dscs_hash_string(mat_name)] = get_material_data(nla_track, bpy_material, errorlog)
    
    ###############
    # CAMERA DATA #
    ###############
    # TODO: IMPLEMENT
    pass

    ##############
    # LIGHT DATA #
    ##############
    # TODO: IMPLEMENT
    pass
    

    ###################
    # UNHANDLED ANIMS #
    ###################
    unhandled_float_transforms = {}
    
    return node_transforms, handled_float_transforms, unhandled_float_transforms
    

def transform_to_animation(bpy_armature_obj, anim_name, bpy_to_dscs_bone_map, errorlog, node_transforms, float_transforms):
    # Clean up extracted animation data
    all_frames = set()
    t = {}
    r = {}
    s = {}
    missing_bones = []
    for (bpy_bidx, bname, pos, rot, scl) in node_transforms:
        if bname not in bpy_to_dscs_bone_map:
            missing_bones.append(bname)
            continue
        dscs_bidx = bpy_to_dscs_bone_map[bname]
        t[dscs_bidx] = pos
        r[dscs_bidx] = rot
        s[dscs_bidx] = scl
        all_frames.update(pos.keys())
        all_frames.update(rot.keys())
        all_frames.update(scl.keys())
    for keyframes in float_transforms.values():
        all_frames.update(keyframes.keys())
            
    if len(missing_bones):
        newline = '\n'
        errorlog.log_warning_message(f"Animation track '{anim_name}' has animations for {len(missing_bones)} bone{'s' if len(missing_bones) > 1 else ''} that are not in the armature '{bpy_armature_obj.name}' - these have not been exported. These bones are:\n{newline.join(missing_bones)}")
    
    # Now integerise the frames
    # TODO: If two frames get chucked into the same bin, should we do something with that?
    float_frames = list(all_frames)
    # TODO: Still not right
    # Denominator can, and probably should be, a float...
    if len(float_frames):
        #integerized_frames, factor = rational_approx_brute_force(float_frames, max_denominator=1024)
        integerized_frames = [int(f) for f in float_frames]
        factor = 1
    else:
        integerized_frames = {}
        factor = 1
    
    frame_lookup = {float_frame: int_frame for float_frame, int_frame in zip(float_frames, integerized_frames)}
    
    t = {bidx: {frame_lookup[frame]: v                    for frame, v in bone_data.items()} for bidx, bone_data in t.items()}
    r = {bidx: {frame_lookup[frame]: [q.x, q.y, q.z, q.w] for frame, q in bone_data.items()} for bidx, bone_data in r.items()}
    s = {bidx: {frame_lookup[frame]: v                    for frame, v in bone_data.items()} for bidx, bone_data in s.items()}
    

    ai = AnimInterface()
    # TODO: FIX ME
    ai.playback_rate  = factor * 24 #/ strip.scale
    ai.bone_count     = len(bpy_armature_obj.data.bones)
    ai.locations      = t
    ai.rotations      = r
    ai.scales         = s
    ai.float_channels = {}#{fidx: {frame_lookup[frame]: v for frame, v in float_data.items()} for fidx, float_data in float_transforms.items()}
    
    return ai


def first_track_action(nla_track, obj_identifier, errorlog):
    strip_count = len(nla_track.strips)
    if strip_count == 0:
        return None
    elif strip_count > 1:
        errorlog.log_warning_message(f"NLA Track '{nla_track.name}' for '{obj_identifier}' has {strip_count} NLA Strips - only the first will be exported")
    strip = nla_track.strips[0]
    return strip.action
    

def get_bone_data(nla_track, bpy_armature_obj, transform, model_transforms, errorlog):
    action = first_track_action(nla_track, f"armature '{bpy_armature_obj.name}'", errorlog)
    out = []
    if action is None:
        return out
    
    bone_names = [b.name for b in bpy_armature_obj.data.bones]
    fcurves = extract_fcurves(action)
    bone_transforms = synchronised_quat_bone_data_from_fcurves(fcurves, bpy_armature_obj.pose.bones)
    
    for bone_name, ad in bone_transforms.items():
        if bone_name not in bpy_armature_obj.pose.bones:
            continue
        bpy_bone = bpy_armature_obj.data.bones[bone_name]
        t, r, s = transform(bpy_bone, 
                            ad["location"].values(),
                            [q for q in ad["rotation_quaternion"].values()],
                            ad["scale"].values(),
                            model_transforms)
        
        out.append([bone_names.index(bone_name), bone_name, 
                    {(k-1) : v for k, v in zip(ad["location"].keys(), t)}, 
                    {(k-1) : v for k, v in zip(ad["rotation_quaternion"], r)}, 
                    {(k-1) : v for k, v in zip(ad["scale"], s)}])

    return out


def get_material_data(nla_track, bpy_material, errorlog):
    action = first_track_action(nla_track, f"material '{bpy_material.name}'", errorlog)
    fcurves = extract_fcurves(action)
    
    animation_channels = {}
    # Extract all animatable bits...
    for idx, attribute in \
    [
        (0x33, "diffuse_color"      ),
        (0x36, "bumpiness"          ),
        (0x38, "specular_strength"  ),
        (0x39, "specular_power"     ),
        (0x3B, "reflection_strength"),
        (0x3C, "fresnel_min"        ),
        (0x3D, "fresnel_exp"        ),
        (0x3E, "surface_color"      ),
        (0x3F, "subsurface_color"   ),
        (0x40, "fuzzy_spec_color"   ),
        (0x41, "rolloff"            ),
        (0x42, "velvet_strength"    ),
        (0x46, "overlay_bumpiness"  ),
        (0x47, "overlay_strength"   ),
        (0x4F, "parallax_bias_x"    ),
        (0x50, "parallax_bias_y"    ),
        (0x55, "uv1.scroll"         ),
        (0x58, "uv2.scroll"         ),
        (0x5B, "uv3.scroll"         ),
        (0x5E, "uv_1.offset"        ),
        (0x61, "uv_2.offset"        ),
        (0x64, "distortion"         ),
        (0x71, "lightmap_power"     ),
        (0x72, "lightmap_strength"  ),
        (0x74, "uv_3.offset"        ),
        (0x77, "fat"                ),
        (0x78, "uv_1.rotation"      ),
        (0x7B, "uv_2.rotation"      ),
        (0x7E, "uv_3.rotation"      ),
        (0x81, "uv_1.scale"         ),
        (0x84, "uv_2.scale"         ),
        (0x87, "uv_3.scale"         ),
        (0x8D, "zbias"              ),
    ]:
        attr_key = f"DSCS_MaterialProperties.{attribute}"
        if attr_key in fcurves:
            for arr_idx, keyframes in sorted(fcurves[attr_key].items(), key=lambda item: int(item[0])):
                if arr_idx >= 0x10:
                    errorlog.log_warning_message(f"Material '{bpy_material.name}' animation for '{attribute}' animates an array index above 15 ({arr_idx}), and will be skipped")
                    continue
                elif arr_idx < 0:
                    errorlog.log_warning_message(f"Material '{bpy_material.name}' animation for '{attribute}' animates a negative array index ({arr_idx}), and will be skipped")
                    continue
                animation_idx = (idx << 4) | arr_idx
                animation_channels[animation_idx] = {kf.co[0] - 1: kf.co[1] for kf in keyframes.keyframe_points}
    return animation_channels
