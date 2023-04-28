import math

import bpy

from ..IOHelpersLib.Collection import init_collection
from ..IOHelpersLib.Objects import lock_obj_transforms

def import_cameras(parent_collection, armature_obj, dscs_to_bpy_bone_map, gi):
    nm = armature_obj.name
    if len(gi.cameras):
        collection = init_collection(f"{parent_collection.name} Cameras", parent_collection)
    for i, camera_data in enumerate(gi.cameras):
        camera = bpy.data.cameras.new(f"{nm} Camera {i}")
        camera.type        = 'PERSP' if camera_data.projection == 0 else "ORTHO"
        camera.lens_unit   = "FOV"
        camera.angle       = camera_data.fov
        camera.ortho_scale = camera_data.orthographic_scale
        camera.clip_start  = camera_data.zNear
        camera.clip_end    = camera_data.zFar
        camera.DSCS_CameraProperties.aspect_ratio = camera_data.aspect_ratio

        camera_obj = bpy.data.objects.new(f"{nm} Camera {i}", camera)
        collection.objects.link(camera_obj)
        
        camera_obj.location = [0., 0., 0.]
        camera_obj.rotation_euler[0] = 90 * (math.pi/180)
        camera_obj.scale = [1., 1., 1.]
        lock_obj_transforms(camera_obj)
        
        constraint = camera_obj.constraints.new("CHILD_OF")
        constraint.target = armature_obj
        target_bone_hash = camera_data.bone_name_hash
        constraint.subtarget = armature_obj.data.bones[dscs_to_bpy_bone_map[target_bone_hash]].name
