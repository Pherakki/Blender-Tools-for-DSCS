import bpy
import bmesh
from collections import Counter
import numpy as np
import itertools
import os
import shutil
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty
from bpy_extras.image_utils import load_image
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from ..CollatedData.ToReadWrites import generate_files_from_intermediate_format
from ..CollatedData.IntermediateFormat import IntermediateFormat
from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names, shader_textures, shader_uniforms_vp_fp_from_names
from ..Utilities.Interpolation import lerp


class ExportDSCSBase:
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER'}
    filename_ext = ".name"

    export_anims: BoolProperty(
        name="Export Animations",
        description="Enable/disable to export/not export animations.",
        default=True)

    def export_file(self, context, filepath, platform, copy_shaders=True):
        # Grab the parent object
        parent_obj = self.get_model_to_export()
        assert parent_obj.mode == 'OBJECT', f"Current mode is {parent_obj.mode}; ensure that Object Mode is selected before attempting to export."
        validate_blender_data(parent_obj)

        model_data = IntermediateFormat()
        export_folder = os.path.join(*os.path.split(filepath)[:-1])
        export_images_folder = os.path.join(export_folder, 'images')
        os.makedirs(export_images_folder, exist_ok=True)
        export_shaders_folder = os.path.join(export_folder, 'shaders')
        if copy_shaders:
            os.makedirs(export_shaders_folder, exist_ok=True)

        used_materials = []
        used_textures = []
        self.export_skeleton(parent_obj, model_data)
        self.export_meshes(parent_obj, model_data, used_materials)
        self.export_materials(model_data, used_materials, used_textures, export_shaders_folder)
        self.export_textures(used_textures, model_data, export_images_folder)
        if self.export_anims:
            self.export_animations(parent_obj.children[0], model_data)

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
        model_data.skeleton.unknown_data['unknown_data_2'] = model_armature.get('unknown_data_2', [0, 0]*len(bone_name_list))
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

            for group in get_all_nonempty_vertex_groups(mesh_obj):
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
        has_uvs = len(mesh.uv_layers) > 0
        if has_uvs:
            mesh.calc_tangents()
        exported_vertices = []
        vgroup_verts = {}
        vgroup_wgts = {}
        faces = [{l: mesh.loops[l].vertex_index for l in f.loop_indices} for f in mesh.polygons]
        group_map = {g.index: i for i, g in enumerate(get_all_nonempty_vertex_groups(mesh_obj))}

        if 'UV3Map' in mesh.uv_layers:
            map_ids = ['UVMap', 'UV2Map', 'UV3Map']
        elif 'UV2Map' in mesh.uv_layers:
            map_ids = ['UVMap', 'UV2Map']
        elif 'UVMap' in mesh.uv_layers:
            map_ids = ['UVMap']
        else:
            map_ids = []
        colour_map = []
        if 'Map' in mesh.vertex_colors:
            colour_map = ['Map']
        n_uvs = len(map_ids)
        n_colours = len(colour_map)

        def generating_function(lidx):
            uvs = [tuple(mesh.uv_layers[map_id].data.values()[lidx].uv) for map_id in map_ids]
            colour = [tuple((mesh.vertex_colors[map_id].data.values()[lidx].color)) for map_id in colour_map]

            return tuple([*uvs, *colour])

        for vert_idx, linked_loops in link_loops.items():
            vertex = mesh.vertices[vert_idx]
            loop_datas = [generating_function(ll) for ll in linked_loops]
            unique_values = list(set(loop_datas))
            for unique_value in unique_values:
                loops_with_this_value = [linked_loops[i] for i, x in enumerate(loop_datas) if x == unique_value]
                loop_objs_with_this_value = [mesh.loops[lidx] for lidx in loops_with_this_value]
                group_bone_ids = [get_bone_id(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups]
                group_bone_ids = None if len(group_bone_ids) == 0 else group_bone_ids
                group_weights = [grp.weight for grp in vertex.groups]
                group_weights = None if len(group_weights) == 0 else group_weights

                if has_uvs:
                    tangents = [l.tangent for l in loop_objs_with_this_value]
                    normals = [l.normal for l in loop_objs_with_this_value]
                    signs = [l.bitangent_sign  for l in loop_objs_with_this_value]
                    if not all([sign == signs[0] for sign in signs]):
                        print("!!!! WARNING !!!!")
                        print("Not all bitangents of loops attached to an exported vertex have the same sign!!!")
                    avg_tangent = np.mean(tangents, axis=0)
                    avg_normal = np.mean(normals, axis=0)
                    bitangent = signs[0]*np.cross(avg_normal, avg_tangent)
                    tangent_data = {'Tangent': (*avg_tangent, signs[0]),
                                    'Bitangent': bitangent}
                else:
                    tangent_data = {}

                vert = {'Position': vertex.co,
                        'Normal': vertex.normal,
                        **{key: value for key, value in zip(['UV', 'UV2', 'UV3'], unique_value[:n_uvs])},
                        **{key: value for key, value in zip(['Colour'], unique_value[n_uvs:])},
                        **tangent_data,
                        'WeightedBoneID': [group_map[grp.group] for grp in vertex.groups],
                        'BoneWeight': group_weights}

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

            if 'ToonTextureID' not in node_names and 'DiffuseTextureID' in node_names:
                texname = 'pc001ah01s'
                if texname in tex_names:
                    tex_idx = tex_names.index(texname)
                else:
                    tex_idx = len(used_textures)
                material.shader_uniforms['ToonTextureID'] = [tex_idx, 0, 0]
                used_textures.append(DummyTexture(texname))
            if 'DiffuseColour' not in node_names:
                material.shader_uniforms['DiffuseColour'] = [1., 1., 1., 1.]

            # Export the material components
            for key in shader_uniforms_vp_fp_from_names.keys():
                if bmat.get(key) is not None:
                    material.shader_uniforms[key] = bmat.get(key)
            material.unknown_data['unknown_material_components'] = {}
            for key in ['160', '161', '162', '163', '164', '166', '167', '168', '169', '172']:
                if bmat.get(key) is not None:
                    material.unknown_data['unknown_material_components'][int(key)] = bmat.get(key)

    def export_textures(self, used_textures, model_data, export_images_folder):
        used_texture_names = [tex.name for tex in used_textures]
        used_texture_paths = [tex.filepath for tex in used_textures]
        for texture, texture_path in zip(used_texture_names, used_texture_paths):
            tex = model_data.new_texture()
            tex.name = os.path.splitext(texture)[0]
            if texture_path is not None:
                try:
                    shutil.copy2(texture_path,
                                 os.path.join(export_images_folder, texture))
                except shutil.SameFileError:
                    continue
                except FileNotFoundError:
                    print(texture_path, "not found.")
                    continue

    def export_animations(self, armature, model_data):
        for nla_track in armature.animation_data.nla_tracks:
            animation_data = {'location': {},
                              'rotation_quaternion': {},
                              'scale': {}}
            strips = nla_track.strips
            if len(strips) != 1:
                print(f"NLA track \'{nla_track.name}\' has {len(strips)} strips; will not export if != 1.")
                continue
            nla_strip = strips[0]
            fps = nla_strip.scale * 24

            action = nla_strip.action
            for group in action.groups:
                bone_name = group.name

                curve_defaults = {'location': [0., 0., 0.],
                                  'rotation_quaternion': [1., 0., 0., 0.],
                                  'scale': [1., 1., 1.]}

                # Get whether any of the locations, rotations, and scales are animated; plus the f-curves for those
                # that are
                elements_used, bone_data = get_used_animation_elements(group)
                # For each set that is animated, interpolate missing keyframes for each component of the relevant vector
                # on each keyframe where at least one element is used
                for curve_type, isUsed in elements_used.items():
                    if isUsed:
                        curve_data = interpolate_missing_frame_elements(bone_data[curve_type], curve_defaults[curve_type])
                        zipped_data = zip_vector_elements(curve_data)
                        animation_data[curve_type][bone_name] = zipped_data

            ad = model_data.new_anim(nla_track.name)
            ad.playback_rate = fps
            for bone_name, data in animation_data['rotation_quaternion'].items():
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                ad.add_rotation_fcurve(bone_idx, list(data.keys()), list(data.values()))
            for bone_name, data in animation_data['location'].items():
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                ad.add_location_fcurve(bone_idx, list(data.keys()), list(data.values()))
            for bone_name, data in animation_data['scale'].items():
                bone_idx = model_data.skeleton.bone_names.index(bone_name)
                ad.add_scale_fcurve(bone_idx, list(data.keys()), list(data.values()))

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


def get_used_animation_elements(group):
    elements_used = {'location': False,
                     'rotation_quaternion': False,
                     'scale': False}

    bone_data = {'location': {0: {}, 1: {}, 2: {}},
                 'rotation_quaternion': {0: {}, 1: {}, 2: {}, 3: {}},
                 'scale': {0: {}, 1: {}, 2: {}}}
    for f_curve in group.channels:
        curve_type = f_curve.data_path.split('.')[-1]
        curve_idx = f_curve.array_index
        elements_used[curve_type] = True
        bone_data[curve_type][curve_idx] = {k: v for k, v in [kfp.co for kfp in f_curve.keyframe_points]}

    return elements_used, bone_data


def get_all_required_frames(curve_data):
    res = set()
    for dct in curve_data.values():
        for key in tuple(dct.keys()):
            res.add(int(key))
    return sorted(list(res))


def produce_interpolation_method(component_frame_idxs, framedata, default_value):
    if len(component_frame_idxs) == 0:
        def interp_method(input_frame_idx):
            return default_value
    elif len(component_frame_idxs) == 1:
        value = framedata[component_frame_idxs[0]]

        def interp_method(input_frame_idx):
            return value
    else:
        def interp_method(input_frame_idx):
            next_smallest_element = max([idx for idx in component_frame_idxs if idx < input_frame_idx])
            next_largest_element = min([idx for idx in component_frame_idxs if idx > input_frame_idx])

            min_value = framedata[next_smallest_element]
            max_value = framedata[next_largest_element]

            t = (input_frame_idx - min_value) / (max_value - min_value)

            # Should change lerp to the proper interpolation method
            return lerp(min_value, max_value, t)

    return interp_method


def interpolate_missing_frame_elements(curve_data, default_values):
    all_frame_idxs = get_all_required_frames(curve_data)
    for (component_idx, framedata), default_value in zip(curve_data.items(), default_values):
        component_frame_idxs = list(framedata.keys())

        # Need to pass interp_method_name in here and link to some implementation of all the interpolation methods
        # Blender provides
        interp_method = produce_interpolation_method(component_frame_idxs, framedata, default_value)
        new_framedata = {}
        for frame_idx in all_frame_idxs:
            if frame_idx not in component_frame_idxs:
                new_framedata[frame_idx] = interp_method(frame_idx)
            else:
                new_framedata[frame_idx] = framedata[frame_idx]

        curve_data[component_idx] = new_framedata

    return curve_data


def zip_vector_elements(curve_data):
    new_curve_data = {}
    elements = list(curve_data.values())
    for frame_idxs in zip(*[list(e.keys()) for e in elements]):
        for frame_idx in frame_idxs:
            assert frame_idx == frame_idxs[0]
        frame_idx = frame_idxs[0]
        new_curve_data[frame_idx] = np.array([e[frame_idx] for e in elements])
    return new_curve_data


def get_bone_id(mesh_obj, bone_names, grp):
    group_idx = grp.group
    bone_name = mesh_obj.vertex_groups[group_idx].name
    bone_id = bone_names.index(bone_name)
    return bone_id


class DummyTexture:
    def __init__(self, name):
        self.name = name
        self.filepath = None


def get_all_nonempty_vertex_groups(mesh_obj):
    nonempty_vgs = set()
    for vertex in mesh_obj.data.vertices:
        for group in vertex.groups:
            nonempty_vgs.add(group.group)
    nonempty_vgs = sorted(list(nonempty_vgs))
    nonempty_vgs = [mesh_obj.vertex_groups[idx] for idx in nonempty_vgs]

    return nonempty_vgs


def validate_blender_data(parent_obj):
    armature = parent_obj.children[0]
    meshes = armature.children
    check_vertex_group_counts(meshes)
    check_vertex_weight_counts(meshes)


def check_vertex_group_counts(mesh_objs):
    bad_meshes = []
    for mesh_obj in mesh_objs:
        if len(get_all_nonempty_vertex_groups(mesh_obj)) > 56:
            bad_meshes.append(mesh_obj)
    if len(bad_meshes):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in bad_meshes:
            mesh.select = True
        to_print = []
        for i, mesh_obj in enumerate(bad_meshes):
            nonempties = get_all_nonempty_vertex_groups(mesh_obj)
            empty_vgs = [vg.name for vg in mesh_obj.vertex_groups if vg not in nonempties]
            printline = f"{i+1}) {mesh_obj.name}"
            printline += f", {len(mesh_obj.vertex_groups)} vertex groups, {len(nonempties)} non-empty vertex groups.\n"
            printline += "Empty vertex groups that can be safely removed are:\n"
            printline += '\n'.join(['    ' + vg for vg in empty_vgs])
            printline += '\n'
            to_print.append(printline)
        to_print = '\n'.join(to_print)
        raise Exception(f"The following meshes have more than 56 vertex groups with at least 1 vertex:\n"
                        f"{to_print}\n"
                        f"These meshes have been selected for you.\n"
                        f"Reduce the number of vertex groups in these meshes by dividing the mesh such that some "
                        f"vertex groups are unused by one of the two resulting meshes.")


def check_vertex_weight_counts(mesh_objs):
    bad_meshes = []
    all_bad_vertices = []
    for mesh_obj in mesh_objs:
        bad_vertices = []
        for vertex in mesh_obj.data.vertices:
            if len(vertex.groups) > 4:
                bad_vertices.append(vertex)
        if len(bad_vertices):
            bad_meshes.append(mesh_obj)
            all_bad_vertices.append(bad_vertices)

    if len(bad_meshes):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        bad_meshes[0].select = True
        bad_vertex_counts = [len(bvs) for bvs in all_bad_vertices]
        for bv in all_bad_vertices[0]:
            bv.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        newline = '\n'
        raise Exception(f"The following meshes have vertices included in more than 4 vertex groups:\n"
                        f"{newline.join([f'{mesh.name} ({bvc} bad vertices)' for mesh, bvc in zip(bad_meshes, bad_vertex_counts)])}\n"
                        f"The vertices for the mesh \"{bad_meshes[0].name}\" have been selected for you.\n"
                        f"Reduce the number of vertex groups these vertices are part of to 4 or less.\n"
                        f"You can do this per-vertex via the 'Items' panel of the pop-out menu near the top-right of the 3D viewport.")