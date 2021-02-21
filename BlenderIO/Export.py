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
from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names, shader_textures, shader_uniforms_vp_fp_from_names


class ExportDSCSBase:
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER'}
    filename_ext = ".name"

    def export_file(self, context, filepath, platform, copy_shaders=True):
        model_data = IntermediateFormat()
        export_folder = os.path.join(*os.path.split(filepath)[:-1])
        export_images_folder = os.path.join(export_folder, 'images')
        os.makedirs(export_images_folder, exist_ok=True)
        export_shaders_folder = os.path.join(export_folder, 'shaders')
        if copy_shaders:
            os.makedirs(export_shaders_folder, exist_ok=True)

        used_materials = []
        used_textures = []
        # Grab the parent object
        parent_obj = self.get_model_to_export()
        self.export_skeleton(parent_obj, model_data)
        self.export_meshes(parent_obj, model_data, used_materials)
        self.export_materials(model_data, used_materials, used_textures, export_shaders_folder)
        self.export_textures(used_textures, model_data, export_images_folder)

        model_data.unknown_data['material names'] = [material.name for material in model_data.materials]
        # Top-level unknown data
        model_data.unknown_data['unknown_cam_data_1'] = parent_obj.get('unknown_cam_data_1', [])
        model_data.unknown_data['unknown_cam_data_2'] = parent_obj.get('unknown_cam_data_2', [])
        model_data.unknown_data['unknown_footer_data'] = parent_obj.get('unknown_footer_data', b'')
        generate_files_from_intermediate_format(filepath, model_data, platform)

    def get_model_to_export(self):
        try:
            parent_obj = bpy.context.selected_objects[0]

            sel_obj = None
            while parent_obj is not None:
                sel_obj = parent_obj
                parent_obj = sel_obj.parent
            parent_obj = sel_obj
            return parent_obj
        except Exception as e:
            raise Exception("No object selected. Ensure you have selected some part of the model you wish to export in "
                            "Object Mode before attempting to export.") from e

    def export_skeleton(self, parent_obj, model_data):
        model_armature = parent_obj.children[0]
        bone_name_list = [bone.name for bone in model_armature.data.bones]
        for i, bone in enumerate(model_armature.data.bones):
            name = bone.name
            parent_bone = bone.parent
            parent_id = bone_name_list.index(parent_bone.name) if parent_bone is not None else -1

            model_data.skeleton.bone_names.append(name)
            model_data.skeleton.bone_relations.append([i, parent_id])
            model_data.skeleton.inverse_bind_pose_matrices.append(np.linalg.inv(np.array(bone.matrix_local)))

        # Get the unknown data
        model_data.skeleton.unknown_data['unknown_0x0C'] = model_armature.get('unknown_0x0C', 0)
        model_data.skeleton.unknown_data['unknown_data_1'] = model_armature.get('unknown_data_1', [])
        model_data.skeleton.unknown_data['unknown_data_2'] = model_armature.get('unknown_data_2', [])
        model_data.skeleton.unknown_data['unknown_data_3'] = model_armature.get('unknown_data_3', [])
        model_data.skeleton.unknown_data['unknown_data_4'] = model_armature.get('unknown_data_4', [])

    def export_meshes(self, parent_obj, model_data, used_materials):
        mat_names = []
        for i, mesh_obj in enumerate(parent_obj.children[0].children):
            md = model_data.new_mesh()
            mesh = mesh_obj.data

            link_loops = self.generate_link_loops(mesh)
            face_link_loops = self.generate_face_link_loops(mesh)
            export_verts, export_faces, vgroup_verts, vgroup_wgts = self.split_verts_by_uv(mesh_obj, link_loops, face_link_loops, model_data)

            md.vertices = export_verts
            for j, face in enumerate(export_faces):
                assert len(face) == 3, f"Polygon {j} is not a triangle."
                md.add_polygon(face)

            for group in mesh_obj.vertex_groups:
                bone_name = group.name
                bone_id = model_data.skeleton.bone_names.index(bone_name)
                md.add_vertex_group(bone_id, vgroup_verts.get(bone_id, []), vgroup_wgts.get(bone_id, []))

            matname = mesh.materials[0].name
            if matname not in mat_names:
                md.material_id = len(used_materials)
                used_materials.append(mesh.materials[0])
            else:
                md.material_id = mat_names.index(matname)

            md.unknown_data['unknown_0x31'] = mesh_obj.get('unknown_0x31', 1)
            md.unknown_data['unknown_0x34'] = mesh_obj.get('unknown_0x34', 0)
            md.unknown_data['unknown_0x36'] = mesh_obj.get('unknown_0x36', 0)
            md.unknown_data['unknown_0x4C'] = mesh_obj.get('unknown_0x4C', 0)

    def generate_link_loops(self, mesh):
        link_loops = {}
        for loop in mesh.loops:
            if loop.vertex_index not in link_loops:
                link_loops[loop.vertex_index] = []
            link_loops[loop.vertex_index].append(loop.index)
        return link_loops

    def generate_face_link_loops(self, mesh):
        face_link_loops = {}
        for face in mesh.polygons:
            for loop_idx in face.loop_indices:
                face_link_loops[loop_idx] = face.index
        return face_link_loops

    def split_verts_by_uv(self, mesh_obj, link_loops, face_link_loops, model_data):
        mesh = mesh_obj.data
        exported_vertices = []
        vgroup_verts = {}
        vgroup_wgts = {}
        faces = [{l: mesh.loops[l].vertex_index for l in f.loop_indices} for f in mesh.polygons]

        if 'UV3Map' in mesh.uv_layers:
            map_ids = ['UVMap', 'UV2Map', 'UV3Map']
        elif 'UV2Map' in mesh.uv_layers:
            map_ids = ['UVMap', 'UV2Map']
        elif 'UVMap' in mesh.uv_layers:
            map_ids = ['UVMap']
        else:
            map_ids = []
        generating_function = lambda lidx: tuple([tuple(mesh.uv_layers[map_id].data.values()[lidx].uv) for map_id in map_ids])
        for vert_idx, linked_loops in link_loops.items():
            vertex = mesh.vertices[vert_idx]
            loop_uvs = [generating_function(ll) for ll in linked_loops]
            unique_values = list(set(loop_uvs))
            for unique_value in unique_values:
                loops_with_this_value = [linked_loops[i] for i, x in enumerate(loop_uvs) if x == unique_value]

                group_bone_ids = [get_bone_id(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups]
                group_bone_ids = None if len(group_bone_ids) == 0 else group_bone_ids
                group_weights = [grp.weight for grp in vertex.groups]
                group_weights = None if len(group_weights) == 0 else group_weights

                vert = {'Position': vertex.co,
                        'Normal': vertex.normal,
                        **{key: value for key, value in zip(['UV', 'UV2', 'UV3'], unique_value)},
                        'WeightedBoneID': [grp.group for grp in vertex.groups],
                        'BoneWeight': group_weights}
                # Grab the tangents, bitangents, colours for each UV-split vertex?

                n_verts = len(exported_vertices)
                exported_vertices.append(vert)

                for l in loops_with_this_value:
                    face_idx = face_link_loops[l]
                    faces[face_idx][l] = n_verts

                if group_bone_ids is not None:
                    for group_bone_id, weight in zip(group_bone_ids, group_weights):
                        if group_bone_id not in vgroup_verts:
                            vgroup_verts[group_bone_id] = []
                            vgroup_wgts[group_bone_id] = []
                        vgroup_verts[group_bone_id].append(n_verts)
                        vgroup_wgts[group_bone_id].append(weight)

        faces = [list(face_verts.values()) for face_verts in faces]

        return exported_vertices, faces, vgroup_verts, vgroup_wgts

    def export_materials(self, model_data, used_materials, used_textures, export_shaders_folder):
        tex_names = []
        for bmat in used_materials:
            material = model_data.new_material()
            node_tree = bmat.node_tree
            material.name = bmat.name
            material.unknown_data['unknown_0x00'] = bmat.get('unknown_0x00', 0)
            material.unknown_data['unknown_0x02'] = bmat.get('unknown_0x02', 0)
            material.shader_hex = bmat.get('shader_hex',
                                           '088100c1_00880111_00000000_00058000')  # maybe use 00000000_00000000_00000000_00000000 instead
            material.unknown_data['unknown_0x16'] = bmat.get('unknown_0x16', 1)

            if 'shaders_folder' in bmat:
                for shader_filename in os.listdir(bmat['shaders_folder']):
                    if shader_filename[:35] == material.shader_hex:
                        try:
                            shutil.copy2(os.path.join(bmat['shaders_folder'], shader_filename),
                                         os.path.join(export_shaders_folder, shader_filename))
                        except shutil.SameFileError:
                            continue

            # Export Textures
            node_names = [node.name for node in node_tree.nodes]
            for nm in shader_textures:
                if nm in node_names:
                    texture = node_tree.nodes[nm].image

                    # Construct the texture index
                    texname = texture.name
                    if texname in tex_names:
                        tex_idx = tex_names.index(texname)
                    else:
                        tex_idx = len(used_textures)

                    # Construct the additional, unknown data
                    extra_data = bmat.get(nm)
                    if extra_data is None:
                        extra_data = [0, 0]
                    else:
                        extra_data = extra_data[1:]  # Chop off the texture idx

                    material.shader_uniforms[nm] = [tex_idx, *extra_data]
                    used_textures.append(node_tree.nodes[nm].image)

            # Export the material components
            for key in shader_uniforms_vp_fp_from_names.keys():
                if bmat.get(key) is not None:
                    material.shader_uniforms[key] = bmat.get(key)
            material.unknown_data['unknown_material_components'] = {}
            for key in ['160', '161', '162', '163', '164', '165', '166', '167', '168', '169', '172']:
                if bmat.get(key) is not None:
                    material.unknown_data['unknown_material_components'][key] = bmat.get(key)

    def export_textures(self, used_textures, model_data, export_images_folder):
        used_texture_names = [tex.name for tex in used_textures]
        used_texture_paths = [tex.filepath for tex in used_textures]
        for texture, texture_path in zip(used_texture_names, used_texture_paths):
            tex = model_data.new_texture()
            tex.name = texture
            try:
                shutil.copy2(texture_path,
                             os.path.join(export_images_folder, texture + ".img"))
            except shutil.SameFileError:
                continue
            except FileNotFoundError:
                print(texture_path, "not found.")
                continue
    #
    # def export_file(self, context, filepath, platform):
    #     model_data = IntermediateFormat()
    #     export_folder = os.path.join(*os.path.split(filepath)[:-1])
    #     export_shaders_folder = os.path.join(export_folder, 'shaders')
    #     os.makedirs(export_shaders_folder, exist_ok=True)
    #
    #     export_images_folder = os.path.join(export_folder, 'images')
    #     os.makedirs(export_images_folder, exist_ok=True)
    #
    #     parent_obj = bpy.context.selected_objects[0]
    #
    #     sel_obj = None
    #     while parent_obj is not None:
    #         sel_obj = parent_obj
    #         parent_obj = sel_obj.parent
    #     parent_obj = sel_obj
    #
    #     parent_obj.rotation_euler = (-np.pi / 2, 0, 0)
    #     parent_obj.select_set(True)
    #     bpy.ops.object.transform_apply(rotation=True)
    #     parent_obj.select_set(False)
    #
    #     # Rig
    #     model_armature = parent_obj.children[0]
    #     bone_name_list = [bone.name for bone in model_armature.data.bones]
    #     for i, bone in enumerate(model_armature.data.bones):
    #         name = bone.name
    #         parent_bone = bone.parent
    #         parent_id = bone_name_list.index(parent_bone.name) if parent_bone is not None else -1
    #
    #         model_data.skeleton.bone_names.append(name)
    #         model_data.skeleton.bone_relations.append([i, parent_id])
    #         model_data.skeleton.inverse_bind_pose_matrices.append(np.array(bone.matrix_local))
    #
    #     # Get the unknown data
    #     model_data.skeleton.unknown_data['unknown_0x0C'] = model_armature.get('unknown_0x0C', 0)
    #     model_data.skeleton.unknown_data['unknown_data_1'] = model_armature.get('unknown_data_1', [])
    #     model_data.skeleton.unknown_data['unknown_data_2'] = model_armature.get('unknown_data_2', [])
    #     model_data.skeleton.unknown_data['unknown_data_3'] = model_armature.get('unknown_data_3', [])
    #     model_data.skeleton.unknown_data['unknown_data_4'] = model_armature.get('unknown_data_4', [])
    #     used_materials = set()
    #
    #     # Vertices, Materials, and Textures (oh my!)
    #     for i, mesh_obj in enumerate(model_armature.children):
    #         md = model_data.new_mesh()
    #         # !??!11?!
    #         bpy.context.view_layer.objects.active = mesh_obj
    #         mesh = mesh_obj.data
    #
    #         # This is currently non-functional, backup_normals is just a dummy that gets passed around
    #         #backup_normals = [vertex.normal for vertex in mesh.vertices]
    #         backup_normals = []
    #         bpy.ops.object.mode_set(mode='EDIT')
    #         bm = bmesh.from_edit_mesh(mesh)
    #
    #         backup_normals = {bvert: normal for bvert, normal in zip(bm.verts, backup_normals)}
    #
    #         vgroup_verts = {}
    #         vgroup_wgts = {}
    #         uv_layer = bm.loops.layers.uv.active
    #         if uv_layer is not None:
    #             has_uvs = not all([uv_from_vert_first(uv_layer, bvertex) == [0., 1.] for bvertex in bm.verts])
    #         else:
    #             has_uvs = False
    #
    #         if has_uvs:
    #             split_verts_with_multiple_uvs(bm, uv_layer, backup_normals)
    #
    #         #backup_normals = [(bvert.index, backup_normals[bvert]) for bvert in backup_normals]
    #         #backup_normals = sorted(backup_normals, key=lambda x: x[0])
    #         #backup_normals = [normal_tuple[1] for normal_tuple in backup_normals]
    #
    #         # Hopefully it will update the vertices?!
    #         bpy.ops.object.mode_set(mode='OBJECT')
    #         bpy.ops.object.mode_set(mode='EDIT')
    #         bm = bmesh.from_edit_mesh(mesh)
    #         uv_layer = bm.loops.layers.uv.active
    #
    #         for j, (vertex, bvertex) in enumerate(zip(mesh.vertices, bm.verts)):
    #         #for j, vertex in enumerate(mesh.vertices):
    #             # UV help from :
    #             # https://blender.stackexchange.com/questions/49341/how-to-get-the-uv-corresponding-to-a-vertex-via-the-python-api
    #             group_bone_ids = [get_bone_id(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups]
    #             group_bone_ids = None if len(group_bone_ids) == 0 else group_bone_ids
    #             group_weights = [grp.weight for grp in vertex.groups]
    #             group_weights = None if len(group_weights) == 0 else group_weights
    #
    #             md.add_vertex(list(vertex.co),
    #                           list(vertex.normal),
    #                           uv_from_vert_first(uv_layer, bvertex) if has_uvs else None,
    #                           [grp.group for grp in vertex.groups],
    #                           group_weights)
    #             if group_bone_ids is not None:
    #                 for group_bone_id, weight in zip(group_bone_ids, group_weights):
    #                     if group_bone_id not in vgroup_verts:
    #                         vgroup_verts[group_bone_id] = []
    #                         vgroup_wgts[group_bone_id] = []
    #                     vgroup_verts[group_bone_id].append(j)
    #                     vgroup_wgts[group_bone_id].append(weight)
    #
    #         for i, polygon in enumerate(mesh.polygons):
    #             polyverts = list(polygon.vertices)
    #             assert len(polyverts) == 3, f"Polygon {i} is not a triangle."
    #             md.add_polygon(polyverts)
    #
    #         for group in mesh_obj.vertex_groups:
    #             bone_name = group.name
    #             bone_id = model_data.skeleton.bone_names.index(bone_name)
    #             md.add_vertex_group(bone_id, vgroup_verts.get(bone_id, []), vgroup_wgts.get(bone_id, []))
    #
    #         # Do the material id later...
    #         md.material_id = mesh.materials[0]
    #         used_materials.add((i, mesh.materials[0]))
    #         # Add unknown data
    #         md.unknown_data['unknown_0x31'] = mesh_obj.get('unknown_0x31', 1)
    #         md.unknown_data['unknown_0x34'] = mesh_obj.get('unknown_0x34', 0)
    #         md.unknown_data['unknown_0x36'] = mesh_obj.get('unknown_0x36', 0)
    #         md.unknown_data['unknown_0x4C'] = mesh_obj.get('unknown_0x4C', 0)
    #         #  md.unknown_data['unknown_0x50'] = mesh_obj['unknown_0x50']
    #         #  md.unknown_data['unknown_0x5C'] = mesh_obj['unknown_0x5C']
    #
    #         bpy.ops.object.mode_set(mode='OBJECT')
    #
    #         # Backup normals are currently very wrong
    #         #for vertex, normal in zip(md.vertices, backup_normals):
    #         #    vertex.normal = normal
    #
    #     bpy.context.view_layer.objects.active = parent_obj
    #
    #     used_materials = sorted(list(used_materials), key=lambda x: x[0])
    #     used_textures = []
    #     used_texture_paths = []
    #     for _, bmat in used_materials:
    #         material = model_data.new_material()
    #         node_tree = bmat.node_tree
    #         material.name = bmat.name
    #         material.unknown_data['unknown_0x00'] = bmat.get('unknown_0x00', 0)
    #         material.unknown_data['unknown_0x02'] = bmat.get('unknown_0x02', 0)
    #         material.shader_hex = bmat.get('shader_hex', '088100c1_00880111_00000000_00058000')  # maybe use 00000000_00000000_00000000_00000000 instead
    #         #  material.unknown_data['unknown_0x16'] = bmat['unknown_0x16']
    #
    #         if 'shaders_folder' in bmat:
    #             for shader_filename in os.listdir(bmat['shaders_folder']):
    #                 if shader_filename[:35] == material.shader_hex:
    #                     try:
    #                         shutil.copy2(os.path.join(bmat['shaders_folder'], shader_filename),
    #                                      os.path.join(export_shaders_folder, shader_filename))
    #                     except shutil.SameFileError:
    #                         continue
    #
    #         for key in bmat.keys():
    #             cstring_1 = 'type_1_component_'
    #             cstring_2 = 'type_2_component_'
    #             if key[:len(cstring_1)] == cstring_1:
    #                 bmat_data = list(bmat[key])
    #                 if key[len(cstring_1):] == '50':
    #                     texture_node = node_tree.nodes["Image Texture"]
    #                     bimg = texture_node.image
    #                     bimg_loc = bpy.data.images[bimg.name].filepath
    #                     used_texture_paths.append(bimg_loc)
    #                     texname = clean_texname(bimg.name)
    #                     texname, tex_ext = os.path.splitext(texname)
    #                     if tex_ext != '.dds':
    #                         print(f"WARNING: texture {texname} is not a .dds file, is {tex_ext}")
    #                     if texname not in used_textures:
    #                         material.texture_id = len(used_textures)
    #                         used_textures.append(texname)
    #                     else:
    #                         material.texture_id = used_textures.index(texname)
    #                     # This stuff should go in the to/from readwrites but w/e...
    #                     bmat_data[0] = material.texture_id
    #                 elif key[len(cstring_1):] == '72':
    #                     texture_node = node_tree.nodes["Image Texture.001"]
    #                     bimg = texture_node.image
    #                     bimg_loc = bpy.data.images[bimg.name].filepath
    #                     used_texture_paths.append(bimg_loc)
    #                     texname = clean_texname(bimg.name)
    #                     texname, tex_ext = os.path.splitext(texname)
    #                     if tex_ext != '.dds':
    #                         print(f"WARNING: texture {texname} is not a .dds file, is {tex_ext}")
    #                     if texname not in used_textures:
    #                         material.toon_texture_id = len(used_textures)
    #                         used_textures.append(texname)
    #                     else:
    #                         material.toon_texture_id = used_textures.index(texname)
    #                     # This stuff should go in the to/from readwrites but w/e...
    #                     bmat_data[0] = material.toon_texture_id
    #                 elif all(type(elem) == int for elem in bmat_data):
    #                     texname = bmat['temp_reference_textures'][bmat_data[0]]
    #                     if texname not in used_textures:
    #                         tex_id = len(used_textures)
    #                         used_textures.append(texname)
    #                     else:
    #                         tex_id = used_textures.index(texname)
    #                     # This stuff should go in the to/from readwrites but w/e...
    #                     bmat_data[0] = tex_id
    #                 elif key[len(cstring_1):] == '56':
    #                     bsdf_node = node_tree.nodes["Principled BSDF"]
    #                     bmat_data[0] = bsdf_node.inputs['Specular'].default_value
    #                 material.unknown_data[key] = bmat_data
    #             elif key[:len(cstring_2)] == cstring_2:
    #                 if key[:-2] not in material.unknown_data:
    #                     material.unknown_data[key[:-2]] = []
    #                 material.unknown_data[key[:-2]].append(bmat[key])
    #
    #
    #     # Now get the material ids after all used material have been parsed
    #     used_materials = [um[1] for um in used_materials]
    #     for md in model_data.meshes:
    #         md.material_id = used_materials.index(md.material_id)
    #
    #     for texture, texture_path in zip(used_textures, used_texture_paths):
    #         tex = model_data.new_texture()
    #         tex.name = texture
    #         try:
    #             shutil.copy2(texture_path,
    #                          os.path.join(export_images_folder, texture + ".img"))
    #         except shutil.SameFileError:
    #             continue
    #         except FileNotFoundError:
    #             print(texture_path, "not found.")
    #             continue
    #
    #     model_data.unknown_data['material names'] = [material.name for material in model_data.materials]
    #     # Top-level unknown data
    #     model_data.unknown_data['unknown_cam_data_1'] = parent_obj.get('unknown_cam_data_1', [])
    #     model_data.unknown_data['unknown_cam_data_2'] = parent_obj.get('unknown_cam_data_2', [])
    #     model_data.unknown_data['unknown_footer_data'] = parent_obj.get('unknown_footer_data', b'')
    #     generate_files_from_intermediate_format(filepath, model_data, platform)
    #
    #     parent_obj.rotation_euler = (np.pi / 2, 0, 0)
    #     parent_obj.select_set(True)
    #     bpy.ops.object.transform_apply(rotation=True)
    #     parent_obj.select_set(False)

    def execute_func(self, context, filepath, platform):
        filepath, file_extension = os.path.splitext(filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.export_file(context, filepath, platform)

        return {'FINISHED'}


class ExportDSCSPC(ExportDSCSBase, bpy.types.Operator, ExportHelper):
    bl_idname = 'export_file.export_dscs_pc'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PC')


class ExportDSCSPS4(ExportDSCSBase, bpy.types.Operator, ExportHelper):
    bl_idname = 'export_file.export_dscs_ps4'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PS4')

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
        #normal = backup_normals[vert_to_split]
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
