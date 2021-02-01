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
        model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(f'{filename}_armature_data'))
        bpy.context.collection.objects.link(model_armature)
        model_armature.parent = parent_obj

        # Rig
        list_of_bones = {}

        bpy.context.view_layer.objects.active = model_armature
        bpy.ops.object.mode_set(mode='EDIT')
        for i, relation in enumerate(model_data.skeleton.bone_relations):
            child, parent = relation
            child_name = model_data.skeleton.bone_names[child]
            if child_name in list_of_bones:
                continue

            child_pos = np.array(model_data.skeleton.bone_matrices[child][3, :3])

            bone = model_armature.data.edit_bones.new(child_name)

            list_of_bones[child_name] = bone
            bone.head = np.array([0., 0., 0.])
            bone.tail = np.array([0., 0.2, 0.])  # Make this scale with the model size in the future, for convenience
            bone.transform(Matrix(model_data.skeleton.bone_matrices[child].tolist()))

            bone.head = np.array([0., 0., 0.]) + child_pos
            bone.tail = np.array(bone.tail) + child_pos

            if parent != -1:
                bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

        # Add the unknown data
        model_armature['unknown_0x0C'] = model_data.skeleton.unknown_data['unknown_0x0C']
        model_armature['unknown_parent_child_data'] = model_data.skeleton.unknown_data['unknown_parent_child_data']
        model_armature['unknown_data_1'] = model_data.skeleton.unknown_data['unknown_data_1']
        model_armature['unknown_data_2'] = model_data.skeleton.unknown_data['unknown_data_2']
        model_armature['unknown_data_3'] = model_data.skeleton.unknown_data['unknown_data_3']
        model_armature['unknown_data_4'] = model_data.skeleton.unknown_data['unknown_data_4']

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = parent_obj

        # Can't get blender to import the images as textures and then use them in material nodes
        # Would much prefer to do it this way than to have the textures 'floating around'...
        # for i, IF_texture in enumerate(model_data.textures):
        #     new_texture = bpy.data.images.new(name=IF_texture.name)
        #     tex_filepath, tex_fileext = os.path.splitext(IF_texture.filepath)
        #     tex_filename = os.path.split(tex_filepath)[-1]
        #     tempdir = bpy.app.tempdir
        #     dds_loc = os.path.join(tempdir, tex_filename) + '.dds'
        #     shutil.copy2(IF_texture.filepath, dds_loc)
        #     new_texture.image = bpy.data.images.load(dds_loc)
        # os.remove(dds_loc)

        imported_textures = []
        for i, IF_material in enumerate(model_data.materials):
            # print(IF_material.textureID)
            # print(model_data.textures)
            # tex_name = model_data.textures[IF_material.textureID].name
            new_material = bpy.data.materials.new(name=IF_material.name)
            # Unknown data
            new_material['unknown_0x00'] = IF_material.unknown_data['unknown_0x00']
            new_material['unknown_0x02'] = IF_material.unknown_data['unknown_0x02']
            new_material['shader_hex'] = IF_material.shader_hex
            new_material['shaders_folder'] = os.path.join(*os.path.split(filepath)[:-1], 'shaders')
            #  new_material['unknown_0x16'] = IF_material.unknown_data['unknown_0x16']
            new_material['temp_reference_textures'] = [tex.name for tex in model_data.textures]
            for key in IF_material.unknown_data:
                cstring_1 = 'type_1_component_'
                cstring_2 = 'type_2_component_'
                if key[:len(cstring_1)] == cstring_1:
                    new_material[key] = IF_material.unknown_data[key]
                elif key[:len(cstring_2)] == cstring_2:
                    for i, elem in enumerate(IF_material.unknown_data[key]):
                        new_material[f"{key}_{i}"] = elem

            new_material.use_nodes = True

            # Get nodes to work with
            bsdf_node = new_material.node_tree.nodes.get('Principled BSDF')
            output_node = new_material.node_tree.nodes.get('Material Output')
            new_material.node_tree.links.clear()
            connect = new_material.node_tree.links.new
            if IF_material.specular_coeff is not None:
                bsdf_node.inputs['Specular'].default_value = IF_material.specular_coeff
            # Set texture
            if IF_material.texture_id is not None:
                texture_node = new_material.node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.location = (-350, 220)
                connect(texture_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])
                set_texture_node_image(texture_node, model_data.textures[IF_material.texture_id], imported_textures)

            # This is not the right way to do the colours...
            # if IF_material.emission_rgba is not None:
            #    rgba_node = new_material.node_tree.nodes.new('ShaderNodeRGB')
            #    rgba_node.location = (-350, 100)
            #    rgba_node.outputs['Color'].default_value = IF_material.emission_rgba
            #    connect(rgba_node.outputs['Color'], bsdf_node.inputs['Emission'])
            if IF_material.toon_texture_id is not None:
                toon_texture_node = new_material.node_tree.nodes.new('ShaderNodeTexImage')
                toon_node = new_material.node_tree.nodes.new('ShaderNodeBsdfToon')

                connect(toon_texture_node.outputs['Color'], toon_node.inputs['Color'])
                set_texture_node_image(toon_texture_node, model_data.textures[IF_material.toon_texture_id], imported_textures)

                converter_node = new_material.node_tree.nodes.new('ShaderNodeShaderToRGB')
                connect(toon_node.outputs['BSDF'], converter_node.inputs['Shader'])

                mix_node = new_material.node_tree.nodes.new('ShaderNodeMixRGB')
                mix_node.blend_type = 'MULTIPLY'

                connect(texture_node.outputs['Color'], mix_node.inputs['Color1'])
                connect(converter_node.outputs['Color'], mix_node.inputs['Color2'])

                connect(mix_node.outputs['Color'], bsdf_node.inputs['Base Color'])
            else:
                connect(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])

            connect(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

            new_material.use_backface_culling = True
            new_material.blend_method = 'CLIP'
            new_material.alpha_threshold = 0.7

        for i, IF_mesh in enumerate(model_data.meshes):
            verts = [Vector(vertex.position) for vertex in IF_mesh.vertices]
            edges = []
            faces = [poly.indices for poly in IF_mesh.polygons]

            meshobj_name = f"{filename}_{i}"
            mesh = bpy.data.meshes.new(name=f"{filename}_{i}")
            mesh_object = bpy.data.objects.new(meshobj_name, mesh)
            mesh_object.data.from_pydata(verts, edges, faces)
            bpy.context.collection.objects.link(mesh_object)

            # NO IDEA how to do the normals properly - this is probably a hack?!
            vertex_normals = [vertex.normal for vertex in IF_mesh.vertices]
            if all([normal is not None for normal in vertex_normals]):
                try:
                    vertex_normals = [Vector(normal) for normal in vertex_normals]
                except Exception as e:
                    print("Bad normals:", vertex_normals)
                    raise e
                mesh_object.data.normals_split_custom_set([(0, 0, 0) for _ in mesh_object.data.loops])
                #mesh_object.data.normals_split_custom_set(vertex_normals)
                mesh.normals_split_custom_set_from_vertices(vertex_normals)
            else:
                vertex_normals = []

            material_name = model_data.materials[IF_mesh.material_id].name
            active_material = bpy.data.materials[material_name]
            bpy.data.objects[f"{filename}_{i}"].active_material = active_material

            all_verts_have_no_uvs = all(vert.UV is None for vert in IF_mesh.vertices)
            at_least_one_vert_has_uvs = any(vert.UV is not None for vert in IF_mesh.vertices)
            if all_verts_have_no_uvs:
                assert not at_least_one_vert_has_uvs, f"Some vertices in mesh {i} have UVs and some don't!"
            else:
                uv_layer = mesh.uv_layers.new(name="UVMap", do_init=True)
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        uv_layer.data[loop_idx].uv = IF_mesh.vertices[vert_idx].UV

            for IF_vertex_group in IF_mesh.vertex_groups:
                vertex_group = mesh_object.vertex_groups.new(
                    name=model_data.skeleton.bone_names[IF_vertex_group.bone_idx])
                for vert_idx, vert_weight in zip(IF_vertex_group.vertex_indices, IF_vertex_group.weights):
                    vertex_group.add([vert_idx], vert_weight, 'REPLACE')

            # Add unknown data
            mesh_object['unknown_0x31'] = IF_mesh.unknown_data['unknown_0x31']
            mesh_object['unknown_0x34'] = IF_mesh.unknown_data['unknown_0x34']
            mesh_object['unknown_0x36'] = IF_mesh.unknown_data['unknown_0x36']
            mesh_object['unknown_0x4C'] = IF_mesh.unknown_data['unknown_0x4C']
            #  mesh_object['unknown_0x50'] = IF_mesh.unknown_data['unknown_0x50']
            #  mesh_object['unknown_0x5C'] = IF_mesh.unknown_data['unknown_0x5C']

            bpy.data.objects[meshobj_name].select_set(True)
            bpy.data.objects[armature_name].select_set(True)
            # I would prefer to do this by directly calling object methods if possible
            bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
            bpy.ops.object.parent_set(type='ARMATURE')

            mesh.validate(verbose=True)
            mesh.update()
            for pos, normal, vec in zip(verts, vertex_normals, mesh.vertices):
                vec.normal = normal
            mesh.use_auto_smooth = True

            bpy.data.objects[meshobj_name].select_set(False)
            bpy.data.objects[armature_name].select_set(False)

        # Top-level unknown data
        parent_obj['unknown_cam_data_1'] = model_data.unknown_data['unknown_cam_data_1']
        parent_obj['unknown_cam_data_2'] = model_data.unknown_data['unknown_cam_data_2']
        parent_obj['unknown_footer_data'] = model_data.unknown_data['unknown_footer_data']
        parent_obj['material names'] = model_data.unknown_data['material names']

        if self.import_anims:
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

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = parent_obj
        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (np.pi / 2, 0, 0)
        parent_obj.select_set(True)
        bpy.ops.object.transform_apply(rotation=True)
        parent_obj.select_set(False)

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
