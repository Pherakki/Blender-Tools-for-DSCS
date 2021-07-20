import bpy
import numpy as np


def import_cameras(parent_obj, model_data):
    for i, camera_data in enumerate(model_data.cameras):
        camera = bpy.data.cameras.new(f"{parent_obj.name} Camera {i}")
        camera.type = 'PERSP' if camera_data.projection == 0 else "ORTHO"
        camera.lens_unit = "FOV"
        camera.lens = camera_data.fov
        camera.ortho_scale = camera_data.orthographic_scale
        camera.clip_start = camera_data.zNear
        camera.clip_end = camera_data.zFar

        print(camera_data.bone_name_hash)
        print(model_data.bone_name_hashes)

        camera_obj = bpy.data.objects.new(f"{parent_obj.name} Camera {i}", camera)
        bpy.context.collection.objects.link(camera_obj)
        camera_obj.parent = parent_obj
        camera_obj.rotation_euler[0] = -90 * (np.pi/180)
        constraint = camera_obj.constraints.new("CHILD_OF")
        constraint.target = bpy.data.objects[f"{parent_obj.name}_armature"]
        target_bone_hash = hex(camera_data.bone_name_hash)[2:]
        target_bone_hash = (8-len(target_bone_hash))*'0' + target_bone_hash
        target_bone_hash = target_bone_hash[6:8] + target_bone_hash[4:6] + target_bone_hash[2:4] + target_bone_hash[0:2]
        print(target_bone_hash)
        constraint.subtarget = model_data.bone_name_hashes[target_bone_hash]
