import array
import math
import struct
import bpy
from mathutils import Vector, Quaternion, Matrix

from ...Core.FileFormats.Geom.GeomBinary.MeshBinary.Base import PrimitiveTypes
from ...Core.FileFormats.Geom.Constants import AttributeTypes
from ..IOHelpersLib.Meshes import create_merged_mesh, import_loop_normals, create_uv_map
from ..IOHelpersLib.Context import safe_active_object_switch, set_active_obj, set_mode
from ..IOHelpersLib.Meshes.Generation import make_cuboid


@safe_active_object_switch
def import_colliders(collection, model_name, ni, pi, errorlog):
    p = Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4()
    pinv = p.inverted()
    
    for i, collider in enumerate(pi.colliders):
        # Get geometry
        if collider.TYPE == 0:
            vertices, _, faces = make_cuboid(2*collider.half_width, 
                                             2*collider.half_height,
                                             2*collider.half_depth,
                                             [1, 1, 1])
        elif collider.TYPE == 2:
            vertices = collider.vertices
            faces    = [(t.v1, t.v2, t.v3) for t in collider.triangles]
        else:
            errorlog.log_warning_message(f"Collider {i} is an unrecognised type and was skipped")
            continue

        # Create collider mesh
        collider_name = f"{model_name}_col{i}"
        bpy_mesh = bpy.data.meshes.new(name=collider_name)
        bpy_mesh.from_pydata(vertices, [], faces)
        bpy_mesh.use_auto_smooth = True
        for poly in bpy_mesh.polygons:
            poly.use_smooth = True
        
        # Create objects
        for instance in collider.instances:
            bpy_mesh_object = bpy.data.objects.new(instance.name, bpy_mesh)
            collection.objects.link(bpy_mesh_object)
            
            loc  = (p @ Matrix.Translation(instance.position) @ pinv).to_translation()
            quat = (p @ Quaternion([instance.rotation[-1], *instance.rotation[0:3]]).to_matrix().to_4x4() @ pinv).to_quaternion()
            
            bpy_mesh_object.location = loc
            bpy_mesh_object.rotation_quaternion = quat
            bpy_mesh_object.rotation_euler = quat.to_euler('XYZ')
            bpy_mesh_object.scale = [instance.scale, instance.scale, instance.scale]

        # Set custom props
        bpy_mesh.DSCS_MeshProperties.mesh_type == "COLLIDER"

