import bpy

from ...operator import get_op
from ....dataproc.text import wrap_text

subnamespace = "blunger"

def ErrorBoxBase(namespace, plugin_name):
    class ErrorBoxBaseImpl:
        bl_idname  = f"{namespace}_{subnamespace}.basicerrorbox"
        bl_label   = f"{plugin_name}: Errors Detected"
        bl_options = {'REGISTER'}
        
        message: bpy.props.StringProperty()
    
        @classmethod
        def poll(cls, context):
            return True
    
        def execute(self, context):
            return {'FINISHED'}
    
        def invoke(self, context, event):
            return context.window_manager.invoke_props_dialog(self, width=512)
    
        def check(self, context):
            """Allows the dialog to redraw"""
            return True
    
        def draw(self, context):
            layout = self.layout
    
            col = layout.column()
            col.scale_y = 0.6
    
            for submsg in self.message.split('\n'):
                col.separator(factor=0.2)
                msg_lines = wrap_text(submsg, 96)
                for line in msg_lines:
                    col.label(text=line)
        
        @classmethod
        def create_instance(cls, message, **kwargs):
            op = get_op(cls)
            op('INVOKE_DEFAULT', message=message, **kwargs)
        
    return ErrorBoxBaseImpl

            
def WarningBoxBase(namespace, plugin_name):
    class WarningBoxBaseImpl:
        bl_idname  = f"{namespace}_{subnamespace}.basicwarningbox"
        bl_label   = f"{plugin_name}: Warnings Detected"
        bl_options = {'REGISTER'}
        
        message: bpy.props.StringProperty()
    
        @classmethod
        def poll(cls, context):
            return True
    
        def execute(self, context):
            return {'FINISHED'}
    
        def invoke(self, context, event):
            return context.window_manager.invoke_props_dialog(self, width=512)
    
        def check(self, context):
            """Allows the dialog to redraw"""
            return True
    
        def draw(self, context):
            layout = self.layout
    
            col = layout.column()
            col.scale_y = 0.6
    
            for submsg in self.message.split('\n'):
                col.separator(factor=0.2)
                msg_lines = wrap_text(submsg, 96)
                for line in msg_lines:
                    col.label(text=line)
        
        @classmethod
        def create_instance(cls, message, **kwargs):
            op = get_op(cls)
            op('INVOKE_DEFAULT', message=message, **kwargs)
            
    return WarningBoxBaseImpl


def UnhandledBoxBase(namespace, plugin_name):
    class UnhandledBoxBaseImpl:
        bl_idname  = f"{namespace}_{subnamespace}.unhandlederrorbox"
        bl_label   = f"{plugin_name}: Unhandled Error Detected"
        bl_options = {'REGISTER'}
        
        exception_message: bpy.props.StringProperty()
    
        @classmethod
        def poll(cls, context):
            return True
    
        def execute(self, context):
            return {'FINISHED'}
    
        def invoke(self, context, event):
            return context.window_manager.invoke_props_dialog(self, width=512)
    
        def check(self, context):
            """Allows the dialog to redraw"""
            return True
    
        def draw(self, context):
            layout = self.layout
    
            col = layout.column()
            col.scale_y = 0.6
    
            submessages = self.get_error_message(context, exception_message=self.exception_message).split('\n')
            for submsg in submessages:
                col.separator(factor=0.2)
                msg_lines = wrap_text(submsg, 96)
                
                for line in msg_lines:
                    col.label(text=line)
        
        def get_error_message(self, context, exception_message):
            return f"An unhandled error occurred. The exception is\n{exception_message}\nThe full stacktrace has been printed to the console."
        
        @classmethod
        def create_instance(cls, exception_message, **kwargs):
            op = get_op(cls)
            op('INVOKE_DEFAULT', exception_message=exception_message, **kwargs)
        
    return UnhandledBoxBaseImpl

