import math
import os

import bpy
from bpy.props import BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from. ..Core.FileFormats.Name.NameInterface import NameInterface
from ...Core.FileFormats.Skel.SkelInterface import SkelInterface
from ...Core.FileFormats.Geom.GeomInterface import GeomInterface
from ...Core.FileFormats.Anim.AnimInterface import AnimInterface
from .ArmatureImport import import_skeleton
from .MaterialImport import import_materials
from .MeshImport import import_meshes
from .AnimationImport import import_base_animation, import_animations


class ImportMediaVision(bpy.types.Operator):
    platform = None
    import_anims = None
    img_to_dds = None
    use_custom_nodes = None
    merge_vertices = None

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def import_file(self, context, filepath):
        bpy.ops.object.select_all(action='DESELECT')

        directory, model_name = os.path.split(os.path.splitext(os.path.abspath(filepath))[0])
        armature_name = model_name

        # Load files
        ni = NameInterface.from_file(os.path.join(directory, model_name + ".name"))
        si = SkelInterface.from_file(os.path.join(directory, model_name + ".skel"))
        gb = GeomInterface.binary_type(self.model_type)()
        gb.read(os.path.join(directory, model_name + ".geom"))
        gi = GeomInterface.from_binary(gb)

        # Import data
        armature = import_skeleton(armature_name, ni, si, gi, [2* d for d in gb.bounding_box_diagonal])
        material_list = import_materials(ni, gi, directory, self.img_to_dds, self.use_custom_nodes)
        import_meshes(model_name, ni, gi, armature, material_list, self.merge_vertices)
        # # import_cameras(parent_obj, model_data)
        # # import_lights(parent_obj, model_data)

        # Animations
        base_anim = None
        ais = {}
        for f in sorted([file for file in os.listdir(directory) if file.endswith(os.path.extsep + "anim")]):
            anim_name = f.rsplit('.')[0]
            anim_root = anim_name.rsplit("_")[0]
            
            if anim_root == model_name:  
                ai = AnimInterface.from_file(os.path.join(directory, f), si)
                if anim_name == model_name:
                    base_anim = ai
                else:
                    ais[anim_name] = ai

        add_rest_pose_to_base_anim(si, gi, base_anim)
        import_base_animation(directory, model_name, armature, ni, base_anim)
        import_animations(directory, model_name, armature, ni, ais)

        armature.animation_data.nla_tracks["base"].mute = False

        bpy.ops.object.mode_set(mode="OBJECT")



    #@handle_errors
    def execute(self, context):
        folder = (os.path.dirname(self.filepath))

        # # iterate through the selected files
        # for file in self.files:
        #     path_to_file = (os.path.join(folder, file.name))
        #     filepath, file_extension = os.path.splitext(path_to_file)
        #     assert any([file_extension == ext for ext in
        #                 ('.name', '.skel', '.geom')]), f"Extension is {file_extension}: Not a name, skel or geom file!"
        self.import_file(context, self.filepath)

        return {'FINISHED'}

# from mathutils import Matrix, Quaternion
def add_rest_pose_to_base_anim(si, gi, base_animation):
    for bone_idx, bone in enumerate(si.bones):
        if not len(base_animation.rotations[bone_idx]):
            base_animation.rotations[bone_idx][0] = bone.quat
        if not len(base_animation.locations[bone_idx]):
            base_animation.locations[bone_idx][0] = bone.pos
        if not len(base_animation.scales[bone_idx]):
            base_animation.scales[bone_idx][0] = bone.scale


class ImportDSCS(ImportMediaVision, ImportHelper):
    model_type = "DSCS_OpenGL"

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

    img_to_dds: BoolProperty(
        name="Import IMG as DDS",
        description="Create a copy of each IMG file with a DDS extension before import."
    )

    use_custom_nodes: BoolProperty(
        name="Emulate DSCS Materials",
        description="Create a material node tree to partially emulate DSCS rendering.",
        default=True
    )