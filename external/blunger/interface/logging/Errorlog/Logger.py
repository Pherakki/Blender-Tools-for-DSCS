import functools
import traceback

import bpy

from ....dataproc.text import wrap_text
from .Warnings import ReportableError
from .UI import ErrorBoxBase
from .UI import WarningBoxBase
from .UI import UnhandledBoxBase


def ErrorLogBase(namespace, plugin_name, WarningBox=None, ErrorBox=None, UnhandledBox=None):
    # Define error report popups
    WarningBoxBaseClass   = WarningBoxBase  (namespace, plugin_name) if WarningBox   is None else WarningBox
    ErrorBoxBaseClass     = ErrorBoxBase    (namespace, plugin_name) if ErrorBox     is None else ErrorBox
    UnhandledBoxBaseClass = UnhandledBoxBase(namespace, plugin_name) if UnhandledBox is None else UnhandledBox
    
    class ErrorLog:
        # Finalize UI classes by inheriting from Operator here.
        # This allows users to add more bpy properties onto custom
        # implementations of these classes without the original ones being
        # dropped.
        class _popup_warningbox(WarningBoxBaseClass,   bpy.types.Operator): pass
        class _popup_errorbox  (ErrorBoxBaseClass,     bpy.types.Operator): pass
        class _popup_unhandled (UnhandledBoxBaseClass, bpy.types.Operator): pass
        
        def __init__(self):
            self._errors   = []
            self._warnings = []

        #############
        # STATE API #
        #############
        def clear(self):
            self._errors.clear()
            self._warnings.clear()

        ################
        # WARNINGS API #
        ################
        def has_warnings(self):
            return len(self._warnings) > 0
          
        @property
        def warnings(self):
            return self._warnings
        
        def log_warning_message(self, message):
            """Used to create a generic warning message from a string."""
            self._warnings.append(ReportableError(message))
            
        def log_warning_object(self, warning):
            """Used to create a specialised warning message using a class derived from ErrorLog.BaseError."""
            if not(hasattr(warning, "msg") and hasattr(warning, "HAS_DISPLAYABLE_ERROR")):
                raise ValueError(f"Logged warning must be a class with a member 'msg' and class member 'HAS_DISPLAYABLE_ERROR', received '{type(warning)}'. Use log_warning_message for string-like warning messages")
            self._warnings.append(warning)
            
        def digest_warnings(self, debug_mode=False):
            """Launch warning window if any warnings exist, and clear warning list."""
            # This is wrong but can't do anything better for now.
            # Ideally should load all errors into a single popup with multiple
            # pages.
            if len(self.warnings):
                lines = []
                for i, warning in enumerate(self.warnings):
                    warning_text = f"{i+1}) {warning.msg}"
                    current_warning = wrap_text(warning_text, 80)
                    if len(lines) + len(current_warning) < 15:
                        lines.append(warning_text)
                        print(warning.msg)
                    else:
                        lines.append(f"Plus {len(self.warnings) - i} additional warnings. Check the console for details.")
                        for warning in self.warnings[i:]:
                            print(warning.msg)
                        break
                
                self._popup_warningbox.create_instance('\n'.join(lines))
            self.warnings.clear()
        
        ##############
        # ERRORS API #
        ##############
        def has_errors(self):
            return len(self._errors) > 0
            
        @property
        def errors(self):
            return self._errors

        def log_error_message(self, message):
            """Used to create a generic error message from a string."""
            self._errors.append(ReportableError(message))
    
        def log_error_object(self, error):
            """Used to create a specialised error message using a class derived from ErrorLog.BaseError."""
            assert hasattr(error, "msg") and hasattr(error, "HAS_DISPLAYABLE_ERROR"), f"Logged error must be a class with a member 'msg' and class member 'HAS_DISPLAYABLE_ERROR', received '{type(error)}'. Use log_error_message for string-like error messages"
            self._errors.append(error)
            
        def digest_errors(self, debug_mode=False):
            """Launch error window if any errors exist, and clear error list."""
            # This is wrong but can't do anything better for now.
            # Ideally should load all errors into a single popup with multiple
            # pages.
            if len(self.errors):
                if debug_mode:
                    raise Exception(self.errors[0].msg)
                err = self.errors[0]
                if err.HAS_DISPLAYABLE_ERROR:
                    err.showErrorData()
            
                msg = f"({len(self.errors)}) error(s) were detected when trying to export. The first error is:"
                msg += "\n" + err.msg
                if err.HAS_DISPLAYABLE_ERROR:
                    msg += "\n" + "The relevant data has been selected for you."
                self._popup_errorbox.create_instance(msg)
            self.errors.clear()
    
        #########################
        # CONVENIENCE UTILITIES #
        #########################
        # Having these utils here keeps everything under a single namespace,
        # making the errorlog much easier to use.
        @property
        def BaseError(self):
            return ReportableError
        
        # Decorator for root-level operators that use the errorlog.
        @classmethod
        def handle_exceptions(cls, debug_condition=None, **popup_kwargs):
            def impl(function):
                @functools.wraps(function)
                def handled_execute(self, *args, **kwargs):
                    try:
                        return function(self, *args, **kwargs)
                    except Exception as e:
                        if debug_condition is not None and debug_condition(self):
                            raise e
                        else:
                            print(''.join(traceback.TracebackException.from_exception(e).format()))
                            cls._popup_unhandled.create_instance(str(e), **popup_kwargs)
                            return {"CANCELLED"}
                return handled_execute
            return impl
        
        #################
        # BPY UTILITIES #
        #################      
        # Registry functions so that *only* the errorlog needs to be registered
        # with bpy for the entire errorlog to work.
        
        @classmethod
        def register(cls):
            bpy.utils.register_class(cls._popup_warningbox)
            bpy.utils.register_class(cls._popup_errorbox)
            bpy.utils.register_class(cls._popup_unhandled)
        
        @classmethod
        def unregister(cls):
            bpy.utils.unregister_class(cls._popup_warningbox)
            bpy.utils.unregister_class(cls._popup_errorbox)
            bpy.utils.unregister_class(cls._popup_unhandled)

    return ErrorLog

