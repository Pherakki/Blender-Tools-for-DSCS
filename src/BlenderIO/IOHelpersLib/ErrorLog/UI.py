import bpy

from ..Utils.TextWrapping import wrapText

subnamespace = "iohelperslib"

def ErrorBoxBase(namespace, plugin_name):
    class ErrorBoxBaseImpl(bpy.types.Operator):
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
    
            msg_lines = wrapText(self.message, 96)
            for line in msg_lines:
                col.label(text=line)
    return ErrorBoxBaseImpl

            
def WarningBoxBase(namespace, plugin_name):
    class WarningBoxBaseImpl(bpy.types.Operator):
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
    
            msg_lines = wrapText(self.message, 96)
            for line in msg_lines:
                col.label(text=line)
    return WarningBoxBaseImpl


def UnhandledBoxBase(namespace, plugin_name, generate_unhandled_error_message):
    class UnhandledBoxBaseImpl(bpy.types.Operator):
        bl_idname  = f"{namespace}_{subnamespace}.unhandlederrorbox"
        bl_label   = f"{plugin_name}: Unhandled Error Detected"
        bl_options = {'REGISTER'}
        
        exception_msg: bpy.props.StringProperty()
        context_msg:   bpy.props.StringProperty()
    
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
    
            msg_lines = wrapText(generate_unhandled_error_message(self.exception_msg, self.context_msg), 96)
            for line in msg_lines:
                col.label(text=line)
    return UnhandledBoxBaseImpl
