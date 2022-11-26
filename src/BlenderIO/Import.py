import math
import os

import bpy
from bpy.props import BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from ..Core.FileFormats.Name.NameInterface import NameInterface
from ..Core.FileFormats.Skel.SkelInterface import SkelInterface
from ..Core.FileFormats.Geom.GeomInterface import GeomInterface
from ..Core.FileFormats.Anim.AnimInterface import AnimInterface


class ImportMediaVision(bpy.types.Operator):
    platform = None
    import_anims = None
    img_to_dds = None
    use_custom_nodes = None
    merge_vertices = None

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def import_file(self, context, filepath):
        bpy.ops.object.select_all(action='DESELECT')

        directory, model_name = os.path.split(os.path.splitext(filepath)[0])
        armature_name = model_name + "_armature"

        parent_obj = bpy.data.objects.new(model_name, None)
        bpy.context.collection.objects.link(parent_obj)

        # Import data
        #import_skeleton(parent_obj, armature_name)
        # import_materials(model_data, self.img_to_dds, self.use_custom_nodes)
        # import_meshes(parent_obj, filename, model_data, armature_name, self.merge_vertices)
        # import_cameras(parent_obj, model_data)
        # import_lights(parent_obj, model_data)
        # add_rest_pose_to_base_anim(filename, model_data)
        # import_animations(parent_obj.name, armature_name, model_data)
        #
        # armature = [child for child in parent_obj.children if child.type == "ARMATURE"][0]
        #
        # armature.animation_data.nla_tracks["base"].mute = False

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = parent_obj

        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (math.pi / 2, 0, 0)

    #@handle_errors
    def execute(self, context):
        folder = (os.path.dirname(self.filepath))

        # iterate through the selected files
        for file in self.files:
            path_to_file = (os.path.join(folder, file.name))
            filepath, file_extension = os.path.splitext(path_to_file)
            assert any([file_extension == ext for ext in
                        ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
            self.import_file(context, filepath)

        return {'FINISHED'}


# def add_rest_pose_to_base_anim(filename, model_data):
#     base_animation = model_data.animations[filename]
#     for bone_idx, (quat, loc, scl) in enumerate(model_data.skeleton.rest_pose_delta):
#         if not len(base_animation.rotations[bone_idx].frames):
#             base_animation.rotations[bone_idx].frames.append(0)
#             base_animation.rotations[bone_idx].values.append(quat)  # XYZW -> WXYZ convention
#         if not len(base_animation.locations[bone_idx].frames):
#             base_animation.locations[bone_idx].frames.append(0)
#             base_animation.locations[bone_idx].values.append(loc[:3])  # Cut off affine coord
#         if not len(base_animation.scales[bone_idx].frames):
#             base_animation.scales[bone_idx].frames.append(0)
#             base_animation.scales[bone_idx].values.append(scl[:3])  # Cut off affine coord


class ImportDSCS(ImportMediaVision, ImportHelper):
    bl_idname = 'import_file.import_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.name"

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(
                                             default="*.name",
                                             options={'HIDDEN'},
                                         )

    import_anims: BoolProperty(
        name="Import Animations",
        description="Import animations or not."
    )

    merge_vertices: BoolProperty(
        name="Merge Vertices",
        description="Merge the OpenGL vertices (which look like duplicates in Blender) to Blender vertices.",
        default=True
    )

