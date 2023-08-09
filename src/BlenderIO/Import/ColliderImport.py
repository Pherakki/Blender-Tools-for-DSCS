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

        # Create collider mesh
        collider_name = f"{model_name}_col{i}"
        bpy_mesh = bpy.data.meshes.new(name=collider_name)
        props    = bpy_mesh.DSCS_ColliderProperties
        bpy_mesh.DSCS_MeshProperties.mesh_type = "COLLIDER"
        
        # Get geometry
        if collider.TYPE == 0:
            vertices, _, faces = make_cuboid(2*collider.half_width, 
                                             2*collider.half_height,
                                             2*collider.half_depth,
                                             [1, 1, 1])
            
            props.width  = 2*collider.half_width
            props.height = 2*collider.half_height
            props.depth  = 2*collider.half_depth
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
        bpy_mesh.use_auto_smooth = True
        for poly in bpy_mesh.polygons:
            poly.use_smooth = True
        
        
        # Create objects
        for instance in collider.instances:
            if len(collider.instances) > 1:
                raise ValueError("Unsupported operation: collider has more than one instance")
                
            bpy_mesh_object = bpy.data.objects.new(instance.name, bpy_mesh)
            collection.objects.link(bpy_mesh_object)
            
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
            

    #     # Assign materials
    #     active_material = material_list[mesh.material_id]
    #     bpy.data.objects[meshobj_name].active_material = active_material
        
    #     matname = active_material.name
    #     if matname not in meshes_using_material:
    #         meshes_using_material[matname] = VertexAttributeTracker()
    #     meshes_using_material[matname].log_mesh(bpy_mesh_object, mesh)
        
    #     set_active_obj(bpy_mesh_object)
        
    #     #################
    #     # ADD LOOP DATA #
    #     #################
    #     n_loops = len(bpy_mesh.loops)
    #     map_of_loops_to_model_verts = mesh_info.map_of_loops_to_model_verts
    #     loop_data = [mesh.vertices[map_of_loops_to_model_verts[loop_idx]] for loop_idx in range(n_loops)]

    #     # Assign UVs
    #     for uv_idx, uv_type in enumerate([AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3]):
    #         if mesh.vertices[0][uv_type] is not None:
    #             create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type][0], (l[uv_type][1]*-1) + 1) for l in loop_data))

    #     # Assign vertex colours
    #     if mesh.vertices[0][AttributeTypes.COLOR] is not None:
    #         if hasattr(bpy_mesh, "color_attributes"):
    #             colour_map = bpy_mesh.color_attributes.new(name="Map", domain="CORNER", type="FLOAT_COLOR")
    #             for loop_idx, loop in enumerate(bpy_mesh.loops):
    #                 colour_map.data[loop_idx].color = loop_data[loop_idx].color
    #         else:    
    #             colour_map = bpy_mesh.vertex_colors.new(name="Map", do_init=True)
    #             for loop_idx, loop in enumerate(bpy_mesh.loops):
    #                 colour_map.data[loop_idx].color = int(loop_data[loop_idx].color*255)

    #     ###########
    #     # RIGGING #
    #     ###########
    #     vertex_groups = make_vertex_groups(mesh_info.vertices)
    #     for bone_idx, vg in vertex_groups.items():
    #         vertex_group = bpy_mesh_object.vertex_groups.new(name=ni.bone_names[bone_idx])
    #         for vert_idx, vert_weight in vg:
    #             vertex_group.add([vert_idx], vert_weight, 'REPLACE')

    #     #################
    #     # ADD MISC DATA #
    #     #################
    #     # Load the hashed mesh name
    #     signed_hash = struct.unpack('i', struct.pack('I', mesh.name_hash))[0]
    #     bpy_mesh_object.data.DSCS_MeshProperties.name_hash = signed_hash

    #     # Set armature constraint
    #     bpy_mesh_object.parent = armature
    #     modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
    #     modifier.object = armature

    #     # Assign normals
    #     # Do this LAST because it can remove some loops
    #     if mesh.vertices[0][AttributeTypes.NORMAL] is not None:
    #         import_loop_normals(bpy_mesh, (l.normal for l in loop_data))

    #     # Tell Blender what we've done
    #     bpy_mesh.validate(verbose=True, clean_customdata=False)
    #     bpy_mesh.update()
    #     bpy_mesh.update()

    #     # Convert meshes Y up -> Z up
    #     bpy_mesh.transform(Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4())

    #     meshes.append(bpy_mesh)

    # set_material_vertex_attributes(meshes_using_material, errorlog)


def make_vertex_groups(blender_vert_infos):
    groups = {}
    for vert_idx, vert in enumerate(blender_vert_infos):
        for bone_idx, weight in zip(vert.indices, vert.weights):
            if weight == 0.:
                continue
            elif bone_idx not in groups:
                groups[bone_idx] = []
            groups[bone_idx].append((vert_idx, weight))
    return groups
