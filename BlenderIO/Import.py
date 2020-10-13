import bpy
import numpy as np
import os
import shutil
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from ..CollatedData.FromReadWrites import generate_intermediate_format_from_files


class ImportDSCS(bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.name"

    filter_glob: bpy.props.StringProperty(
                                             default="*.name",
                                             options={'HIDDEN'},
                                         )

    def import_file(self, context, filepath):
        bpy.ops.object.select_all(action='DESELECT')
        model_data = generate_intermediate_format_from_files(filepath)
        filename = os.path.split(filepath)[-1]
        parent_obj = bpy.data.objects.new(filename, None)

        bpy.context.collection.objects.link(parent_obj)

        armature_name = f'{filename}_armature'
        model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(f'{filename}_armature_data'))
        bpy.context.collection.objects.link(model_armature)
        model_armature.parent = parent_obj

        # Rig
        bone_pos = {}
        list_of_bones = {}
        for i, bone_position in enumerate(model_data.skeleton.bone_positions):
            bone_pos[i] = bone_position

        bpy.context.view_layer.objects.active = model_armature
        bpy.ops.object.mode_set(mode='EDIT')
        for i, relation in enumerate(model_data.skeleton.bone_relations):
            child, parent = relation
            child_name = model_data.skeleton.bone_names[child]
            if child_name in list_of_bones:
                continue
            child_pos = bone_pos[child]

            # Now fake some bone tails to make Blender happy
            grandchildren_positions = []
            for relation_2 in model_data.skeleton.bone_relations:
                grandchild, child_2 = relation_2
                if child_2 == child:
                    grandchildren_positions.append(bone_pos[grandchild])

            if len(grandchildren_positions) > 0:
                tail_pos = np.mean(grandchildren_positions, axis=0)
            elif parent == -1:
                tail_pos = [item for item in child_pos]
                tail_pos[2] += 0.05
            else:
                # Get the vector from the parent to the child (i.e. the bone length), and just repeat it for the child
                parent_pos = bone_pos[parent]
                parent_bone_vec = np.array(child_pos) - np.array(parent_pos)
                if np.sqrt(np.sum(parent_bone_vec**2)) < 0.0001:
                    parent_bone_vec[2] += 0.05
                tail_pos = np.array(child_pos) + parent_bone_vec

            bone = model_armature.data.edit_bones.new(child_name)

            # Add the unknown vectors... might define the local coordinate system?!
            bone['xvecs'] = model_data.skeleton.bone_xaxes[i]
            bone['yvecs'] = model_data.skeleton.bone_yaxes[i]
            bone['zvecs'] = model_data.skeleton.bone_zaxes[i]

            list_of_bones[child_name] = bone
            bone.head = child_pos
            bone.tail = list(tail_pos)
            if parent != -1:
                bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

        # Add the unknown data
        model_armature['unknown_0x0C'] = model_data.skeleton.unknown_data['unknown_0x0C']
        model_armature['unknown_parent_child_data'] = model_data.skeleton.unknown_data['unknown_parent_child_data']
        model_armature['bone_data'] = model_data.skeleton.unknown_data['bone_data']
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

        for i, IF_material in enumerate(model_data.materials):
            # print(IF_material.textureID)
            # print(model_data.textures)
            # tex_name = model_data.textures[IF_material.textureID].name
            new_material = bpy.data.materials.new(name=IF_material.name)
            # Unknown data
            new_material['unknown_0x00'] = IF_material.unknown_data['unknown_0x00']
            new_material['unknown_0x10'] = IF_material.unknown_data['unknown_0x10']
            new_material['unknown_0x11'] = IF_material.unknown_data['unknown_0x11']
            new_material['unknown_0x12'] = IF_material.unknown_data['unknown_0x12']
            new_material['unknown_0x16'] = IF_material.unknown_data['unknown_0x16']
            new_material['temp_reference_textures'] = [tex.name for tex in model_data.textures]
            for key in IF_material.unknown_data:
                cstring_1 = 'type_1_component_'
                cstring_2 = 'type_2_component_'
                if key[:len(cstring_1)] == cstring_1:
                    new_material[key] = IF_material.unknown_data[key]
                elif key[:len(cstring_2)] == cstring_2:
                    new_material[key] = IF_material.unknown_data[key]


            new_material.use_nodes = True

            # Get nodes to work with
            bsdf_node = new_material.node_tree.nodes.get('Principled BSDF')
            connect = new_material.node_tree.links.new
            if IF_material.specular_coeff is not None:
                bsdf_node.inputs['Specular'].default_value = IF_material.specular_coeff
            # Set texture
            if IF_material.texture_id is not None:
                texture_node = new_material.node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.location = (-350, 220)
                connect(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                # texture_node.image = bpy.data.images[tex_name]

                IF_texture = model_data.textures[IF_material.texture_id]
                tex_filepath, tex_fileext = os.path.splitext(IF_texture.filepath)
                tex_filename = os.path.split(tex_filepath)[-1]
                tempdir = bpy.app.tempdir
                # The img files are just dds obscured by a different file extension...
                dds_loc = os.path.join(tempdir, tex_filename) + '.dds'
                shutil.copy2(IF_texture.filepath, dds_loc)
                texture_node.image = bpy.data.images.load(dds_loc)
                # os.remove(dds_loc)
            # This is not the right way to do the colours...
            # if IF_material.emission_rgba is not None:
            #    rgba_node = new_material.node_tree.nodes.new('ShaderNodeRGB')
            #    rgba_node.location = (-350, 100)
            #    rgba_node.outputs['Color'].default_value = IF_material.emission_rgba
            #    connect(rgba_node.outputs['Color'], bsdf_node.inputs['Emission'])

            new_material.use_backface_culling = True

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

            uv_layer = mesh.uv_layers.new(name="UVMap", do_init=True)
            for face in mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    if IF_mesh.vertices[vert_idx].UV is not None:
                        uv_layer.data[loop_idx].uv = IF_mesh.vertices[vert_idx].UV

            for IF_vertex_group in IF_mesh.vertex_groups:
                vertex_group = mesh_object.vertex_groups.new(
                    name=model_data.skeleton.bone_names[IF_vertex_group.bone_idx])
                for vert_idx, vert_weight in zip(IF_vertex_group.vertex_indices, IF_vertex_group.weights):
                    vertex_group.add([vert_idx], vert_weight, 'REPLACE')

            # Add unknown data
            mesh_object['unknown_0x30'] = IF_mesh.unknown_data['unknown_0x30']
            mesh_object['unknown_0x31'] = IF_mesh.unknown_data['unknown_0x31']
            mesh_object['unknown_0x34'] = IF_mesh.unknown_data['unknown_0x34']
            mesh_object['unknown_0x36'] = IF_mesh.unknown_data['unknown_0x36']
            mesh_object['unknown_0x44'] = IF_mesh.unknown_data['unknown_0x44']
            mesh_object['unknown_0x50'] = IF_mesh.unknown_data['unknown_0x50']
            mesh_object['unknown_0x5C'] = IF_mesh.unknown_data['unknown_0x5C']

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
        parent_obj['geom_unknown_0x14'] = model_data.unknown_data['geom_unknown_0x14']
        parent_obj['geom_unknown_0x20'] = model_data.unknown_data['geom_unknown_0x20']
        parent_obj['unknown_cam_data_1'] = model_data.unknown_data['unknown_cam_data_1']
        parent_obj['unknown_cam_data_2'] = model_data.unknown_data['unknown_cam_data_2']
        parent_obj['unknown_footer_data'] = model_data.unknown_data['unknown_footer_data']
        parent_obj['material names'] = model_data.unknown_data['material names']

        bpy.context.view_layer.objects.active = parent_obj
        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (np.pi / 2, 0, 0)

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, filepath)

        return {'FINISHED'}
