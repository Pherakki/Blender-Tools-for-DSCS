import bpy
import copy
import numpy as np
import os
from bpy.props import BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
from ...CollatedData.FromReadWrites import generate_intermediate_format_from_files
from .AnimationImport import import_animations
from .ArmatureImport import import_skeleton
from .MaterialImport import import_materials
from .MeshImport import import_meshes
from ...Utilities.Reposing import set_new_rest_pose


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

    platform: EnumProperty(
        name="Platform",
        description="Select which platform the model is for.",
        items=[("PC", "PC", "Imports a DSCS Complete Edition PC model", "", 0),
               ("PS4", "PS4 (WIP)", "Imports a DSCS pr DSHM PS4 model. Not fully tested", "", 1)])

    import_mode: EnumProperty(
        name="Import Mode",
        description="Which mode to import in.",
        items=[("Modelling", "Modelling", "Imports the model in the Bind Pose with its base animation only", "", 0),
               ("Animation", "Animation", "Deform the Bind Pose to the Rest Pose stored in the Skel file, and load all overlay animations", "", 1),
               ("QA", "QA", "Loads the model in the Bind Pose with all animations. Overlay Animations must be viewed as additions to the Base Animation in the NLA editor to display corectly. Should be used to check all animations work as intended with the Base Pose before export", "", 2)])

    def import_file(self, context, filepath):
        bpy.ops.object.select_all(action='DESELECT')
        model_data = generate_intermediate_format_from_files(filepath, self.platform,
                                                             any([self.import_mode == mode for mode in ["Animation", "QA"]]))
        filename = os.path.split(filepath)[-1]
        armature_name = filename + "_armature"
        parent_obj = bpy.data.objects.new(filename, None)

        bpy.context.collection.objects.link(parent_obj)
        import_skeleton(parent_obj, armature_name, model_data)
        import_materials(model_data)
        import_meshes(parent_obj, filename, model_data, armature_name)
        add_rest_pose_to_base_anim(filename, model_data)
        import_animations(armature_name, model_data)

        print(self.import_mode)
        if self.import_mode == "Animation":
            set_new_rest_pose(armature_name, model_data.skeleton.bone_names, model_data.skeleton.rest_pose_delta)
        else:
            # Unmute the base animation on the armature
            parent_obj.children[0].animation_data.nla_tracks[parent_obj.name].mute = False

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = parent_obj

        # Rotate to the Blender coordinate convention
        parent_obj.rotation_euler = (np.pi / 2, 0, 0)

    def execute(self, context):
        filepath, file_extension = os.path.splitext(self.filepath)
        assert any([file_extension == ext for ext in
                    ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, filepath)

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
