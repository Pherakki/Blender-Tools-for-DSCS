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
def import_colliders(collection, bpy_armature, model_name, ni, pi, material_list, errorlog):
    p = Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4()
    pinv = p.inverted()
    
    material_lookup = {nm.encode('utf8'): mat for nm, mat in zip(ni.material_names, material_list)}
    
    i=0
    for _, collider in enumerate(pi.colliders):
        # Create objects
        for instance in collider.instances:
            # Create collider mesh
            collider_name = f"{model_name}_col{i}"
            bpy_mesh = bpy.data.meshes.new(name=collider_name)
            
            # Construct object
            bpy_mesh_object = bpy.data.objects.new(instance.name, bpy_mesh)
            collection.objects.link(bpy_mesh_object)
            
            props    = bpy_mesh_object.DSCS_ColliderProperties
            bpy_mesh.DSCS_MeshProperties.mesh_type = "COLLIDER"
            
            # Get geometry
            if collider.TYPE == 0:
                vertices, _, faces = make_cuboid(2*collider.half_width, 
                                                 2*collider.half_depth,
                                                 2*collider.half_height,
                                                 [1, 1, 1])
                
                # Rotate Y up -> Z up
                props.box_props["width"]  = 2*collider.half_width
                props.box_props["height"] = 2*collider.half_height
                props.box_props["depth"]  = 2*collider.half_depth
                props.collider_type = "BOX"
            elif collider.TYPE == 2:
                vertices = collider.vertices
                faces    = [(t.v1, t.v2, t.v3) for t in collider.triangles]
                props.collider_type = "COMPLEX"
            else:
                errorlog.log_warning_message(f"Collider {i} is an unrecognised type and was skipped")
                continue
            
            # Construct
            bpy_mesh.from_pydata(vertices, [], faces)
            
            # Materials
            if collider.TYPE == 0:
                active_material = material_lookup[collider.material_name]
                bpy_mesh.materials.append(active_material)
            elif collider.TYPE == 2:
                for midx, material_name in enumerate(collider.materials):
                    active_material = material_lookup[material_name]
                    bpy_mesh.materials.append(active_material)
                
                for tridx, tri in enumerate(collider.triangles):
                    bpy_mesh.polygons[tridx].material_index  = tri.material
                    
                # Convert meshes Y up -> Z up
                bpy_mesh.transform(Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4())
            
            # Object stuff
            loc  = (p @ Matrix.Translation(instance.position) @ pinv).to_translation()
            quat = (p @ Quaternion([instance.rotation[-1], *instance.rotation[0:3]]).to_matrix().to_4x4() @ pinv).to_quaternion()
            
            bpy_mesh_object.location = loc
            bpy_mesh_object.rotation_quaternion = quat
            bpy_mesh_object.rotation_euler = quat.to_euler('XYZ')
            bpy_mesh_object.scale = [instance.scale, instance.scale, instance.scale]
            
            rprops = props.ragdoll_props
            rprops.unknown_vector = instance.unknown_vec3
            rprops.unknown_float  = instance.unknown_float
            rprops.is_solid       = instance.is_solid


            if collider.TYPE == 2:    
                # Rigging
                vertex_groups = make_collider_vertex_groups(collider.triangles)
                for bone_idx, vg in vertex_groups.items():
                    vertex_group = bpy_mesh_object.vertex_groups.new(name=collider.bones[bone_idx].decode('utf8'))
                    for vert_idx, vert_weight in vg:
                        vertex_group.add([vert_idx], vert_weight, 'REPLACE')
                        
                # Set armature constraint
                modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
                modifier.object = bpy_armature
                        
            bpy_mesh_object.parent = bpy_armature
            i += 1


            # Tell Blender what we've done
            bpy_mesh.validate(verbose=True, clean_customdata=False)
            bpy_mesh.update()
            bpy_mesh.update()

    #     # Convert meshes Y up -> Z up
    #     bpy_mesh.transform(Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4())

    #     meshes.append(bpy_mesh)

    # set_material_vertex_attributes(meshes_using_material, errorlog)


def make_collider_vertex_groups(triangles):
    groups = {}
    for tri in triangles:
        bone_idx = tri.bone
        if bone_idx not in groups:
            groups[bone_idx] = []
        groups[bone_idx].append((tri.v1, 1))
        groups[bone_idx].append((tri.v2, 1))
        groups[bone_idx].append((tri.v3, 1))
    return groups
