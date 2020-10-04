import bpy
import numpy as np
import os
import shutil
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from .CollatedData.FromReadWrites import generate_intermediate_format_from_files


bl_info = {
        "name": "Digimon Story: Cyber Sleuth (.name)",
        "description": "Imports model files from Digimon Story: Cyber Sleuth (PC)",
        "author": "Pherakki",
        "version": (0, 1),
        "blender": (2, 80, 0),
        "location": "File > Import",
        "warning": "",
        "category": "Import-Export",
        }


class ImportDSCS(bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.name"
    
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
        for relation in model_data.skeleton.bone_relations:
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
                tail_pos = np.array(child_pos) + parent_bone_vec

            bone = model_armature.data.edit_bones.new(child_name)
            list_of_bones[child_name] = bone
            bone.head = child_pos
            bone.tail = list(tail_pos)
            if parent != -1:
                bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]
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
            #os.remove(dds_loc)

        for i, IF_material in enumerate(model_data.materials):
            #print(IF_material.textureID)
            #print(model_data.textures)
            #tex_name = model_data.textures[IF_material.textureID].name

            new_material = bpy.data.materials.new(name=IF_material.name)
            new_material.use_nodes = True

            # Get nodes to work with
            bsdf_node = new_material.node_tree.nodes.get('Principled BSDF')
            connect = new_material.node_tree.links.new

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
            #if IF_material.emission_rgba is not None:
            #    rgba_node = new_material.node_tree.nodes.new('ShaderNodeRGB')
            #    rgba_node.location = (-350, 100)
            #    rgba_node.outputs['Color'].default_value = IF_material.emission_rgba
            #    connect(rgba_node.outputs['Color'], bsdf_node.inputs['Emission'])

        for i, IF_mesh in enumerate(model_data.meshes):
            verts = [Vector(vertex.position) for vertex in IF_mesh.vertices]
            edges = []
            faces = [poly.indices for poly in IF_mesh.polygons]

            meshobj_name = f"{filename}_{i}"
            mesh = bpy.data.meshes.new(name=f"{filename}_{i}")
            mesh_object = bpy.data.objects.new(meshobj_name, mesh)
            mesh_object.data.from_pydata(verts, edges, faces)
            bpy.context.collection.objects.link(mesh_object)

            vertex_normals = [Vector(vertex.normal) for vertex in IF_mesh.vertices]
            # I think this assignment is incorrect - the data in 'vertex_normals' are 3-vectors, one per vertex,
            # no idea what blender does with this 'normals_split_custom_set_from_vertices' function but the
            # results don't look right at all. Disabled until I gain basic competency
            #mesh.normals_split_custom_set_from_vertices(vertex_normals)

            material_name = model_data.materials[IF_mesh.material_id].name
            active_material = bpy.data.materials[material_name]
            bpy.data.objects[f"{filename}_{i}"].active_material = active_material

            uv_layer = mesh.uv_layers.new(name="UVMap", do_init=True)
            for face in mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    if IF_mesh.vertices[vert_idx].UV is not None:
                        uv_layer.data[loop_idx].uv = IF_mesh.vertices[vert_idx].UV

            for IF_vertex_group in IF_mesh.vertex_groups:
                vertex_group = mesh_object.vertex_groups.new(name=model_data.skeleton.bone_names[IF_vertex_group.bone_idx])
                for vert_idx, vert_weight in zip(IF_vertex_group.vertex_indices, IF_vertex_group.weights):
                    vertex_group.add([vert_idx], vert_weight, 'REPLACE')

            bpy.data.objects[meshobj_name].select_set(True)
            bpy.data.objects[armature_name].select_set(True)
            # I would prefer to do this by directly calling object methods if possible
            bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
            bpy.ops.object.parent_set(type='ARMATURE')
            mesh.validate(verbose=True)
            mesh.update()
            bpy.data.objects[meshobj_name].select_set(False)
            bpy.data.objects[armature_name].select_set(False)

        bpy.context.view_layer.objects.active = parent_obj

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, filepath)
        
        return {'FINISHED'}

    
def menu_func_import(self, context):
    self.layout.operator(ImportDSCS.bl_idname, text="DSCS Model (.name)")


# def menu_func_export(self, context):
#     self.layout.operator(ExportDSCS.bl_idname, text="DSCS Model (.name)")


def register():
    bpy.utils.register_class(ImportDSCS)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    # Not ready for this one yet
    # bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportDSCS)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    # Not ready for this one yet
    # bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

# if __name__ == "__main__":
#     register()
