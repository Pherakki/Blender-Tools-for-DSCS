import bpy
import numpy as np

from ..IOHelpersLib.Objects import find_bpy_objects
from ..IOHelpersLib.Maths import convert_rotation_to_quaternion
from ...Utilities.List import natural_sort
from ...Utilities.Hash import dscs_hash_string

from ...Core.FileFormats.Phys.PhysInterface import PhysInterface


def generate_unique_name(material_names, stem):
    if stem not in material_names:
        return stem
    elif stem[:0x40-4] not in material_names:
        return stem[:0x40-4]
    else:
        new_stem = stem[:0x40-4]
        idx = 1
        while f"{new_stem}.{idx:0>3}" in material_names:
            idx += 1
        return f"{new_stem}.{idx:0>3}"
    

def make_collider_material(ni, gi, name, material_names):
    name = generate_unique_name(material_names, name)
    material_names[name] = len(material_names)
    ni.material_names.append(name)
    gi.add_material(dscs_hash_string(name), 1, [0, 0, 0, 0])
    return name


def extract_colliders(ni, gi, armature_obj, errorlog):
    def gen_mat():
        return make_collider_material(ni, gi, "ColliderMaterial", material_names)
    
    bpy_collider_objs = natural_sort(find_bpy_objects(bpy.data.objects, armature_obj, [lambda x: x.type == "MESH"]), lambda x: x.name)
    bpy_collider_objs = natural_sort([obj for obj in bpy_collider_objs if obj.data.DSCS_MeshProperties.mesh_type == "COLLIDER"], lambda x: x.name)
    
    if len(bpy_collider_objs) == 0:
        return None
    
    pi = PhysInterface()
    bone_names     = {n: i for i, n in enumerate(ni.bone_names)}
    material_names = {n: i for i, n in enumerate(ni.material_names)}
    used_mats = set()
    used_bones = set()
    for collider in bpy_collider_objs:
        props = collider.DSCS_ColliderProperties
        if props.collider_type == "BOX":
            box_props = props.box_props
            
            if collider.active_material is not None:
                mat_name = collider.active_material.name.encode("utf8")
            else:
                mat_name = gen_mat()
            
            scale_x, scale_y, scale_z = collider.scale
            pi.add_box_collider(scale_x*box_props.width/2, 
                                scale_y*box_props.depth/2, 
                                scale_z*box_props.height/2, 
                                mat_name)
            used_mats.add(mat_name)
        elif props.collider_type == "COMPLEX":
            # TODO: Need to put lots of error-checking in here...
            
            bpy_vs = collider.data.vertices
            bpy_tris = collider.data.polygons
            
            # TODO: ROTATE VERTS
            vertices = np.array([(v.co[0], v.co[2], v.co[1]) for v in bpy_vs])
            tris = []
            mat_names  = {}
            bone_names = {}
            vertex_group_idx_to_name_map = {g.index: g.name for g in collider.vertex_groups}
            for tri in bpy_tris:
                # Check if it's a tri
                if len(tri.vertices) > 3:
                    errorlog.log_error_message(f"Collider '{collider.name}' has non-triangular faces. Triangulate the mesh before exporting.")
                    break
                
                # Materials
                material_idx = tri.material_index
                
                if material_idx >= len(collider.material_slots):
                    material_name = gen_mat()
                else:
                    material_name = collider.material_slots[material_idx].name
                
                if material_name not in mat_names:
                    mat_names[material_name] = len(mat_names)
                
                # Bones
                vertex_groups = {}
                for v in tri.vertices:
                    for g in v.groups:
                        if g.group not in vertex_groups:
                            vertex_groups[g.group] = 0
                        vertex_groups[g.group] += g.weight
                
                vertex_groups = sorted(vertex_groups.items(), key=lambda x: x[1])
                if len(vertex_groups) > 1:
                    bone_name = vertex_group_idx_to_name_map[vertex_groups[0][0]]
                elif len(vertex_groups) == 0:
                    bone_name = ni.bone_names[0]
                else:
                    bone_name = vertex_group_idx_to_name_map[vertex_groups[0][0]]
                
                if bone_name not in bone_names:
                    bone_names[bone_name] = len(bone_names)
                
                collider.tris.append([*tri.vertices, mat_names[material_name], bone_names[bone_name]])
            
            for m in mat_names:
                used_mats.add(m)
            for b in bone_names:
                used_bones.add(b)
            pi.add_complex_collider(vertices, tris, list(mat_names.items()), list(bone_names.items()))
            
        else:
            errorlog.log_warning_message(f"Collider object '{collider.name}' has unknown type '{props.collider_type}' and will not be exported.")
        
        rprops = props.ragdoll_props
        quat = convert_rotation_to_quaternion(collider.rotation_quaternion, collider.rotation_euler, collider.rotation_mode)
        pi.colliders[-1].add_instance(collider.name.encode("utf8"), 
                                      list(collider.location), 
                                      [quat.x, quat.y, quat.z, quat.w],
                                      1.,
                                      list(rprops.unknown_vector),
                                      rprops.unknown_float,
                                      rprops.is_solid)
    pi.materials = sorted(used_mats)
    pi.bones     = sorted(used_bones)
    
    return pi
    