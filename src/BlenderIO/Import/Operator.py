import os

import bpy
from bpy_extras.io_utils import ImportHelper

from ...filetypes.Name.Interface import NameFile
from ...filetypes.Skel.Interface import SkelFile
from ...filetypes.Geom.Interface import GeomFile
from ...filetypes.Anim.Interface import AnimFile

from .Data.Skeleton  import import_skeleton
from .Data.Material  import import_materials
from .Data.Meshes    import import_meshes
from .Data.Camera    import import_cameras
from .Data.Light     import import_lights
from .Data.Animation import import_base_animation
from .Data.Animation import import_animations

from ....external.blunger.interface.collection import init_collection
from ....external.blunger.dataproc.text import logged_decode
from ..Logging import ImportErrorLog
# from ..Preferences import get_preferences
from .Policies import ImportPoliciesGroup, ImportPoliciesArgs

from .ImportHundredLineGeom import import_hl_geom, import_hl_anim

def add_rest_pose_to_base_anim(si, gi, base_animation):
    for bone_idx, bone in enumerate(si.bones):
        if not len(base_animation.rotations[bone_idx]):
            base_animation.rotations[bone_idx][0] = bone.quat
        if not len(base_animation.positions[bone_idx]):
            base_animation.positions[bone_idx][0] = bone.pos
        if not len(base_animation.scales[bone_idx]):
            base_animation.scales[bone_idx][0] = bone.scale


class ImportMVGL(ImportPoliciesArgs, bpy.types.Operator):
    import_policies: bpy.props.PointerProperty(type=ImportPoliciesGroup)
    
    # def invoke(self, context, event):
    #     prefs = get_preferences()
    #     ImportPoliciesGroup.copy_between(prefs, self)
    #     return super().invoke(context, event)
    
    @ImportErrorLog.handle_exceptions()
    def import_file(self, context, filepath):
        self.import_policies.copy_from(self)
        errorlog = ImportErrorLog()
        
        bpy.ops.object.select_all(action='DESELECT')
        
        directory, model_name = os.path.split(os.path.splitext(os.path.abspath(filepath))[0])
        armature_name = model_name
        
        # Load files
        name = NameFile.from_file(os.path.join(directory, model_name + ".name"))
        skel = SkelFile.from_file(os.path.join(directory, model_name + ".skel"))
        gb = GeomFile.binary_type(self.model_type)()
        gb.read(os.path.join(directory, model_name + ".geom"))
        geom = GeomFile.from_binary(gb)

        bone_names     = [logged_decode(nm, "bone name",     errorlog, "utf8") for nm in name.bone_names]
        material_names = [logged_decode(nm, "material name", errorlog, "utf8") for nm in name.material_names]

        collection = init_collection(model_name)

        bpy_armature_object, dscs_to_bpy_bone_map = import_skeleton(collection, armature_name, bone_names, material_names, skel, geom, [2*d for d in gb.bounding_box_diagonal], errorlog)
        # DO MATERIAL IMPORT PROPERLY
        material_list = import_materials(material_names, geom, directory, errorlog, rename_imgs=False, use_custom_nodes=True)
        import_meshes(collection, model_name, bone_names, geom, bpy_armature_object, material_list, None, True)
        import_cameras(collection, bpy_armature_object, dscs_to_bpy_bone_map, geom)
        import_lights(collection, bpy_armature_object, dscs_to_bpy_bone_map, geom)
        
        base_anim = AnimFile.from_file(os.path.join(directory, model_name + ".anim"))
        # # Need to inject skeleton transforms into base animation.
        add_rest_pose_to_base_anim(skel, geom, base_anim)
        import_base_animation(model_name, bpy_armature_object, name.bone_names, base_anim, errorlog)
        
        # Temporary Animation Loading...
        self.load_animations(directory, model_name, bpy_armature_object, [b.name for b in bpy_armature_object.data.bones], errorlog)
    
    def execute(self, context):
        folder = (os.path.dirname(self.filepath))
        
        # iterate through the selected files
        self.import_file(context, self.filepath)

        return {'FINISHED'}

    def load_animations(self, directory, model_name, bpy_armature_object, bone_names, errorlog):
        if self.import_policies.import_anims:
            overlay_anims = {os.path.splitext(anim_name)[0] :
                AnimFile.from_file(os.path.join(directory, anim_name))
                for anim_name in 
                sorted([f for f in os.listdir(directory) 
                        if f.startswith(model_name + "_") 
                        and os.path.splitext(f)[1] == ".anim"])
            }
            import_animations(model_name, bpy_armature_object, bone_names, overlay_anims, errorlog)


class ImportDSCSOpenGL(ImportMVGL, ImportHelper):
    model_type = "DSCS_OpenGL"

    bl_idname = 'import_file.import_dscs_opengl'
    bl_label = 'Digimon Story: Cyber Sleuth [PC] (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.geom"

    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(
                                             default="*.geom",
                                             options={'HIDDEN'},
                                         )

    # import_anims: BoolProperty(
    #     name="Import Animations",
    #     description="Import animations or not."
    # )

    # merge_vertices: BoolProperty(
    #     name="Merge Vertices",
    #     description="Merge the OpenGL vertices (which look like duplicates in Blender) to Blender vertices.",
    #     default=True
    # )

    # img_to_dds: BoolProperty(
    #     name="Import IMG as DDS",
    #     description="Create a copy of each IMG file with a DDS extension before import."
    # )

    # use_custom_nodes: BoolProperty(
    #     name="Emulate DSCS Materials",
    #     description="Create a material node tree to partially emulate DSCS rendering.",
    #     default=True
    # )


class ImportDSCSPS(ImportMVGL, ImportHelper):
    model_type = "DSCS_PS"

    bl_idname = 'import_file.import_dscs_ps'
    bl_label = 'Digimon Story: Cyber Sleuth [PS4/Vita] (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.geom"

    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(
                                             default="*.geom",
                                             options={'HIDDEN'},
                                         )


class ImportMegido72(ImportMVGL, ImportHelper):
    model_type = "Megido72"

    bl_idname = 'import_file.import_megido72'
    bl_label = 'Megido 72 (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.geom"

    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(
                                             default="*.geom",
                                             options={'HIDDEN'},
                                         )




class ImportHundredLine(bpy.types.Operator, ImportHelper):
    model_type = "HundredLine"

    bl_idname = 'import_file.import_hundredline'
    bl_label = 'Hundred Line (.geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.geom"

    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(
                                             default="*.geom",
                                             options={'HIDDEN'},
                                         )


    
    # def invoke(self, context, event):
    #     prefs = get_preferences()
    #     ImportPoliciesGroup.copy_between(prefs, self)
    #     return super().invoke(context, event)
    
    @ImportErrorLog.handle_exceptions()
    def import_file(self, context, filepath):
        errorlog = ImportErrorLog()
        
        bpy.ops.object.select_all(action='DESELECT')
        
        directory, model_name = os.path.split(os.path.splitext(os.path.abspath(filepath))[0])
        armature_name = model_name
        
        import_hl_geom(filepath, errorlog)
        
    def execute(self, context):
        folder = (os.path.dirname(self.filepath))
        
        # iterate through the selected files
        self.import_file(context, self.filepath)

        return {'FINISHED'}

def fetch_armatures(self, context):
    armature_list = []
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            armature_list.append((obj.name, obj.name, obj.name, "OUTLINER_OB_ARMATURE", len(armature_list)))
    return tuple(armature_list)

def update_anim_filter(self, context):
    if self.filter_anims_by_model_name:
        filter_name = f"{self.armature_name}_*.anim"
        self.filter_glob = filter_name
        print(filter_name)
    else:
        self.filter_glob = "*.anim"

class ImportAnimBase(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = "*.anim"
    
    filter_glob: bpy.props.StringProperty(
                                             default="*.anim",
                                             options={'HIDDEN'},
                                         )
        
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    # filter_anims_by_model_name: bpy.props.BoolProperty(name="Filter Anims by Armature Name", default=True, update=update_anim_filter)
    armature_name: bpy.props.EnumProperty(items=fetch_armatures,
                                     name="Armature")


    # def invoke(self, context, event):
    #     # prefs = get_preferences()
    #     # ImportPoliciesGroup.copy_between(prefs, self)
    #     self.filter_anims_by_model_name = True # Set from prefs...
    #     return super().invoke(context, event)
        
    

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        # sfile = context.space_data
        # operator = sfile.active_operator
        # policies = operator.policies

        # layout.prop(self, "filter_anims_by_model_name")
        layout.prop(self, "armature_name")


    def find_selected_model(self, context):
        sel_obj = context.active_object
        if sel_obj is None:
            return None
        while sel_obj.parent is not None:
            sel_obj = sel_obj.parent
        if sel_obj.type == "ARMATURE":
            return sel_obj
        return None
        
    def execute(self, context):
        folder = (os.path.dirname(self.filepath))
        return self.import_file(context, bpy.data.objects[self.armature_name], [os.path.join(folder, f.name) for f in self.files])

    # This should be refactored to be more like the HundredLine importer -- import one animation at a time rather than in a big call
    @ImportErrorLog.handle_exceptions()
    def import_file(self, context, bpy_armature_object, filepaths):
        if bpy.context.view_layer.objects.active is not None:        
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        # Try to load file and log any errors...
        errorlog = ImportErrorLog()            
        if self.armature_name is None:
            errorlog.log_error_message("No armatures exist in the scene. Animations cannot be imported")
        
        # Report an error if there's no armature
        if len(errorlog.errors):
            errorlog.digest_errors(False)
            return {'CANCELLED'}

        anims = {os.path.splitext(os.path.split(filepath)[1])[0]: AnimFile.from_file(filepath) for filepath in filepaths}
        bone_names = [b.name for b in bpy_armature_object.data.bones]
        import_animations(bpy_armature_object.name, bpy_armature_object, bone_names, anims, errorlog)
        
        # Report any warnings that were logged
        errorlog.digest_errors(False)
        
        if len(errorlog.warnings):
            errorlog.digest_warnings(False)
            self.report({"INFO"}, "Import successful, with warnings.")
        else:
            self.report({"INFO"}, "Import successful.")
        
        return {'FINISHED'}

class ImportDSCSAnim(ImportAnimBase, ImportHelper):
    bl_idname = "import_file.import_dscsanim"
    bl_label = "DSCS Animation (.anim)"


class ImportMegido72Anim(ImportAnimBase, ImportHelper):
    bl_idname = "import_file.import_megido72anim"
    bl_label = "Megido72 Animation (.anim)"


class ImportHundredLineAnim(ImportAnimBase, ImportHelper):
    bl_idname = "import_file.import_hundredlineanim"
    bl_label = "HundredLine (.anim)"


    @ImportErrorLog.handle_exceptions()
    def import_file(self, context, bpy_armature_object, filepaths):
        if bpy.context.view_layer.objects.active is not None:        
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        # Try to load file and log any errors...
        errorlog = ImportErrorLog()            
        if self.armature_name is None:
            errorlog.log_error_message("No armatures exist in the scene. Animations cannot be imported")
        
        # Report an error if there's no armature
        if len(errorlog.errors):
            errorlog.digest_errors(False)
            return {'CANCELLED'}

        for filepath in filepaths:
            import_hl_anim(bpy_armature_object, filepath, errorlog)
        
        # Report any warnings that were logged
        errorlog.digest_errors(False)
        
        if len(errorlog.warnings):
            errorlog.digest_warnings(False)
            self.report({"INFO"}, "Import successful, with warnings.")
        else:
            self.report({"INFO"}, "Import successful.")
        
        return {'FINISHED'}
