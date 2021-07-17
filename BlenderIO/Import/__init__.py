import bpy
import copy
import numpy as np
import os
from bpy.props import BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Matrix
from ...CollatedData.FromReadWrites import generate_intermediate_format_from_files
from .AnimationImport import import_animations
from ...Utilities.ExportedAnimationReposingFunctions import shift_animation_data
from .ArmatureImport import import_skeleton
from .MaterialImport import import_materials
from .MeshImport import import_meshes


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
    skeleton_mode: EnumProperty(
        name="Skeleton Type",
        description="Which skeleton to import. 'Bind Pose' is currently the only one which works with animations.",
        items=[("Bind Pose", "Bind Pose", "Use the Bind Pose stored in the Geom file.", "", 0),
               ("Rest Pose", "Rest Pose", "Deform the Bind {ose to the Rest Pose stored in the Skel file.", "", 1),
               ("Composite Pose", "Composite Pose", "Combines Geom, Skel, and Anim data into what the game seems to use as a base pose for the animations.", "", 2)])

    def import_file(self, context, filepath, platform):
        bpy.ops.object.select_all(action='DESELECT')
        model_data = generate_intermediate_format_from_files(filepath, platform, self.import_anims)
        filename = os.path.split(filepath)[-1]
        armature_name = filename + "_armature"
        parent_obj = bpy.data.objects.new(filename, None)

        bpy.context.collection.objects.link(parent_obj)
        import_skeleton(parent_obj, armature_name, model_data)
        import_materials(model_data)
        import_meshes(parent_obj, filename, model_data, armature_name)
        add_rest_pose_to_base_anim(filename, model_data)
        import_animations(armature_name, model_data)

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = parent_obj

        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (np.pi / 2, 0, 0)

    def execute_func(self, context, filepath, platform):
        filepath, file_extension = os.path.splitext(filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, filepath, platform)

        return {'FINISHED'}


def add_rest_pose_to_base_anim(filename, model_data):
    base_animation = model_data.animations[filename]
    for bone_idx, (quat, loc, scl) in enumerate(model_data.skeleton.rest_pose_delta):
        if not len(base_animation.rotations[bone_idx].frames):
            base_animation.rotations[bone_idx].frames.append(0)
            base_animation.rotations[bone_idx].values.append(np.roll(quat, 1))  # XYZW -> WXYZ convention
        if not len(base_animation.locations[bone_idx].frames):
            base_animation.locations[bone_idx].frames.append(0)
            base_animation.locations[bone_idx].values.append(loc[:3])  # Cut off affine coord
        if not len(base_animation.scales[bone_idx].frames):
            base_animation.scales[bone_idx].frames.append(0)
            base_animation.scales[bone_idx].values.append(scl[:3])  # Cut off affine coord


class ImportDSCSPC(ImportDSCSBase, bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs_pc'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PC')


class ImportDSCSPS4(ImportDSCSBase, bpy.types.Operator, ImportHelper):
    bl_idname = 'import_file.import_dscs_ps4'

    def execute(self, context):
        return super().execute_func(context, self.filepath, 'PS4')
