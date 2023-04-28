import os

import bpy
from bpy_extras.io_utils import ExportHelper
from ..Utils.ErrorLog import ExportErrorLog
from .ExportSkel import extract_skel, create_bpy_to_dscs_bone_map
from .ExportGeom import extract_geom
from .ExportName import extract_name
from .ExportAnim import extract_base_anim, extract_anims, optimise_base_anim

class ExportMediaVision(bpy.types.Operator):
    multiple_material_policy: bpy.props.EnumProperty(
        items=[
            ("WARN",  "Warn",  "Log a warning if any meshes have more than one material"),
            ("ERROR", "Error", "Log an error if any meshes have more than one material, and display the erroneous meshes")
        ],
        name="Multiple Materials Policy",
        default="WARN"
    )
    
    partially_unrigged_mesh_policy: bpy.props.EnumProperty(
        items=[
            ("WARN",  "Warn",  "Log a warning if any meshes have mixed rigged and unrigged vertices"),
            ("ERROR", "Error", "Log an error if any meshes have mixed rigged and unrigged vertices"),
        ],
        name="Partially Unrigged Mesh Policy",
        default="WARN"
    )
    
    missing_weights_policy: bpy.props.EnumProperty(
        items=[
            ("STRIP", "Strip", "Strip vertex groups that do not have a corresponding bone"),
            ("ERROR", "Error", "Log an error if any meshes have vertex groups that do not have corresponding bones"),
        ],
        name="Missing Weights Policy",
        default="ERROR"
    )
    
    
    @ExportErrorLog.display_exceptions()
    def export_file(self, context):
        errorlog = ExportErrorLog(self.multiple_material_policy,
                                  self.partially_unrigged_mesh_policy,
                                  self.missing_weights_policy)
        bpy_to_dscs_bone_map = {}
        material_names = []
        
        # NEED TO CREATE A 'TRANSFORMS' OBJECT + INSTANCE THAT CAN BE DIRECTLY
        # USED BY THE TRANSFORMY ALGORITHMS
        
        # Get data required for extraction
        armature_obj = find_selected_model(errorlog)
        bpy_to_dscs_bone_map = create_bpy_to_dscs_bone_map(armature_obj)
        
        # Extract armature data and animations
        base_anim = extract_base_anim(armature_obj, errorlog, bpy_to_dscs_bone_map)
        si        = extract_skel(armature_obj, base_anim, errorlog, bpy_to_dscs_bone_map)
        optimise_base_anim(base_anim)
        anims     = extract_anims(armature_obj, errorlog, bpy_to_dscs_bone_map)
        
        # Extract geometry and names
        gi, image_extractors = extract_geom(armature_obj, errorlog, bpy_to_dscs_bone_map, material_names)
        ni        = extract_name(errorlog, bpy_to_dscs_bone_map, material_names)
        
        # Check if there were any errors generated during export
        errorlog.validate_error_data()
        errorlog.digest_errors()
        
        # If there were no errors, all this data should be guaranteed to be valid,
        # and therefore it should all successfully export
        ni.to_file(os.path.splitext(self.filepath)[0] + ".name")
        si.to_file(os.path.splitext(self.filepath)[0] + ".skel")
        gi.to_file(os.path.splitext(self.filepath)[0] + ".geom", self.model_type, invalidate_self_allowed=True)
        base_anim.to_file(os.path.splitext(self.filepath)[0] + ".anim", si, isBase=True)
        for track_name, ai in anims.items():
            ai.to_file(os.path.splitext(self.filepath)[0] + f"_{track_name}.anim", si, isBase=False)
        
        # Export textures
        base_dir = os.path.dirname(self.filepath)
        img_dir = os.path.join(base_dir, "images")
        os.makedirs(img_dir, exist_ok=True)
        for img_ex in image_extractors:
            img_ex.export(img_dir)
        
        # Check for hash collisions!!!
        if errorlog.has_warnings():
            errorlog.digest_warnings()
            self.report({"INFO"}, "Export successful, with warnings.")
        else:
            self.report({"INFO"}, "Export successful.")
    
    def execute(self, context):
        self.export_file(context)
        return {'FINISHED'}


class ExportDSCS(ExportMediaVision, ExportHelper):
    model_type = "DSCS_OpenGL"

    bl_idname = 'export_file.export_dscs'
    bl_label = 'Digimon Story: Cyber Sleuth (.name, .skel, .geom)'
    bl_options = {'REGISTER', 'UNDO'}
    # This will actually work with any file extension since the code just looks for the right ones...
    filename_ext = "*.name"

    #files: CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob: bpy.props.StringProperty(default="*.name", options={'HIDDEN'})


def find_selected_model(errorlog):
    # PUT IN CHECK HERE TO FOLLOW CONSTRAINT PARENTS
    # KEEP A MEMORY OF PARENTS TO DETECT AND AVOID CYCLES
    try:
        parent_obj = bpy.context.selected_objects[0]
    except IndexError:
        errorlog.log_error_message("You must select some part of the model you wish to export in Object Mode before attempting to export it. No model is currently selected.")
        return

    sel_obj = None
    while parent_obj is not None:
        sel_obj = parent_obj
        parent_obj = sel_obj.parent
    parent_obj = sel_obj
    if parent_obj.type != "ARMATURE":
        errorlog.log_error_message(f"An object is selected, but the top-level object \'{parent_obj.name}\' is not an Armature object - has type {parent_obj.type}.")
    return parent_obj
