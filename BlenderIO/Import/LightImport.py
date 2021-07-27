import bpy
import numpy as np


def import_lights(parent_obj, model_data):
    for i, light_data in enumerate(model_data.light_sources):
        if light_data.mode == 0:  # Directional
            l_type = "SUN"
        elif light_data.mode == 2:  # Ambient
            l_type = "AREA"
        elif light_data.mode == 3:  # Point
            l_type = "POINT"
        elif light_data.mode == 4:  # Fog
            l_type = "AREA"
        else:
            assert 0, f"Unknown light mode enum \'{light_data.mode}\'."

        light = bpy.data.lights.new(f"{parent_obj.name} Light {i}", l_type)
        if light_data.mode == 4:
            light["Unknown_Fog_Param"] = light_data.unknown_fog_param
        light.energy = light_data.intensity
        light.color = (light_data.red, light_data.green, light_data.blue)
        light["Alpha"] = light_data.alpha

        light_obj = bpy.data.objects.new(f"{parent_obj.name} Light {i}", light)
        bpy.context.collection.objects.link(light_obj)
        light_obj.parent = parent_obj
        # light_obj.rotation_euler[0] = -90 * (np.pi/180)
        # constraint = light_obj.constraints.new("CHILD_OF")
        # constraint.target = bpy.data.objects[f"{parent_obj.name}_armature"]
        #
        # constraint.subtarget = light_data.bone_name
        light['target_bone_hash'] = light_data.bone_name
