import bpy
import bmesh
import numpy as np
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
            model_data.skeleton.bone_xvecs.append(list(bone['xvecs']))
            model_data.skeleton.bone_yvecs.append(list(bone['yvecs']))
            model_data.skeleton.bone_zvecs.append(list(bone['zvecs']))

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
            bpy.ops.object.mode_set(mode='EDIT')
            mesh = mesh_obj.data
            bm = bmesh.from_edit_mesh(mesh)

            vgroup_verts = {}
            vgroup_wgts = {}
            uv_layer = bm.loops.layers.uv.active
            has_uvs = not all([uv_from_vert_first(uv_layer, bvertex) == [0., 1.] for bvertex in bm.verts])

            for j, (vertex, bvertex) in enumerate(zip(mesh.vertices, bm.verts)):
                # UV help from :
                # https://blender.stackexchange.com/questions/49341/how-to-get-the-uv-corresponding-to-a-vertex-via-the-python-api
                group_ids = [get_group(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups]
                group_ids = None if len(group_ids) == 0 else group_ids
                group_weights = [grp.weight for grp in vertex.groups]
                group_weights = None if len(group_weights) == 0 else group_weights

                md.add_vertex(list(vertex.co),
                              list(vertex.normal),
                              uv_from_vert_first(uv_layer, bvertex) if has_uvs else None,
                              group_ids,
                              group_weights)
                if group_ids is not None:
                    for group_id, weight in zip(group_ids, group_weights):
                        if group_id not in vgroup_verts:
                            vgroup_verts[group_id] = []
                            vgroup_wgts[group_id] = []
                        vgroup_verts[group_id].append(j)
                        vgroup_wgts[group_id].append(weight)

            for polygon in mesh.polygons:
                md.add_polygon(list(polygon.vertices))

            for bone_id in vgroup_verts:
                md.add_vertex_group(bone_id, vgroup_verts[bone_id], vgroup_wgts)

            # Do the material id later...
            md.material_id = mesh.materials[0]
            used_materials.add((i, mesh.materials[0]))
            # Add unknown data
            md.unknown_data['unknown_0x30'] = mesh_obj['unknown_0x30']
            md.unknown_data['unknown_0x31'] = mesh_obj['unknown_0x31']
            md.unknown_data['unknown_0x34'] = mesh_obj['unknown_0x34']
            md.unknown_data['unknown_0x36'] = mesh_obj['unknown_0x36']
            md.unknown_data['unknown_0x44'] = mesh_obj['unknown_0x44']
            md.unknown_data['unknown_0x50'] = mesh_obj['unknown_0x50']
            md.unknown_data['unknown_0x5C'] = mesh_obj['unknown_0x5C']
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = parent_obj

        used_materials = sorted(list(used_materials), key=lambda x: x[0])
        used_textures = []
        for _, bmat in used_materials:
            material = model_data.new_material()
            node_tree = bmat.node_tree
            material.name = bmat.name
            material.unknown_data['unknown_0x00'] = bmat['unknown_0x00']
            material.unknown_data['unknown_0x10'] = bmat['unknown_0x10']
            material.unknown_data['unknown_0x11'] = bmat['unknown_0x11']
            material.unknown_data['unknown_0x12'] = bmat['unknown_0x12']
            material.unknown_data['unknown_0x16'] = bmat['unknown_0x16']
            for key in bmat.keys():
                cstring_1 = 'type_1_component_'
                cstring_2 = 'type_2_component_'
                if key[:len(cstring_1)] == cstring_1:
                    bmat_data = list(bmat[key])
                    print(key, bmat_data)
                    if key[len(cstring_1):] == '50':
                        print("Doing the first bit")
                        texture_node = node_tree.nodes["Image Texture"]
                        bimg = texture_node.image
                        texname, _ = os.path.splitext(os.path.basename(bimg.filepath))
                        if texname not in used_textures:
                            material.texture_id = len(used_textures)
                            used_textures.append(texname)
                        else:
                            material.texture_id = used_textures.index(texname)
                        # This stuff should go in the to/from readwrites but w/e...
                        bmat_data[0] = material.texture_id
                    elif all(type(elem) == int for elem in bmat_data):
                        print("Doing the elif bit")
                        texname = bmat['temp_reference_textures'][bmat_data[0]]
                        if texname not in used_textures:
                            tex_id = len(used_textures)
                            used_textures.append(texname)
                        else:
                            tex_id = used_textures.index(texname)
                        # This stuff should go in the to/from readwrites but w/e...
                        bmat_data[0] = tex_id
                    material.unknown_data[key] = bmat_data
                elif key[:len(cstring_2)] == cstring_2:
                    material.unknown_data[key] = bmat[key]

        # Now get the material ids after all used material have been parsed
        used_materials = [um[1] for um in used_materials]
        for md in model_data.meshes:
            md.material_id = used_materials.index(md.material_id)

        for texture in used_textures:
            tex = model_data.new_texture()
            tex.name = texture

        model_data.unknown_data['material names'] = [material.name for material in model_data.materials]
        # Top-level unknown data
        model_data.unknown_data['geom_unknown_0x14'] = parent_obj['geom_unknown_0x14']
        model_data.unknown_data['geom_unknown_0x20'] = parent_obj['geom_unknown_0x20']
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
def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return list(uv_data.uv)
    return [0., 1.]


def get_group(mesh_obj, bone_names, grp):
    group_idx = grp.group
    bone_name = mesh_obj.vertex_groups[group_idx].name
    bone_id = bone_names.index(bone_name)
    return bone_id
