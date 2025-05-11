import bpy

from ...external.blunger.interface.logging import ErrorLogBase
from ...external.blunger.interface.logging import UnhandledBoxBase
from .Globals import NAMESPACE


def create_unhandled_error_msg(exception_msg, context_msg):
    return f"BlenderToolsForDSCS has encountered an unhandled error. The exception is:\n\n"           \
    f"{exception_msg}\n\n"                                                                            \
    f"A full stacktrace has been printed to the console.\n"                                           \
    f"Since all exceptions should be handled by the internal error-reporting system, "                \
    f"this is a bug. Please report this at https://github.com/Pherakki/Blender-Tools-For-DSCS/issues" \
    f"using the 'Bug Report' template, with the following information:\n"                             \
    f"1) {context_msg}\n"                                                                             \
    f"2) The stacktrace that has been printed to the console.\n"                                      \
    f"3) Any further information that you think may be relevant."


class DSCSUnhandledErrorBox(UnhandledBoxBase(NAMESPACE, "BlenderToolsForDSCS")):
    context_message: bpy.props.StringProperty()
    
    def get_error_message(self, context, exception_message):
        return create_unhandled_error_msg(exception_message, self.context_message)


BaseClass = ErrorLogBase(NAMESPACE, "BlenderToolsForDSCS", UnhandledBox=DSCSUnhandledErrorBox)


class ImportErrorLog(BaseClass):
    def __init__(self):
        super().__init__()
        ...

    def validate_error_data(self):
        ...
    
    @classmethod
    def handle_exceptions(cls):
        return super().handle_exceptions(context_message="The filename if you are importing a vanilla file. Otherwise, an upload of the custom data that fails to import.")


class ExportErrorLog(BaseClass):
    def __init__(self, multiple_material_policy,
                 partially_unrigged_mesh_policy,
                 missing_weights_policy):
        super().__init__()
        
        #self.missing_material_policy   = None
        self.missing_material_meshes   = []
        
        self.multiple_material_policy       = multiple_material_policy
        self.multiple_materials_meshes      = []
        
        self.partially_unrigged_mesh_policy = partially_unrigged_mesh_policy
        self.missing_weights_policy         = missing_weights_policy
        
        self.vweight_floor = 0.
        
        

    # def validate_error_data(self):
    #     # Only other policy could be to export with a default material...
    #     if len(self.missing_material_meshes):
    #         self.log_error_object(MissingMaterialsError(self.missing_material_meshes))
        
    #     if len(self.multiple_materials_meshes):
    #         err = MultipleMaterialsError(self.multiple_materials_meshes)
    #         if self.multiple_material_policy == "WARN":
    #             self.log_warning_message(err.warning_message())
    #         elif self.multiple_material_policy == "ERROR":
    #             self.log_error_object(err)
    #         # AUTOSPLIT option - split mesh faces by material index
    #         else:
    #             raise NotImplementedError(f"Unknown multiple material policy '{self.multiple_material_policy}'")

    @classmethod
    def display_exceptions(cls):
        return super().display_exceptions(context_message="The filename if you are exporting an unedited vanilla file. Otherwise, an upload of the .blend file you are trying to export.")
