import bpy
import numpy as np
import os
import shutil
from bpy.props import BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image
from bpy_extras.object_utils import object_data_add
from mathutils import Vector, Matrix
from ..CollatedData.FromReadWrites import generate_intermediate_format_from_files


class ImportDSCSBase:
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.name"

    filter_glob: bpy.props.StringProperty(
                                             default="*.name",
                                             options={'HIDDEN'},
                                         )

    import_anims: BoolProperty(
        name="Import Animations",
        description="Enable/disable to import/not import animations.",
        default=True)

    def import_file(self, context, filepath, platform):
        bpy.ops.object.select_all(action='DESELECT')
        model_data = generate_intermediate_format_from_files(filepath, platform, self.import_anims)
        filename = os.path.split(filepath)[-1]
        parent_obj = bpy.data.objects.new(filename, None)

        bpy.context.collection.objects.link(parent_obj)
        armature_name = f'{filename}_armature'
        self.import_skeleton(parent_obj, filename, model_data, armature_name)
        self.import_materials(model_data)
        self.import_meshes(parent_obj, filename, model_data, armature_name)
        # Do animations

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = parent_obj

        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (np.pi / 2, 0, 0)
        parent_obj.select_set(True)
        bpy.ops.object.transform_apply(rotation=True)
        parent_obj.select_set(False)

    def import_skeleton(self, parent_obj, filename, model_data, armature_name):
        model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(f'{filename}_armature_data'))
        bpy.context.collection.objects.link(model_armature)
        model_armature.parent = parent_obj

        # Rig
        list_of_bones = {}

        bpy.context.view_layer.objects.active = model_armature
        bpy.ops.object.mode_set(mode='EDIT')

        bone_matrices = model_data.skeleton.inverse_bind_pose_matrices
        for i, relation in enumerate(model_data.skeleton.bone_relations):
            child, parent = relation
            child_name = model_data.skeleton.bone_names[child]
            if child_name in list_of_bones:
                continue

            bm = bone_matrices[child]
            # This should just be the inverse though?!
            pos = bm[:3, 3]
            pos *= -1  # For some reason, need to multiply the positions by -1?

            rotation = bm[:3, :3]
            pos = np.dot(rotation.T, pos)  # And then rotate them?!

            bone_matrix = np.zeros((4, 4))
            bone_matrix[3, :3] = pos
            bone_matrix[:3, :3] = rotation.T
            bone_matrix[3, 3] = 1

            #####

            child_pos = pos

            bone = model_armature.data.edit_bones.new(child_name)

            list_of_bones[child_name] = bone
            bone.head = np.array([0., 0., 0.])
            bone.tail = np.array([0., 0.2, 0.])  # Make this scale with the model size in the future, for convenience
            bone.transform(Matrix(bone_matrix.tolist()))

            bone.head = np.array([0., 0., 0.]) + child_pos
            bone.tail = np.array(bone.tail) + child_pos

            if parent != -1:
                bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

        # Add the unknown data
        model_armature['unknown_0x0C'] = model_data.skeleton.unknown_data['unknown_0x0C']
        model_armature['unknown_data_1'] = model_data.skeleton.unknown_data['unknown_data_1']
        model_armature['unknown_data_2'] = model_data.skeleton.unknown_data['unknown_data_2']
        model_armature['unknown_data_3'] = model_data.skeleton.unknown_data['unknown_data_3']
        model_armature['unknown_data_4'] = model_data.skeleton.unknown_data['unknown_data_4']

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = parent_obj

    def import_materials(self, model_data):
        for i, IF_material in enumerate(model_data.materials):
            new_material = bpy.data.materials.new(name=IF_material.name)
            # Unknown data
            new_material['unknown_0x00'] = IF_material.unknown_data['unknown_0x00']
            new_material['unknown_0x02'] = IF_material.unknown_data['unknown_0x02']
            new_material['shader_hex'] = IF_material.shader_hex
            new_material['unknown_0x16'] = IF_material.unknown_data['unknown_0x16']

            for nm, value in IF_material.shader_uniforms.items():
                new_material[nm] = value
            for nm, value in IF_material.unknown_data['unknown_material_components'].items():
                new_material[str(nm)] = value

            new_material.use_nodes = True

            # Set some convenience variables
            shader_uniforms = IF_material.shader_uniforms
            nodes = new_material.node_tree.nodes
            connect = new_material.node_tree.links.new

            # Remove the default shader node
            bsdf_node = nodes.get('Principled BSDF')
            nodes.remove(bsdf_node)

            output_node = new_material.node_tree.nodes.get('Material Output')
            new_material.node_tree.links.clear()

            imported_textures = []
            final_diffuse_node = None
            if 'DiffuseTextureID' in shader_uniforms:
                tex0_img_node = nodes.new('ShaderNodeTexImage')
                tex0_img_node.name = "DiffuseTextureID"
                tex0_img_node.label = "DiffuseTextureID"
                set_texture_node_image(tex0_img_node, model_data.textures[shader_uniforms["DiffuseTextureID"][0]], imported_textures)
                tex0_node = nodes.new('ShaderNodeBsdfPrincipled')
                tex0_node.name = "DiffuseShader"
                tex0_node.label = "DiffuseShader"
                connect(tex0_img_node.outputs['Alpha'], tex0_node.inputs['Alpha'])

                # Might be updated by following nodes
                final_diffuse_colour_node = tex0_img_node
                if "ToonTextureID" in shader_uniforms:
                    toon_texture_node = nodes.new('ShaderNodeTexImage')
                    toon_texture_node.name = "ToonTextureID"
                    toon_texture_node.label = "ToonTextureID"
                    toon_node = nodes.new('ShaderNodeBsdfToon')
                    toon_node.name = "ToonShader"
                    toon_node.label = "ToonShader"
                    connect(toon_texture_node.outputs['Color'], toon_node.inputs['Color'])
                    set_texture_node_image(toon_texture_node, model_data.textures[shader_uniforms["ToonTextureID"][0]], imported_textures)

                    converter_node = nodes.new('ShaderNodeShaderToRGB')
                    connect(toon_node.outputs['BSDF'], converter_node.inputs['Shader'])

                    mix_node = new_material.node_tree.nodes.new('ShaderNodeMixRGB')
                    mix_node.blend_type = 'MULTIPLY'

                    connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
                    connect(converter_node.outputs['Color'], mix_node.inputs['Color2'])

                    final_diffuse_colour_node = mix_node
                if "DiffuseColour" in shader_uniforms:
                    rgba_node = nodes.new('ShaderNodeRGB')
                    rgba_node.name = "DiffuseColour"
                    rgba_node.label = "DiffuseColour"
                    rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColour"]

                    mix_node = nodes.new('ShaderNodeMixRGB')
                    mix_node.blend_type = 'MULTIPLY'
                    connect(final_diffuse_colour_node.outputs['Color'], mix_node.inputs['Color1'])
                    connect(rgba_node.outputs['Color'], mix_node.inputs['Color2'])

                    final_diffuse_colour_node = mix_node

                if "SpecularStrength" in shader_uniforms:
                    specular_value = nodes.new('ShaderNodeValue')
                    specular_value.name = 'SpecularStrength'
                    specular_value.label = 'SpecularStrength'
                    specular_value.outputs['Value'].default_value = shader_uniforms["SpecularStrength"][0]
                    connect(specular_value.outputs['Value'], tex0_node.inputs['Specular'])
                connect(final_diffuse_colour_node.outputs['Color'], tex0_node.inputs['Base Color'])
                final_diffuse_node = tex0_node

            elif "DiffuseColour" in shader_uniforms:
                rgba_node = nodes.new('ShaderNodeRGB')
                rgba_node.name = "DiffuseColour"
                rgba_node.label = "DiffuseColour"
                rgba_node.outputs['Color'].default_value = shader_uniforms["DiffuseColour"]

                diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
                diffuse_node.name = "DiffuseColourShader"
                diffuse_node.label = "DiffuseColourShader"

                connect(rgba_node.outputs['Color'], diffuse_node.inputs['Color'])
                final_diffuse_node = diffuse_node

            if final_diffuse_node is not None:
                connect(final_diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

            new_material.use_backface_culling = True
            new_material.blend_method = 'CLIP'
            new_material.alpha_threshold = 0.7

    def build_loops_and_verts(self, model_vertices, model_polygons):
        # Currently unused because it doesn't distinguish overlapping polygons with the same vertices but different vertex orders
        set_compliant_model_vertex_positions = [tuple(vert['Position']) for vert in model_vertices]
        verts = set(set_compliant_model_vertex_positions)
        verts = list(verts)

        map_of_model_verts_to_verts = {i: verts.index(vert) for i, vert in
                                       enumerate(set_compliant_model_vertex_positions)}

        map_of_loops_to_model_vertices = {}
        polys = []
        for poly_idx, poly in enumerate(model_polygons):
            poly_verts = []
            for model_vertex_idx in poly.indices:
                vert_idx = map_of_model_verts_to_verts[model_vertex_idx]
                map_of_loops_to_model_vertices[(poly_idx, vert_idx)] = model_vertex_idx
                poly_verts.append(vert_idx)
            polys.append(poly_verts)

        return verts, polys, map_of_loops_to_model_vertices, map_of_model_verts_to_verts

    def import_meshes(self, parent_obj, filename, model_data, armature_name):
        for i, IF_mesh in enumerate(model_data.meshes):
            # This function should be the best way to remove duplicate vertices (?) but doesn't pick up overlapping polygons with opposite normals
            # verts, faces, map_of_loops_to_model_vertices, map_of_model_verts_to_verts = self.build_loops_and_verts(IF_mesh.vertices, IF_mesh.polygons)
            # verts = [Vector(vert) for vert in verts]
            edges = []

            # Init mesh
            meshobj_name = f"{filename}_{i}"
            mesh = bpy.data.meshes.new(name=f"{filename}_{i}")
            mesh_object = bpy.data.objects.new(meshobj_name, mesh)

            verts = [Vector(v['Position']) for v in IF_mesh.vertices]
            faces = [poly.indices for poly in IF_mesh.polygons]
            mesh_object.data.from_pydata(verts, edges, faces)
            bpy.context.collection.objects.link(mesh_object)

            # Get the loop data
            # map_of_blenderloops_to_modelloops = {}
            # for poly_idx, poly in enumerate(mesh.polygons):
            #     for loop_idx in poly.loop_indices:
            #         vert_idx = mesh.loops[loop_idx].vertex_index
            #         model_vertex = map_of_loops_to_model_vertices[(poly_idx, vert_idx)]
            #         map_of_blenderloops_to_modelloops[loop_idx] = IF_mesh.vertices[model_vertex]

            # Assign normals
            # if 'Normal' in map_of_blenderloops_to_modelloops[0]:
            if 'Normal' in IF_mesh.vertices[0]:
                # loop_normals = [Vector(loop_data['Normal']) for loop_data in map_of_blenderloops_to_modelloops.values()]
                # loop_normals = [Vector(IF_mesh.vertices[loop.vertex_index]['Normal']) for loop in mesh_object.data.loops]
                # mesh_object.data.normals_split_custom_set([(0, 0, 0) for _ in mesh_object.data.loops])
                # mesh_object.data.normals_split_custom_set(loop_normals)
                mesh_object.data.normals_split_custom_set_from_vertices([Vector(v['Normal']) for v in IF_mesh.vertices])

            mesh.use_auto_smooth = True

            # Assign materials
            material_name = model_data.materials[IF_mesh.material_id].name
            active_material = bpy.data.materials[material_name]
            bpy.data.objects[meshobj_name].active_material = active_material

            # Assign UVs
            for uv_type in ['UV', 'UV2', 'UV3']:
                # if uv_type in map_of_blenderloops_to_modelloops[0]:
                if uv_type in IF_mesh.vertices[0]:
                    uv_layer = mesh.uv_layers.new(name=f"{uv_type}Map", do_init=True)
                    for loop_idx, loop in enumerate(mesh.loops):
                        # uv_layer.data[loop_idx].uv = map_of_blenderloops_to_modelloops[loop_idx][uv_type]
                        uv_layer.data[loop_idx].uv = IF_mesh.vertices[loop.vertex_index][uv_type]

            # Rig the vertices
            for IF_vertex_group in IF_mesh.vertex_groups:
                vertex_group = mesh_object.vertex_groups.new(name=model_data.skeleton.bone_names[IF_vertex_group.bone_idx])
                for vert_idx, vert_weight in zip(IF_vertex_group.vertex_indices, IF_vertex_group.weights):
                    #vertex_group.add([map_of_model_verts_to_verts[vert_idx]], vert_weight, 'REPLACE')
                    vertex_group.add([vert_idx], vert_weight, 'REPLACE')

            # Add unknown data
            mesh_object['unknown_0x31'] = IF_mesh.unknown_data['unknown_0x31']
            mesh_object['unknown_0x34'] = IF_mesh.unknown_data['unknown_0x34']
            mesh_object['unknown_0x36'] = IF_mesh.unknown_data['unknown_0x36']
            mesh_object['unknown_0x4C'] = IF_mesh.unknown_data['unknown_0x4C']

            bpy.data.objects[meshobj_name].select_set(True)
            bpy.data.objects[armature_name].select_set(True)
            # I would prefer to do this by directly calling object methods if possible
            # mesh_object.parent_set()...
            bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
            bpy.ops.object.parent_set(type='ARMATURE')

            mesh.validate(verbose=True)
            mesh.update()

            bpy.data.objects[meshobj_name].select_set(False)
            bpy.data.objects[armature_name].select_set(False)

        # Top-level unknown data
        parent_obj['unknown_cam_data_1'] = model_data.unknown_data['unknown_cam_data_1']
        parent_obj['unknown_cam_data_2'] = model_data.unknown_data['unknown_cam_data_2']
        parent_obj['unknown_footer_data'] = model_data.unknown_data['unknown_footer_data']

    def import_animations(self, parent_obj, model_armature, model_data):
        bpy.ops.object.mode_set(mode="POSE")
        model_armature.animation_data_create()
        for animation_name, animation_data in list(model_data.animations.items())[::-1]:
            action = bpy.data.actions.new(animation_name)

            for rotation_data, location_data, scale_data, bone_name in zip(animation_data.rotations.values(),
                                                                           animation_data.locations.values(),
                                                                           animation_data.scales.values(),
                                                                           model_data.skeleton.bone_names):
                if len(rotation_data.frames) != 0:
                    for i in range(4):
                        fc = action.fcurves.new(f'pose.bones["{bone_name}"].rotation_quaternion', index=i)
                        fc.keyframe_points.add(count=len(rotation_data.frames))
                        fc.keyframe_points.foreach_set("co", [x for co in zip([float(elem) for elem in rotation_data.frames],
                                                                              [elem[i] for elem in rotation_data.values]) for x in co])
                        fc.update()
                if len(location_data.frames) != 0:
                    for i in range(3):
                        fc = action.fcurves.new(f'pose.bones["{bone_name}"].location', index=i)
                        fc.keyframe_points.add(count=len(location_data.frames))
                        fc.keyframe_points.foreach_set("co", [x for co in zip([float(elem) for elem in location_data.frames],
                                                                              [elem[i] for elem in location_data.values]) for x in co])
                        fc.update()
                if len(scale_data.frames) != 0:
                    for i in range(3):
                        fc = action.fcurves.new(f'pose.bones["{bone_name}"].scale', index=i)
                        fc.keyframe_points.add(count=len(scale_data.frames))
                        fc.keyframe_points.foreach_set("co", [x for co in zip([float(elem) for elem in scale_data.frames],
                                                                              [elem[i] for elem in scale_data.values]) for x in co])
                        fc.update()

            model_armature.animation_data.action = action
            track = model_armature.animation_data.nla_tracks.new()
            track.name = action.name
            track.mute = True
            nla_strip = track.strips.new(action.name, action.frame_range[0], action)
            nla_strip.scale = 24 / animation_data.playback_rate
            model_armature.animation_data.action = None

    def execute_func(self, context, filepath, platform):
        filepath, file_extension = os.path.splitext(filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, filepath, platform)

        return {'FINISHED'}


def set_texture_node_image(node, IF_texture, import_memory):
    tex_filename = os.path.split(IF_texture.filepath)[-1]
    tempdir = bpy.app.tempdir
    dds_loc = os.path.join(tempdir, tex_filename)
    if tex_filename not in import_memory:
        import_memory.append(tex_filename)
        shutil.copy2(IF_texture.filepath, dds_loc)
        bpy.data.images.load(dds_loc)
    node.image = bpy.data.images[tex_filename]


class ImportDSCSPC(ImportDSCSBase, bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs_pc'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PC')


class ImportDSCSPS4(ImportDSCSBase, bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs_ps4'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PS4')


def get_total_transform(idx, parent_bones, bone_data):
    if idx == -1:
        rot = np.eye(3)
        loc = np.zeros(3)
        return rot, loc
    else:
        parent_idx = parent_bones[idx]
        parent_rot, parent_loc = get_total_transform(parent_idx, parent_bones, bone_data)

        rot = np.dot(parent_rot.T, quat_to_matrix(bone_data[idx][0]))
        loc = np.dot(parent_rot, np.array(bone_data[idx][1][:3])) + parent_loc

        return rot, loc


def quat_to_matrix(quat):
    quat = np.array(quat)
    x, y, z, w = quat
    x2, y2, z2, w2 = quat**2

    return 2*np.array([[.5 - y2 - z2,   x*y - z*w,   x*z + y*w],
                       [   x*y + z*w, .5 - x2 - z2,   y*z - x*w],
                       [   x*z - y*w,   y*z + x*w, .5 - x2 - y2]])

