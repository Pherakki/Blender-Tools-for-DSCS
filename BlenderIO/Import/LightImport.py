import bpy
import numpy as np


def import_lights(parent_obj, model_data):
    for i, light_data in enumerate(model_data.light_sources):
        if light_data.mode == 0:  # Point
            l_type = "POINT"
            light_name = "PointLamp" + f'{light_data.light_id}'.rjust(2, '0')
        elif light_data.mode == 2:  # Ambient
            l_type = "AREA"
            light_name = "AmbientLamp"
        elif light_data.mode == 3:  # Directional
            l_type = "SUN"
            light_name = "DirLamp" + f'{light_data.light_id}'.rjust(2, '0')
        elif light_data.mode == 4:  # Fog
            l_type = "AREA"
            light_name = "Fog"
        else:
            assert 0, f"Unknown light mode enum \'{light_data.mode}\'."

        light = bpy.data.lights.new(light_name, l_type)
        light.energy = light_data.intensity
        light.color = (light_data.red, light_data.green, light_data.blue)

        light_obj = bpy.data.objects.new(light_name, light)
        bpy.context.collection.objects.link(light_obj)
        light_obj.parent = parent_obj

        # Add data that I don't think Blender can handle
        if light_data.mode == 4:
            light_obj["Unknown_Fog_Param"] = light_data.unknown_fog_param
        light_obj["Alpha"] = light_data.alpha

        # Attach it to a bone if it isn't fog
        if light_data.mode != 4:
            light_obj.rotation_euler[0] = -90 * (np.pi/180)
            constraint = light_obj.constraints.new("CHILD_OF")
            constraint.target = bpy.data.objects[f"{parent_obj.name}_armature"]

            constraint.subtarget = light_data.bone_name
