import math
import struct

import bpy

from ..IOHelpersLib.Collection import init_collection
from ..IOHelpersLib.Objects import lock_obj_transforms

def import_lights(parent_collection, armature_obj, dscs_to_bpy_bone_map, gi):
    nm = armature_obj.name
    if len(gi.lights):
        collection = init_collection(f"{parent_collection.name} Lights", parent_collection)
    for i, light_data in enumerate(gi.lights):
        bpy_light = bpy.data.lights.new(f"{nm} Light {i}", "POINT")
        bpy_light.color = [light_data.red, light_data.green, light_data.blue]
        
        bpy_light_obj = bpy.data.objects.new(f"{nm} Light {i}", bpy_light)
        collection.objects.link(bpy_light_obj)
        
        bpy_light_obj.location = [0., 0., 0.]
        bpy_light_obj.rotation_euler[0] = 90 * (math.pi/180)
        bpy_light_obj.scale = [1., 1., 1.]
        lock_obj_transforms(bpy_light_obj)

        lookup = {
            0: "POINT",
            1: "UNKNOWN",
            2: "AMBIENT",
            3: "DIRECTIONAL",
            4: "FOG"
        }
        
        props = bpy_light.DSCS_LightProperties
        props.mode         = lookup[light_data.mode]
        props.light_id     = light_data.light_id
        props.intensity    = light_data.intensity
        props.fog_height   = light_data.unknown_fog_param
        props.alpha        = light_data.alpha
        props.unknown_0x20 = light_data.unknown_0x20
        props.unknown_0x24 = light_data.unknown_0x24
        props.unknown_0x28 = light_data.unknown_0x28
        props.unknown_0x2C = light_data.unknown_0x2C
       
        constraint = bpy_light_obj.constraints.new("CHILD_OF")
        constraint.target = armature_obj
        target_bone_hash = light_data.bone_name_hash
        if target_bone_hash in dscs_to_bpy_bone_map:
            constraint.subtarget = armature_obj.data.bones[dscs_to_bpy_bone_map[target_bone_hash]].name
        else:
            props.bone_hash = struct.unpack('i', struct.pack('I', target_bone_hash))[0]
