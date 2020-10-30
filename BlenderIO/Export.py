import bpy
import bmesh
from collections import Counter
import numpy as np
import itertools
import os
import shutil
from bpy_extras.io_utils import ExportHelper
from bpy_extras.image_utils import load_image
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from ..CollatedData.ToReadWrites import generate_files_from_intermediate_format
from ..CollatedData.IntermediateFormat import IntermediateFormat
import struct


class ExportDSCS(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_file.export_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER'}
    filename_ext = ".name"

    def export_file(self, context, filepath):
        model_data = IntermediateFormat()
        export_folder = os.path.join(*os.path.split(filepath)[:-1])
        export_shaders_folder = os.path.join(export_folder, 'shaders')
        os.makedirs(export_shaders_folder, exist_ok=True)

        parent_obj = bpy.context.selected_objects[0]
        sel_obj = None
        while parent_obj is not None:
            sel_obj = parent_obj
            parent_obj = sel_obj.parent
        parent_obj = sel_obj
        # Rig
        model_armature = parent_obj.children[0]
        bone_name_list = [bone.name for bone in model_armature.data.bones]
        for i, bone in enumerate(model_armature.data.bones):
            name = bone.name
            pos = bone.head_local
            parent_bone = bone.parent
            parent_id = bone_name_list.index(parent_bone.name) if parent_bone is not None else -1

            model_data.skeleton.bone_names.append(name)
            model_data.skeleton.bone_positions.append(pos)
            model_data.skeleton.bone_relations.append([i, parent_id])
            model_data.skeleton.bone_xaxes.append(list(bone['xvecs']))
            model_data.skeleton.bone_yaxes.append(list(bone['yvecs']))
            model_data.skeleton.bone_zaxes.append(list(bone['zvecs']))

        # Get the unknown data
        model_data.skeleton.unknown_data['unknown_0x0C'] = model_armature['unknown_0x0C']
        model_data.skeleton.unknown_data['unknown_parent_child_data'] = model_armature['unknown_parent_child_data']
        model_data.skeleton.unknown_data['bone_data'] = model_armature['bone_data']
        model_data.skeleton.unknown_data['unknown_data_1'] = model_armature['unknown_data_1']
        model_data.skeleton.unknown_data['unknown_data_2'] = model_armature['unknown_data_2']
        model_data.skeleton.unknown_data['unknown_data_3'] = model_armature['unknown_data_3']
        model_data.skeleton.unknown_data['unknown_data_4'] = model_armature['unknown_data_4']
        used_materials = set()

        # Vertices, Materials, and Textures (oh my!)
        for i, mesh_obj in enumerate(model_armature.children):
            md = model_data.new_mesh()
            # !??!11?!
            bpy.context.view_layer.objects.active = mesh_obj
            mesh = mesh_obj.data

            backup_normals = [vertex.normal for vertex in mesh.vertices]

            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(mesh)

            backup_normals = {bvert: normal for bvert, normal in zip(bm.verts, backup_normals)}

            vgroup_verts = {}
            vgroup_wgts = {}
            uv_layer = bm.loops.layers.uv.active
            if uv_layer is not None:
                has_uvs = not all([uv_from_vert_first(uv_layer, bvertex) == [0., 1.] for bvertex in bm.verts])
            else:
                has_uvs = False

            if has_uvs:
                split_verts_with_multiple_uvs(bm, uv_layer, backup_normals)

            backup_normals = [(bvert.index, backup_normals[bvert]) for bvert in backup_normals]
            backup_normals = sorted(backup_normals, key=lambda x: x[0])
            backup_normals = [normal_tuple[1] for normal_tuple in backup_normals]

            # Hopefully it will update the vertices?!
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(mesh)
            uv_layer = bm.loops.layers.uv.active

            for j, (vertex, bvertex) in enumerate(zip(mesh.vertices, bm.verts)):
            #for j, vertex in enumerate(mesh.vertices):
                # UV help from :
                # https://blender.stackexchange.com/questions/49341/how-to-get-the-uv-corresponding-to-a-vertex-via-the-python-api
                group_bone_ids = [get_bone_id(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups]
                group_bone_ids = None if len(group_bone_ids) == 0 else group_bone_ids
                group_weights = [grp.weight for grp in vertex.groups]
                group_weights = None if len(group_weights) == 0 else group_weights

                md.add_vertex(list(vertex.co),
                              list(vertex.normal),
                              uv_from_vert_first(uv_layer, bvertex) if has_uvs else None,
                              [grp.group for grp in vertex.groups],
                              group_weights)
                if group_bone_ids is not None:
                    for group_bone_id, weight in zip(group_bone_ids, group_weights):
                        if group_bone_id not in vgroup_verts:
                            vgroup_verts[group_bone_id] = []
                            vgroup_wgts[group_bone_id] = []
                        vgroup_verts[group_bone_id].append(j)
                        vgroup_wgts[group_bone_id].append(weight)

            for i, polygon in enumerate(mesh.polygons):
                polyverts = list(polygon.vertices)
                assert len(polyverts) == 3, f"Polygon {i} is not a triangle."
                md.add_polygon(polyverts)

            for group in mesh_obj.vertex_groups:
                bone_name = group.name
                bone_id = model_data.skeleton.bone_names.index(bone_name)
                md.add_vertex_group(bone_id, vgroup_verts.get(bone_id, []), vgroup_wgts.get(bone_id, []))

            # Do the material id later...
            md.material_id = mesh.materials[0]
            used_materials.add((i, mesh.materials[0]))
            # Add unknown data
            md.unknown_data['unknown_0x31'] = mesh_obj['unknown_0x31']
            md.unknown_data['unknown_0x34'] = mesh_obj['unknown_0x34']
            md.unknown_data['unknown_0x36'] = mesh_obj['unknown_0x36']
            md.unknown_data['unknown_0x5A'] = mesh_obj['unknown_0x5A']
            #  md.unknown_data['unknown_0x50'] = mesh_obj['unknown_0x50']
            #  md.unknown_data['unknown_0x5C'] = mesh_obj['unknown_0x5C']

            bpy.ops.object.mode_set(mode='OBJECT')

            # Backup normals are currently very wrong
            #for vertex, normal in zip(md.vertices, backup_normals):
            #    vertex.normal = normal

        bpy.context.view_layer.objects.active = parent_obj

        used_materials = sorted(list(used_materials), key=lambda x: x[0])
        used_textures = []
        for _, bmat in used_materials:
            material = model_data.new_material()
            node_tree = bmat.node_tree
            material.name = bmat.name
            material.unknown_data['unknown_0x00'] = bmat['unknown_0x00']
            material.unknown_data['unknown_0x02'] = bmat['unknown_0x02']
            material.shader_hex = bmat['shader_hex']
            #  material.unknown_data['unknown_0x16'] = bmat['unknown_0x16']

            for shader_filename in os.listdir(bmat['shaders_folder']):
                if shader_filename[:35] == material.shader_hex:
                    try:
                        shutil.copy2(os.path.join(bmat['shaders_folder'], shader_filename),
                                     os.path.join(export_shaders_folder, shader_filename))
                    except shutil.SameFileError:
                        continue

            for key in bmat.keys():
                cstring_1 = 'type_1_component_'
                cstring_2 = 'type_2_component_'
                if key[:len(cstring_1)] == cstring_1:
                    bmat_data = list(bmat[key])
                    if key[len(cstring_1):] == '50':
                        texture_node = node_tree.nodes["Image Texture"]
                        bimg = texture_node.image
                        texname = clean_texname(bimg.name)
                        texname, tex_ext = os.path.splitext(texname)
                        if tex_ext != '.dds':
                            print(f"WARNING: texture {texname} is not a .dds file, is {tex_ext}")
                        if texname not in used_textures:
                            material.texture_id = len(used_textures)
                            used_textures.append(texname)
                        else:
                            material.texture_id = used_textures.index(texname)
                        # This stuff should go in the to/from readwrites but w/e...
                        bmat_data[0] = material.texture_id
                    elif all(type(elem) == int for elem in bmat_data):
                        texname = bmat['temp_reference_textures'][bmat_data[0]]
                        if texname not in used_textures:
                            tex_id = len(used_textures)
                            used_textures.append(texname)
                        else:
                            tex_id = used_textures.index(texname)
                        # This stuff should go in the to/from readwrites but w/e...
                        bmat_data[0] = tex_id
                    elif key[len(cstring_1):] == '56':
                        bsdf_node = node_tree.nodes["Principled BSDF"]
                        bmat_data[0] = bsdf_node.inputs['Specular'].default_value
                    material.unknown_data[key] = bmat_data
                elif key[:len(cstring_2)] == cstring_2:
                    if key[:-2] not in material.unknown_data:
                        material.unknown_data[key[:-2]] = []
                    material.unknown_data[key[:-2]].append(bmat[key])


        # Now get the material ids after all used material have been parsed
        used_materials = [um[1] for um in used_materials]
        for md in model_data.meshes:
            md.material_id = used_materials.index(md.material_id)

        for texture in used_textures:
            tex = model_data.new_texture()
            tex.name = texture

        model_data.unknown_data['material names'] = [material.name for material in model_data.materials]
        # Top-level unknown data
        model_data.unknown_data['unknown_cam_data_1'] = parent_obj['unknown_cam_data_1']
        model_data.unknown_data['unknown_cam_data_2'] = parent_obj['unknown_cam_data_2']
        model_data.unknown_data['unknown_footer_data'] = parent_obj['unknown_footer_data']
        generate_files_from_intermediate_format(filepath, model_data)

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.export_file(context, filepath)

        return {'FINISHED'}


# UV help from:
# https://blender.stackexchange.com/questions/49341/how-to-get-the-uv-corresponding-to-a-vertex-via-the-python-api
# ... and to do this without needing bmesh:
# [mesh.data.uv_layers["UVMap"].data.items()[loop][1].uv for loop in [l.index for l in mesh.data.loops if l.vertex_index == 7]]
def get_associated_uvs(uv_layer, v):
    return [tuple(l[uv_layer].uv) for l in v.link_loops]


def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return list(uv_data.uv)
    return [0., 1.]


# With help from
# https://stackoverflow.com/a/20872750
def uv_from_vert_median(uv_layer, v):
    uvs = ([tuple(l[uv_layer].uv) for l in v.link_loops])
    if len(uvs) == 0:
        return [0., 1.]
    else:
        return max(uvs, key=Counter(uvs).get)

#def uv_from_vert_first(uv_layer, v):
#    for lidx in v.link_loops:
#        uv_data = uv_layer.data.items()[lidx][1]
#        return list(uv_data.uv)
#    return [0., 1.]


def get_bone_id(mesh_obj, bone_names, grp):
    group_idx = grp.group
    bone_name = mesh_obj.vertex_groups[group_idx].name
    bone_id = bone_names.index(bone_name)
    return bone_id


def clean_texname(name):
    elems = name.split('.')
    cutoff = None
    for i, elem in enumerate(reversed(elems)):
        if len(elem) == 3 and elem.isnumeric():
            cutoff = i + 1
    if cutoff is not None:
        name = '.'.join(elems[:-cutoff])
    return name


def split_verts_with_multiple_uvs(bm, uv_layer, backup_normals):
    """
    The output format requires vertices to be output a single set of UV coordinates attached. In Blender, vertices have
    multiple UV coordinates (one per face they are part of) and so if all these coordinates are not the same, the vertex
    must be split into multiple vertices with an unique UV coordinate that is appropriate for all the faces it is
    attached to.

    This function finds all vertices with more than one unique set of UV coordinates and splits them into multiple
    vertices, each with a unique set of UVs.
    """
    verts_to_split = []
    for bvertex in bm.verts:
        uvs = get_associated_uvs(uv_layer, bvertex)
        if len(set(uvs)) > 1:
            verts_to_split.append(bvertex)

    for vert_to_split in verts_to_split:
        bm.verts.ensure_lookup_table()
        normal = backup_normals[vert_to_split]
        #  del backup_normals[vert_to_split]

        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action='DESELECT')
        vert_to_split.select_set(True)

        old_verts = list(bm.verts)
        old_verts.remove(vert_to_split)

        bpy.ops.mesh.edge_split(type='VERT')
        new_verts = [vert for vert in bm.verts if vert not in old_verts]
        bm.verts.ensure_lookup_table()
        vert_to_split.select_set(False)

        # Group and merge new verts by uv coords
        unique_uvs = [(uv_from_vert_first(uv_layer, bvert), bvert) for bvert in new_verts]
        groups = itertools.groupby(sorted(unique_uvs, key=lambda x: x[0]), key=lambda x: x[0])
        for uv, group in groups:
            # Dist is arbitrary since only verts to be merged are passed, and they have the same position...
            bmesh.ops.remove_doubles(bm, verts=[elem[1] for elem in group], dist=0.0001)

        new_verts = [vert for vert in bm.verts if vert not in old_verts]

        # Just make sure nothing has done horribly wrong...
        for bvert in new_verts:
            assert len(set(get_associated_uvs(uv_layer, bvert))) == 1
            #  backup_normals[bvert] = normal
