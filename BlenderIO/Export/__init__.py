import array
import copy
import numpy as np
import os
import shutil

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, EnumProperty, FloatProperty

from ...CollatedData.ToReadWrites import generate_files_from_intermediate_format
from ...CollatedData.IntermediateFormat import IntermediateFormat, MaterialData
from ...FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names, shader_textures, shader_uniforms_vp_fp_from_names
from .ExportAnimation import export_animations, create_blank_anim
from ..DSCSBlenderUtils import find_selected_model

from ...Utilities.Matrices import calculate_bone_matrix_relative_to_parent, generate_transform_delta, decompose_matrix, generate_transform_matrix
from ...Utilities.ActionDataRetrieval import get_action_data
from ...Utilities.StringHashing import dscs_name_hash
from ...Utilities.OpenGLResources import id_to_glfunc, glBool_options, glEnable_options, glBlendFunc_options, glBlendEquationSeparate_options, glCullFace_options, glComparison_options
from ...Utilities.Lists import flip_dict, natural_sort

from ...Utilities.Paths import normalise_abs_path


class ExportMediaVision(bpy.types.Operator):
    bl_options = {'REGISTER'}
    filename_ext = ".name"

    platform: None
    export_anims: None
    img_to_dds: None
    flip_uvs: None
    vweights_adjust: None
    vweight_floor: None
    export_anim_mode = None
    generate_physics = None

    def export_file(self, context, filepath):
        # Grab the parent object
        parent_obj = find_selected_model()
        assert parent_obj.mode == 'OBJECT', f"Current mode is {parent_obj.mode}; ensure that Object Mode is selected before attempting to export."
        assert parent_obj.type == 'EMPTY', f"Top-level object \"{parent_obj.name}\" is not an empty axis object."
        armature, meshes = validate_blender_data(parent_obj)

        model_data = IntermediateFormat()
        export_folder, filename = os.path.split(filepath)

        base_anim = armature.animation_data.nla_tracks.get("base", None)
        #if self.export_mode == "Modelling" or self.export_mode == "QA":
        export_images_folder = os.path.join(export_folder, 'images')
        os.makedirs(export_images_folder, exist_ok=True)

        # Top-level unknown data
        model_data.unknown_data['unknown_cam_data_1'] = parent_obj.get('unknown_cam_data_1', [])
        model_data.unknown_data['unknown_cam_data_2'] = parent_obj.get('unknown_cam_data_2', [])
        model_data.unknown_data['unknown_footer_data'] = parent_obj.get('unknown_footer_data', b'')

        used_materials = []
        used_textures = []
        self.export_skeleton(armature, None if base_anim is None else base_anim.strips[0].action, model_data)
        self.export_meshes(meshes, model_data, used_materials)
        self.export_materials(model_data, used_materials, used_textures)
        self.export_textures(used_textures, model_data, export_images_folder)
        self.export_cameras(find_cameras(parent_obj), model_data)
        self.export_lights(find_lights(parent_obj), model_data)

        # The first frame of the base animation becomes the rest pose
        # Strip out any transforms in the base animation that are only for the first frame: DSCS will get this from
        # the rest pose, allowing us to make the animation files smaller
        if base_anim is None:
            create_blank_anim(model_data, filename)
        else:
            transforms_not_in_base = {'location': [], 'rotation_quaternion': [], 'scale': []}
            export_animations([base_anim], model_data, filename,
                              strip_single_frame_transforms=True,
                              required_transforms={},
                              out_transforms=transforms_not_in_base,
                              interp_mode=self.export_anim_mode)

        if self.export_anims:
            overlay_anims = [track for track in armature.animation_data.nla_tracks if track.name != "base"]
            export_animations(overlay_anims, model_data, filename,
                              strip_single_frame_transforms=False,
                              required_transforms={},
                              interp_mode=self.export_anim_mode)

        self.clean_up_model(model_data)
        generate_files_from_intermediate_format(filepath, model_data, filename, self.platform,
                                                animation_only=False,#self.export_mode=="Animation",
                                                create_physics=self.generate_physics)

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
        if base_animation is None:
            model_data.skeleton.rest_pose = matrices_to_rest_pose(model_data.skeleton.bone_names, parent_bones, [np.array(bone.matrix_local) for bone in armature.data.bones])
        else:
            model_data.skeleton.rest_pose = extract_rest_pose_from_base_animation(model_data.skeleton.bone_names, parent_bones, base_animation,
                                                                                  [np.array(bone.matrix_local) for bone in armature.data.bones])
        # Get the unknown data
        model_data.skeleton.unknown_data['unknown_0x0C'] = armature.get('unknown_0x0C', 0)
        model_data.skeleton.unknown_data['unknown_data_1'] = armature.get('unknown_data_1', [])
        model_data.skeleton.unknown_data['unknown_data_3'] = armature.get('unknown_data_3', [])
        model_data.skeleton.unknown_data['unknown_data_4'] = armature.get('unknown_data_4', [])

    def export_meshes(self, meshes, model_data, used_materials):
        mat_names = []
        force_recalc_normals = self.recalc_normal_mode == 1
        force_not_recalc_normals = self.recalc_normal_mode == 2

        # Natural sort meshes by name so they're exported in the same order as the outliner
        sorted_meshes = natural_sort(meshes, accessor=lambda x: x.name)
        for i, mesh_obj in enumerate(sorted_meshes):
            md = model_data.new_mesh()
            mesh = mesh_obj.data

            # Deal with any zero vectors
            zero_vec = (0., 0., 0.)
            loop_normals = [l.normal for l in mesh.loops]
            lnorms_zero = [tuple(normal) == zero_vec for normal in loop_normals]
            if (not mesh.has_custom_normals or any(lnorms_zero) or force_recalc_normals) and not force_not_recalc_normals:
                print(f"Recalculating normals on mesh {i}...")
                if not mesh.has_custom_normals:
                    mesh.create_normals_split()
                mesh.calc_normals_split()
                res = []
                for j, iszero in enumerate(lnorms_zero):
                    res.append(mesh.loops[j].normal if iszero else loop_normals[j])
                mesh.normals_split_custom_set(res)
                print(f"Done.")

            link_loops = self.generate_link_loops(mesh)
            face_link_loops = self.generate_face_link_loops(mesh)
            export_verts, export_faces, vgroup_verts, vgroup_wgts = self.split_verts_by_loop_data(mesh_obj, link_loops, face_link_loops, model_data, self.vweight_floor)
            if self.flip_uvs:
                for key in ['UV', 'UV2', 'UV3']:
                    if key in export_verts[0]:
                        for vert in export_verts:
                            u, v = vert[key]
                            vert[key] = (u, 1. - v)

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
                mat_names.append(matname)
            else:
                md.material_id = mat_names.index(matname)

            md.unknown_data['meshflags'] = 1  # Support this later... # mesh_obj.get('unknown_0x31', 1)
            md.name_hash = mesh_obj.get('name_hash', dscs_name_hash(mesh_obj.name))

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

    def fetch_data(self, obj, element, sigfigs):
        dsize = len(getattr(obj[0], element))
        data = array.array('f', [0.0] * (len(obj) * dsize))
        obj.foreach_get(element, data)
        return [tuple(round_to_sigfigs(datum, sigfigs)) for datum in zip(*(iter(data),) * dsize)]

    def fetch_tangent(self, obj, sigfigs):
        dsize = len(getattr(obj[0], "tangent"))
        data = array.array('f', [0.0] * (len(obj) * dsize))
        obj.foreach_get("tangent", data)

        signs = array.array('f', [0.0] * (len(obj)))
        obj.foreach_get("bitangent_sign", data)
        return [(*round_to_sigfigs(datum, sigfigs), sign) for datum, sign in zip(zip(*(iter(data),) * dsize), signs)]

    def split_verts_by_loop_data(self, mesh_obj, link_loops, face_link_loops, model_data, vweight_floor):
        print(">>> Splitting", mesh_obj)
        mesh = mesh_obj.data
        has_uvs = len(mesh.uv_layers) > 0

        exported_vertices = []
        vgroup_verts = {}
        vgroup_wgts = {}
        faces = [{l: mesh.loops[l].vertex_index for l in f.loop_indices} for f in mesh.polygons]
        group_map = {g.index: i for i, g in enumerate(get_all_nonempty_vertex_groups(mesh_obj))}

        map_ids = list(mesh.uv_layers.keys())[:3]
        colour_map = list(mesh.vertex_colors.keys())[:1]
        n_uvs = len(map_ids)
        n_colours = len(colour_map)

        use_normals = mesh_obj.get("export_normals", True)
        use_tangents = mesh_obj.get("export_tangents", False)
        use_binormals = mesh_obj.get("export_binormals", False)
        map_name = map_ids[0] if len(map_ids) else 'dummy'
        can_export_tangents = has_uvs and mesh.uv_layers.get(map_name) is not None and (use_normals and (use_tangents or use_binormals))

        if can_export_tangents:
            mesh.calc_tangents(uvmap=map_name)

        sigfigs = 4
        nloops = len(mesh.loops)

        # Extract normals
        if use_normals:
            normals = [(elem,) for elem in self.fetch_data(mesh.loops, "normal", sigfigs)]
        else:
            normals = [tuple()]*nloops

        # Extract UVs
        UV_data = [None]*n_uvs
        for i, map_id in enumerate(map_ids):
            UV_data[i] = self.fetch_data(mesh.uv_layers[map_id].data, "uv", sigfigs+2)
        if len(UV_data):
            UV_data = [tuple(elems) for elems in zip(*UV_data)]
        else:
            UV_data = [tuple()]*nloops

        # Extract colours
        col_data = [None]*n_colours
        for i, map_id in enumerate(colour_map):
            col_data[i] = self.fetch_data(mesh.vertex_colors[map_id].data, "color", sigfigs)
        if len(col_data):
            col_data = [tuple(elems) for elems in zip(*col_data)]
        else:
            col_data = [tuple()]*nloops

        # Extract tangents
        if can_export_tangents:
            tangents = [(elem,) for elem in self.fetch_tangent(mesh.loops, sigfigs)]
        else:
            tangents = [tuple()]*nloops

        # Calculate binormals
        if use_binormals and can_export_tangents:
            bitangents = [(tuple(round_to_sigfigs(tangent[0][3] * np.cross(normal, tangent[0][:3]), sigfigs)),) for normal, tangent in zip(normals, tangents)]
        else:
            bitangents = [tuple()]*nloops

        # Make loop -> unique value lookup maps
        loop_idx_to_key = [key for key in (zip(normals, UV_data, col_data, tangents, bitangents))]
        unique_val_map = {key: i for i, key in enumerate(list(set(loop_idx_to_key)))}
        loop_idx_to_unique_key = {i: unique_val_map[key] for i, key in enumerate(loop_idx_to_key)}

        for vert_idx, linked_loops in link_loops.items():
            vertex = mesh.vertices[vert_idx]

            unique_ids = {i: [] for i in list(set(loop_idx_to_unique_key[ll] for ll in linked_loops))}
            for ll in linked_loops:
                unique_ids[loop_idx_to_unique_key[ll]].append(ll)
            unique_values = [(loop_idx_to_key[lids[0]], lids) for id_, lids in unique_ids.items()]

            for unique_value, loops_with_this_value in unique_values:
                group_bone_ids = [get_bone_id(mesh_obj, model_data.skeleton.bone_names, grp) for grp in vertex.groups if grp.weight > vweight_floor]
                group_weights = [grp.weight for grp in vertex.groups if grp.weight > vweight_floor]
                # Normalise the group weights
                total_weight = sum(group_weights)
                if total_weight > 0.:
                    group_weights = [wght / total_weight for wght in group_weights]

                # Set to None for export if no vertices are left
                group_bone_ids = None if len(group_bone_ids) == 0 else group_bone_ids
                group_weights = None if len(group_weights) == 0 else group_weights

                vert = {'Position': vertex.co,
                        **{key: value for key, value in zip(['Normal'], unique_value[0])},
                        **{key: value for key, value in zip(['UV', 'UV2', 'UV3'], unique_value[1])},
                        **{key: value for key, value in zip(['Colour'], unique_value[2])},
                        **{key: value for key, value in zip(['Tangent'], unique_value[3])},
                        **{key: value for key, value in zip(['Binormal'], unique_value[4])},
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
        glfunc_to_id = flip_dict(id_to_glfunc)
        for bmat in used_materials:
            assigned_default_shader = bmat.get('shader_hex') is None

            material = model_data.new_material()
            node_tree = bmat.node_tree
            material.name = bmat.name
            material.shader_hex = bmat.get('shader_hex',
                                           '088100c1_00880111_00000000_00058000')
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
                        tex_names.append(texname)
                        used_textures.append(node_tree.nodes[nm].image)

                    # Construct the additional, unknown data
                    extra_data = bmat.get(nm)
                    if extra_data is None:
                        extra_data = [0, 0]
                    else:
                        extra_data = extra_data[1:]  # Chop off the texture idx

                    material.shader_uniforms[nm] = [tex_idx, *extra_data]

            if assigned_default_shader:
                texname = 'placeholder_toon.img'
                if texname in tex_names:
                    tex_idx = tex_names.index(texname)
                else:
                    tex_idx = len(used_textures)
                    tex_names.append(texname)
                    used_textures.append(DummyTexture(texname))
                material.shader_uniforms['CLUTSampler'] = [tex_idx, 0, 0]
            if 'DiffuseColor' not in node_names:
                material.shader_uniforms['DiffuseColor'] = [1., 1., 1., 1.]

            # Export the material components
            for key in shader_uniforms_vp_fp_from_names.keys():
                if bmat.get(key) is not None:
                    data = bmat.get(key)
                    try:
                        if hasattr(data, "__len__"):
                            data = [float(elem) for elem in data]
                        else:
                            data = [float(data)]

                        material.shader_uniforms[key] = data
                    except Exception as e:
                        raise TypeError(f"Shader Uniform value \"{key}\" cannot be interpreted as a list of floats: {data}") from e

            #########################
            # EXPORT OPENGL OPTIONS #
            #########################
            material.unknown_data['unknown_material_components'] = {}
            out = material.unknown_data['unknown_material_components']

            data = bmat.get("glBlendFunc")
            if data is not None:
                fglBlendFunc_options = flip_dict(glBlendFunc_options)
                param_1 = self.errorhandle_opengl_get("glBlendFunc", data[0], fglBlendFunc_options)
                param_2 = self.errorhandle_opengl_get("glBlendFunc", data[1], fglBlendFunc_options)

                out[glfunc_to_id["glBlendFunc"]] = [param_1, param_2, 0, 0]

            data = bmat.get("glBlendEquationSeparate")
            if data is not None:
                fglBlendEquationSeparate_options = flip_dict(glBlendEquationSeparate_options)
                param_1 = self.errorhandle_opengl_get("glBlendEquationSeparate", data, fglBlendEquationSeparate_options)
                out[glfunc_to_id["glBlendEquationSeparate"]] = [param_1, 0, 0, 0]

            data = bmat.get("GL_BLEND")
            if data is not None:
                fglEnable_options = flip_dict(glEnable_options)
                param_1 = self.errorhandle_opengl_get("GL_BLEND", data, fglEnable_options)
                out[glfunc_to_id["GL_BLEND"]] = [param_1, 0, 0, 0]

            data = bmat.get("glCullFace")
            if data is not None:
                fglCullFace_options = flip_dict(glCullFace_options)
                param_1 = self.errorhandle_opengl_get("glCullFace", data, fglCullFace_options)
                out[glfunc_to_id["glCullFace"]] = [param_1, 0, 0, 0]

            data = bmat.get("glDepthFunc")
            if data is not None:
                fglComparison_options = flip_dict(glComparison_options)
                param_1 = self.errorhandle_opengl_get("glDepthFunc", data, fglComparison_options)
                out[glfunc_to_id["glDepthFunc"]] = [param_1, 0, 0, 0]

            data = bmat.get("glDepthMask")
            if data is not None:
                fglBool_options = flip_dict(glBool_options)
                param_1 = self.errorhandle_opengl_get("glDepthMask", data, fglBool_options)
                out[glfunc_to_id["glDepthMask"]] = [param_1, 0, 0, 0]

            data = bmat.get("GL_DEPTH_TEST")
            if data is not None:
                fglEnable_options = flip_dict(glEnable_options)
                param_1 = self.errorhandle_opengl_get("GL_DEPTH_TEST", data, fglEnable_options)
                out[glfunc_to_id["GL_DEPTH_TEST"]] = [param_1, 0, 0, 0]

            data = bmat.get("glColorMask")
            if data is not None:
                fglBool_options = flip_dict(glBool_options)
                params = [self.errorhandle_opengl_get("glColorMask", opt, fglBool_options) for opt in data]
                out[glfunc_to_id["glColorMask"]] = params

            if not bmat.use_backface_culling:
                out[glfunc_to_id["GL_CULL_FACE"]] = [0, 0, 0, 0]
            if bmat.blend_method == 'CLIP':
                out[glfunc_to_id["GL_ALPHA_TEST"]] = [1, 0, 0, 0]
                out[glfunc_to_id["glAlphaFunc"]] = [516., bmat.alpha_threshold, 0, 0]

    @staticmethod
    def errorhandle_opengl_get(setting, option, optionlist):
        try:
            return optionlist[option]
        except Exception as e:
            newline = '\n'
            raise TypeError(f"\"{option}\" is not a valid OpenGL parameter for \"{setting}\". Options are:\n {newline.join(optionlist)}") from e

    def export_textures(self, used_textures, model_data, export_images_folder):
        used_texture_names = [tex.name for tex in used_textures]
        used_texture_paths = [os.path.normpath(tex.filepath) for tex in used_textures]
        for texture, texture_path in zip(used_texture_names, used_texture_paths):
            tex = model_data.new_texture()
            tex.name = os.path.splitext(texture)[0]
            if texture_path is not None:
                try:
                    _, texture_filename = os.path.split(texture_path)
                    texture_stem, texture_ext = os.path.splitext(texture_filename)
                    if self.img_to_dds and texture_ext == ".img":
                        use_texture = texture_stem + ".dds"
                    else:
                        use_texture = texture_filename
                    shutil.copy2(texture_path,
                                 os.path.join(export_images_folder, use_texture))
                except shutil.SameFileError:
                    continue
                except FileNotFoundError:
                    print(texture_path, "not found.")
                    continue

    def export_cameras(self, cameras, model_data):
        for camera_obj in cameras:
            cam = model_data.new_camera()
            childof_constraints = [constr for constr in camera_obj.constraints if constr.type == "CHILD_OF"]
            assert len(childof_constraints) == 1, f"Camera \'{camera_obj.name}\' must have ONE \'CHILD OF\' constraint."
            constr = childof_constraints[0]
            cam.bone_name = constr.subtarget
            assert type(cam.bone_name) == str, "[DEBUG] Not a string"

            camera = camera_obj.data
            cam.zNear = camera.clip_start
            cam.zFar = camera.clip_end

            if camera.type == "PERSP":
                cam.projection = 0
                # Put in a conversion from mm later...
                assert camera.lens_unit == "FOV", f"Camera not in FOV mode."
                cam.fov = camera.lens
                cam.orthographic_scale = 0.
            elif camera.type == "ORTHO":
                cam.projection = 1
                cam.fov = 0.
                cam.orthographic_scale = camera.ortho_scale

    def export_lights(self, lights, model_data):
        type_counts = [0, 0]
        for light_obj in lights:
            light = light_obj.data

            lgt = model_data.new_light()
            fogparam = light_obj.get("Unknown_Fog_Param")
            if fogparam is not None:
                lgt.mode = 4
                light_name = "Fog"
                light_id = 0
            elif light.type == "POINT":
                lgt.mode = 0
                light_id = type_counts[0]
                light_name = "PointLamp" + str(light_id).rjust(2, '0')
                type_counts[0] += 1
            elif light.type == "AREA":
                lgt.mode = 2
                light_name = "AmbientLamp"
                light_id = 99
            elif light.type == "SUN":
                lgt.mode = 3
                light_id = type_counts[1]
                light_name = "DirLamp" + str(light_id).rjust(2, '0')
                type_counts[1] += 1
            else:
                assert 0, "Unrecognised light type \'{light.type}\'."

            if fogparam is None:
                fogparam = 0.

            lgt.intensity = light.energy
            lgt.red, lgt.green, lgt.blue = list(light.color)
            lgt.alpha = light_obj.get("Alpha", 1.)

            lgt.bone_name = light_name
            lgt.light_id = light_id
            lgt.unknown_fog_param = fogparam

    def clean_up_model(self, model_data):
        if self.vweights_adjust == "FitToWeights":
            all_required_materials = {}
            for i, mesh in enumerate(model_data.meshes):
                key = (mesh.material_id, get_required_shader_width(mesh))
                if key not in all_required_materials:
                    all_required_materials[key] = []
                all_required_materials[key].append(i)

            new_materials = []
            material_handle_count = {}
            for new_material_idx, ((old_material_idx, width), mesh_idxs) in enumerate(all_required_materials.items()):
                new_materials.append(create_adjusted_shader_material(model_data, old_material_idx, width, material_handle_count))
                for mesh_idx in mesh_idxs:
                    model_data.meshes[mesh_idx].material_id = new_material_idx
            model_data.materials = new_materials

            print("ALL OUTPUT MATERIALS", len(model_data.materials))

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.export_file(context, filepath)

        return {'FINISHED'}


def get_required_shader_width(mesh):
    n_verts = max([len(vtx['WeightedBoneID']) if vtx['WeightedBoneID'] is not None else 0 for vtx in mesh.vertices])
    n_verts = 0 if len(mesh.vertex_groups) == 1 else n_verts
    return f"{0x40 + 8 * n_verts:0>2X}"


def create_adjusted_shader_material(model_data, idx, width, material_handle_count):
    material = model_data.materials[idx]
    shader_hex = material.shader_hex

    hex_st = shader_hex[:-5]
    hex_mid = shader_hex[-5:-3]
    hex_end = shader_hex[-3:]

    # Make new material
    new_material = copy.deepcopy(material)

    # Rename new material
    if idx in material_handle_count:
        name = "{material.name}_w{width}"
    else:
        material_handle_count[idx] = 0
        name = material.name
    material_handle_count[idx] += 1

    new_material.name = name

    # Fix the shader hex
    if width != hex_mid:
        new_material.shader_hex = hex_st + width + hex_end

    return new_material


def fix_weights(geomInterface, vweights_adjust):
    # Fix weight paddings
    for gi_mesh in geomInterface.meshes:
        if vweights_adjust == "FitToWeights":
            calculate_shader_weight_width(geomInterface, gi_mesh)
        elif vweights_adjust == "Pad4":
            if "WeightedBoneID" in gi_mesh.vertices[0]:
                for i, vertex in enumerate(gi_mesh.vertices):
                    vertex["WeightedBoneID"] = [*vertex["WeightedBoneID"], *([0]*(4-len(vertex["WeightedBoneID"])))]
                    vertex["BoneWeight"] = [*vertex["BoneWeight"], *([0.]*(4-len(vertex["BoneWeight"])))]
                    gi_mesh.vertices[i] = vertex
                calculate_shader_weight_width(geomInterface, gi_mesh)


def strip_unused_materials(geomInterface):
    used_material_ids = set()
    for mesh in geomInterface.meshes:
        used_material_ids.add(mesh.material_id)
    print(">> USED IDS", used_material_ids)
    material_id_map = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(used_material_ids))}
    print(">> ID MAP", material_id_map)
    for mesh in geomInterface.meshes:
        mesh.material_id = material_id_map[mesh.material_id]
    print(">> USED MATERIALS BEFORE STRIP", len(geomInterface.material_data))
    geomInterface.material_data = [material for i, material in enumerate(geomInterface.material_data) if
                                   i in material_id_map]
    print(">> USED MATERIALS AFTER STRIP", len(geomInterface.material_data))


def round_to_sigfigs(x, p):
    """
    Credit to Scott Gigante
    Taken from https://stackoverflow.com/a/59888924
    Rounds a float x to p significant figures
    """
    x = np.asarray(x)
    x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10**(p-1))
    mags = 10 ** (p - 1 - np.floor(np.log10(x_positive)))
    return np.round(x * mags) / mags


def matrices_to_rest_pose(bone_names, parent_bones, bind_pose_matrices):
    rest_pose = []
    for i, bone_name in enumerate(bone_names):
        bm = calculate_bone_matrix_relative_to_parent(i, parent_bones, bind_pose_matrices)
        # Shift from local space to model-space
        rloc, rquat, rscale = decompose_matrix(bm, WXYZ=False)
        if np.isnan(rquat[0]):
            rquat = [0., 0., 0., 0.5]
        rest_pose.append([rquat, [*rloc, 1.], [*rscale, 1.]])
    return rest_pose


def extract_rest_pose_from_base_animation(bone_names, parent_bones, base_animation, bind_pose_matrices):
    """Might have issues with animations that have 0 scale..?"""
    curve_defaults = {'rotation_quaternion': [1., 0., 0., 0.],
                      'location': [0., 0., 0.],
                      'scale': [1., 1., 1.],
                      'rotation_euler': [0., 0., 0.]}
    base_animation_data= get_action_data(base_animation, curve_defaults)

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
            if np.isnan(rquat[0]):
                rquat = [0., 0., 0., 0.5]
            rest_pose.append([rquat, [*rloc, 1.], [*rscale, 1.]])
        else:
            rest_pose.append([[0., 0., 0., 1.], [0., 0., 0., 1.], [1., 1., 1., 1.]])
    return rest_pose


def get_bone_id(mesh_obj, bone_names, grp):
    group_idx = grp.group
    bone_name = mesh_obj.vertex_groups[group_idx].name
    bone_id = bone_names.index(bone_name)
    return bone_id


class DummyTexture:
    def __init__(self, name):
        self.name = name
        self.filepath = os.path.join(*((__file__.split(os.sep))[:-3]), 'Resources', name)
        self.filepath = normalise_abs_path(self.filepath)


def get_all_nonempty_vertex_groups(mesh_obj):
    nonempty_vgs = set()
    for vertex in mesh_obj.data.vertices:
        for group in vertex.groups:
            nonempty_vgs.add(group.group)
    nonempty_vgs = sorted(list(nonempty_vgs))
    nonempty_vgs = [mesh_obj.vertex_groups[idx] for idx in nonempty_vgs]

    return nonempty_vgs


def validate_blender_data(parent_obj):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    armature = find_armatures(parent_obj)
    meshes = find_meshes(armature)
    check_vertex_group_counts(meshes)
    check_vertex_weight_counts(meshes)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None

    return armature, meshes


def find_armatures(parent_object):
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


def find_meshes(armature_obj):
    return [item for item in armature_obj.children if item.type == "MESH"]


def find_cameras(parent_object):
    return [item for item in parent_object.children if item.type == "CAMERA"]


def find_lights(parent_object):
    return [item for item in parent_object.children if item.type == "LIGHT"]


def check_vertex_group_counts(mesh_objs):
    bad_meshes = []
    for mesh_obj in mesh_objs:
        if len(get_all_nonempty_vertex_groups(mesh_obj)) > 56:
            bad_meshes.append(mesh_obj)
    if len(bad_meshes):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in bad_meshes:
            mesh.select_set(True)
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
        try:
            bpy.context.view_layer.objects.active = bad_meshes[0]
        except Exception as e:
            res = f"{e} "
            res += " ||| "
            res += " ".join([f"{mob}" for mob in mesh_objs])
            res += " ||| "
            res += " ".join([f"{mob}" for mob in bad_meshes])
            raise Exception(res)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        bad_meshes[0].select_set(True)

        bad_vertex_counts = [len(bvs) for bvs in all_bad_vertices]
        print(all_bad_vertices)  # For some reason, some verts don't decide to get selected without this...
        for bv in all_bad_vertices[0]:
            try:
                bv.select = True
            except:
                bv.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        newline = '\n'
        raise Exception(f"The following meshes have vertices included in more than 4 vertex groups:\n"
                        f"{newline.join([f'{mesh.name} ({bvc} bad vertices)' for mesh, bvc in zip(bad_meshes, bad_vertex_counts)])}\n"
                        f"The vertices for the mesh \"{bad_meshes[0].name}\" have been selected for you.\n"
                        f"Reduce the number of vertex groups these vertices are part of to 4 or less.\n"
                        f"You can do this per-vertex via the 'Items' panel of the pop-out menu near the top-right of the 3D viewport.")


class ExportDSCS(ExportMediaVision, ExportHelper):
    bl_idname = 'export_file.export_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'

    platform: EnumProperty(
        name="Platform",
        description="Select which platform the model is for.",
        items=[("PC", "PC", "Exports a DSCS Complete Edition PC model", "", 0),
               ("PS4", "PS4 (WIP)", "Exports a DSCS pr DSHM PS4 model. Not fully tested", "", 1)])

    export_anims: BoolProperty(
        name="Export Animations",
        description="Export animations or not."
    )


    img_to_dds: BoolProperty(
        name="IMG->DDS File Extension",
        description="Exports textures that have an 'img' extension with a 'dds' extension."
    )

    flip_uvs: BoolProperty(
        name="Flip UVs",
        description="Invert the exported UV coordinates."
    )

    recalc_normal_mode: EnumProperty(
        name="Recalc Normals",
        description="Policy for recalculating normals.",
        items=[("As Required", "As Required", "Recalculates normals for meshes with invalid loop normals", "", 0),
               ("Always", "Always", "Recalculates loop normals for every mesh", "", 1),
               ("Never", "Never", "Exports whatever loop normals Blender holds, even if they are zero", "", 2)]
    )

    vweights_adjust: EnumProperty(
        name="Fix Vertex Weights",
        description="Policy for post-processing Vertex Weights.",
        items=[("FitToWeights", "Adjust Shader", "Calculates the shader name that should be correctly aligned with the Vertex Weights on each mesh. This will generate additional materials where required. Some generated shader names may not exist in the game data, which will require them to be written by you. Meshes with non-existent shaders will not render in-game", "", 0),
               (        "FitToWeights",  "Pad all to 4", "Pads all vertex weights to a width of 4.", "", 1),
               (        "None",          "None", "Does not apply any post-processing to the Vertex Weights. This is very likely to result in graphical issues", "", 2)]
    )

    vweight_floor: FloatProperty(
        name="Vertex Weight Cutoff",
        description="Remove Vertex Weights below or equal to this minimum on export",
        default=0.0,
        min=0.0,
        max=1.0
    )

    export_anim_mode: EnumProperty(
        name="Anim Frame Integerisation",
        description="Policy for integerising animation frames.",
        items=[("Interpolate", "Interpolate", "Interpolates the keyframe values to the nearest integer frame, after scaling the keyframes such that each keyframe can be uniquely mapped to an integer frame value. Should result in smoother animations, but may be buggy.", "", 0),
               (       "Snap",        "Snap", "Integerises floating-point-valued frames by snapping the keyframes to the nearest integer, after scaling the keyframes such that each keyframe can be uniquely mapped to an integer frame value. Animations may be choppy, but stable.", "", 1)]
    )

    generate_physics: BoolProperty(
        name="Generate Physics",
        description="Whether to create a PHYS file from the model. Only used for Map models."
    )


class ExportMegido(ExportMediaVision, ExportHelper):
    bl_idname = 'export_file.export_megido'
    bl_label = 'Megido 72 (.name, .skel, .geom)'

    platform = "Megido"

    export_anims: BoolProperty(
        name="Export Animations",
        description="Export animations or not."
    )

    img_to_dds: BoolProperty(
        name="IMG->DDS File Extension",
        description="Exports textures that have an 'img' extension with a 'dds' extension."
    )

    flip_uvs: BoolProperty(
        name="Flip UVs",
        description="Invert the exported UV coordinates."
    )

    recalc_normal_mode: EnumProperty(
        name="Recalc Normals",
        description="Policy for recalculating normals.",
        items=[("As Required", "As Required", "Recalculates normals for meshes with invalid loop normals", "", 0),
               ("Always", "Always", "Recalculates loop normals for every mesh", "", 1),
               ("Never", "Never", "Exports whatever loop normals Blender holds, even if they are zero", "", 2)])
