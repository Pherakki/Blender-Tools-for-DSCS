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
from .CameraImport   import import_cameras
from .LightImport    import import_lights
from .MaterialImport import import_materials
from .MeshImport import import_meshes
from .AnimationImport import import_base_animation, import_animations
from ..IOHelpersLib.Collection import init_collection
from ..Utils.ErrorLog import ImportErrorLog


class ImportMediaVision(bpy.types.Operator):
    platform = None
    import_anims = None
    img_to_dds = None
    use_custom_nodes = None
    merge_vertices = None

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    @ImportErrorLog.display_exceptions()
    def import_file(self, context, filepath):
        errorlog = ImportErrorLog()
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
        collection = init_collection(model_name)
        armature_obj, dscs_to_bpy_bone_map = import_skeleton(collection, armature_name, ni, si, gi, [2* d for d in gb.bounding_box_diagonal])
        material_list = import_materials(ni, gi, directory, self.img_to_dds, self.use_custom_nodes)
        import_meshes(collection, model_name, ni, gi, armature_obj, material_list, errorlog, self.merge_vertices)
        import_cameras(collection, armature_obj, dscs_to_bpy_bone_map, gi)
        import_lights(collection, armature_obj, dscs_to_bpy_bone_map, gi)
        if gi.extra_clut is not None:
            armature_obj.data.DSCS_ModelProperties.extra_clut = gi.extra_clut.hex()
            
        # Animations
        base_anim = AnimInterface.from_file(os.path.join(directory, model_name + ".anim"), si)
        ais = {}
        for f in sorted([file for file in os.listdir(directory) if file.endswith(os.path.extsep + "anim")]):
            anim_name = f.rsplit('.')[0]
            anim_root = anim_name.rsplit("_")[0]
            if anim_root == model_name:  
                ai = AnimInterface.from_file(os.path.join(directory, f), si)
                if anim_name == model_name:
                else:
                    ais[anim_name] = ai
        add_rest_pose_to_base_anim(si, gi, base_anim)
        import_base_animation(directory, model_name, armature_obj, ni, base_anim)
        import_animations(directory, model_name, armature_obj, ni, ais)

        armature_obj.animation_data.nla_tracks["base"].mute = False

        # Finalise
        bpy.ops.object.mode_set(mode="OBJECT")


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
