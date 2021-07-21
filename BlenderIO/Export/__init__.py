import bpy
import numpy as np
import os
import shutil
from bpy_extras.io_utils import ExportHelper
from bpy.props import EnumProperty

from ...CollatedData.ToReadWrites import generate_files_from_intermediate_format
from ...CollatedData.IntermediateFormat import IntermediateFormat
from ...FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names, shader_textures, shader_uniforms_vp_fp_from_names
from .ExportAnimation import export_animations
from ..DSCSBlenderUtils import find_selected_model

from ...Utilities.Matrices import calculate_bone_matrix_relative_to_parent, generate_transform_delta, decompose_matrix, generate_transform_matrix
from ...Utilities.ActionDataRetrieval import get_action_data


class ExportDSCS(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_file.export_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER'}
    filename_ext = ".name"

    platform: EnumProperty(
        name="Platform",
        description="Select which platform the model is for.",
        items=[("PC", "PC", "Exports a DSCS Complete Edition PC model", "", 0),
               ("PS4", "PS4 (WIP)", "Exports a DSCS pr DSHM PS4 model. Not fully tested", "", 1)])

    export_mode: EnumProperty(
        name="Export Mode",
        description="Which mode to export in.",
        items=[("Modelling", "Modelling", "Exports the model with its base animation only", "", 0),
               ("Animation", "Animation", "Exports overlay animations only", "", 1),
               ("QA", "QA", "Exports the model and all animations", "", 2)])

    def export_file(self, context, filepath):
        # Grab the parent object
        parent_obj = find_selected_model()
        assert parent_obj.mode == 'OBJECT', f"Current mode is {parent_obj.mode}; ensure that Object Mode is selected before attempting to export."
        assert parent_obj.type == 'EMPTY', f"Top-level object \"{parent_obj.name}\" is not an empty axis object."
        validate_blender_data(parent_obj)

        model_data = IntermediateFormat()
        export_folder, filename = os.path.split(filepath)

        armature = self.find_armatures(parent_obj)
        base_anim = armature.animation_data.nla_tracks[parent_obj.name]
        if self.export_mode == "Modelling" or self.export_mode == "QA":
            export_images_folder = os.path.join(export_folder, 'images')
            os.makedirs(export_images_folder, exist_ok=True)

            # Top-level unknown data
            model_data.unknown_data['unknown_cam_data_1'] = parent_obj.get('unknown_cam_data_1', [])
            model_data.unknown_data['unknown_cam_data_2'] = parent_obj.get('unknown_cam_data_2', [])
            model_data.unknown_data['unknown_footer_data'] = parent_obj.get('unknown_footer_data', b'')

            used_materials = []
            used_textures = []
            self.export_skeleton(armature, base_anim.strips[0].action, model_data)
            self.export_meshes(parent_obj, model_data, used_materials)
            self.export_materials(model_data, used_materials, used_textures)
            self.export_textures(used_textures, model_data, export_images_folder)

        # The first frame of the base animation becomes the rest pose
        # Strip out any transforms in the base animation that are only for the first frame: DSCS will get this from
        # the rest pose, allowing us to make the animation files smaller
        transforms_not_in_base = {'location': [], 'rotation_quaternion': [], 'scale': []}
        export_animations([base_anim], model_data,
                          strip_single_frame_transforms=True,
                          required_transforms={},
                          out_transforms=transforms_not_in_base)

        if self.export_mode == "Animation" or self.export_mode == "QA":
            overlay_anims = [track for track in armature.animation_data.nla_tracks if track.name != parent_obj.name]
            export_animations(overlay_anims, model_data,
                              strip_single_frame_transforms=False,
                              required_transforms={})

        # print("!!!!!!!")
        # print(os.getcwd())
        # print(__file__, os.path.dirname(__file__))
        # print("!!!!!!!")

        generate_files_from_intermediate_format(filepath, model_data, self.platform, animation_only=self.export_mode=="Animation")

    def find_armatures(self, parent_object):
        armatures = [item for item in parent_object.children if item.type == "ARMATURE"]
        if len(armatures) == 1:
            armature = armatures[0]
        elif len(armatures) > 1:
            print("!!! WARNING !!!")
            print("! More than one armature detected under the object \'{parent_object.name}\':")
            print("!", ", ".join([arm.name for arm in armatures]))
            print(f"! Using {armatures[0].name}")
            print("!!! WARNING !!!")
            armature = armatures[0]
        else:
            assert 0, f"No armature objects found under the axis object \'{parent_object.name}\'."

        return armature

    def export_skeleton(self, armature, base_animation, model_data):
        bone_name_list = [bone.name for bone in armature.data.bones]
        for i, bone in enumerate(armature.data.bones):
            name = bone.name
            parent_bone = bone.parent
            parent_id = bone_name_list.index(parent_bone.name) if parent_bone is not None else -1

            model_data.skeleton.bone_names.append(name)
            model_data.skeleton.bone_relations.append([i, parent_id])
            model_data.skeleton.inverse_bind_pose_matrices.append(np.linalg.inv(np.array(bone.matrix_local)))

        parent_bones = {c: p for c, p in model_data.skeleton.bone_relations}
        model_data.skeleton.rest_pose = extract_rest_pose_from_base_animation(model_data.skeleton.bone_names, parent_bones, base_animation,
                                                                              [np.array(bone.matrix_local) for bone in armature.data.bones])

        # Get the unknown data
        model_data.skeleton.unknown_data['unknown_0x0C'] = armature.get('unknown_0x0C', 0)
        model_data.skeleton.unknown_data['unknown_data_1'] = armature.get('unknown_data_1', [])
        model_data.skeleton.unknown_data['unknown_data_3'] = armature.get('unknown_data_3', [])
        model_data.skeleton.unknown_data['unknown_data_4'] = armature.get('unknown_data_4', [])

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
            md.name_hash = mesh_obj.get('name_hash', '00000000')

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
        can_export_tangents = has_uvs and mesh.uv_layers.get('UVMap') is not None

        # Disable buggy tangent export for now...
        can_export_tangents = False
        if can_export_tangents:
            mesh.calc_tangents(mesh.uv_layers['UVMap'])
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

                if can_export_tangents:
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
                                    'Binormal': bitangent}
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

    def export_materials(self, model_data, used_materials, used_textures):
        tex_names = []
        for bmat in used_materials:
            material = model_data.new_material()
            node_tree = bmat.node_tree
            material.name = bmat.name
            material.shader_hex = bmat.get('shader_hex',
                                           '088100c1_00880111_00000000_00058000')  # maybe use 00000000_00000000_00000000_00000000 instead
            material.enable_shadows = bmat.get('enable_shadows', 1)

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

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.export_file(context, filepath)

        return {'FINISHED'}


def extract_rest_pose_from_base_animation(bone_names, parent_bones, base_animation, bind_pose_matrices):
    curve_defaults = {'rotation_quaternion': [1., 0., 0., 0.],
                      'location': [0., 0., 0.],
                      'scale': [1., 1., 1.]}
    base_animation_data, _ = get_action_data(base_animation,
                                             curve_defaults)

    rest_pose = []
    for i, bone_name in enumerate(bone_names):
        if bone_name in base_animation_data:
            bone_data = base_animation_data[bone_name]

            # Gets the bone data for the first frame of an action, or the curve default if no frames are present
            def get_subdata(curve_type):
                return list(bone_data[curve_type].values())[0] \
                       if len(bone_data[curve_type]) \
                       else curve_defaults[curve_type]

            quat = get_subdata('rotation_quaternion')
            loc = get_subdata('location')
            scale = get_subdata('scale')

            transform_matrix = generate_transform_matrix(quat, loc, scale, WXYZ=True)
            bm = calculate_bone_matrix_relative_to_parent(i, parent_bones, bind_pose_matrices)
            # Shift from local space to model-space
            rpm = np.dot(bm, transform_matrix)
            rloc, rquat, rscale = decompose_matrix(rpm, WXYZ=False)
            rest_pose.append([rquat, [*rloc, 1.], [*rscale, 1.]])
    return rest_pose


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