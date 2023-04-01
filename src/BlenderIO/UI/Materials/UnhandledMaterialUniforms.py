import bpy


class OBJECT_UL_DSCSMaterialUniformUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.split(factor=0.05)
        split.separator()
        split.prop(item, "index")
        split.prop(item, "dtype")
        if item.dtype == "FLOAT32":
            split.prop(item, "float32_data")
        elif item.dtype == "FLOAT32VEC3":
            split.prop(item, "float32vec3_data")
        elif item.dtype == "FLOAT32VEC2":
            split.prop(item, "float32vec2_data")
        elif item.dtype == "FLOAT32VEC4":
            split.prop(item, "float32vec4_data")
        elif item.dtype == "TEXTURE":
            col = split.column()
            col.prop(item.texture_data, "image", text="")
            col.prop(item.texture_data, "data", text="")


def makeCustomPropertiesPanel(parent_id, identifier, space_type, region_type, context, props_getter, poll_func):
    class PropertyPanel(bpy.types.Panel):
        bl_label       = "Extra Uniforms"
        bl_parent_id   = parent_id
        bl_space_type  = space_type
        bl_region_type = region_type
        bl_context     = context

        @classmethod
        def poll(cls, context):
            return poll_func(cls, context)
    
        def draw(self, context):
            layout = self.layout
    
            obj = props_getter(context)
            row = layout.row()
            row.template_list(OBJECT_UL_DSCSMaterialUniformUIList.__name__, "", obj, "unhandled_uniforms", obj, "active_unhandled_uniform_idx")

            col = row.column(align=True)
            col.operator(type(self).AddOperator.bl_idname, icon='ADD',    text="")
            col.operator(type(self).DelOperator.bl_idname, icon='REMOVE', text="")
            col.separator()
            col.operator(type(self).MoveUpOperator.bl_idname,   icon='TRIA_UP',   text="")
            col.operator(type(self).MoveDownOperator.bl_idname, icon='TRIA_DOWN', text="")
    
        @classmethod
        def register(cls):
            bpy.utils.register_class(cls.AddOperator)
            bpy.utils.register_class(cls.DelOperator)
            bpy.utils.register_class(cls.MoveUpOperator)
            bpy.utils.register_class(cls.MoveDownOperator)
    
        @classmethod
        def unregister(cls):
            bpy.utils.unregister_class(cls.AddOperator)
            bpy.utils.unregister_class(cls.DelOperator)
            bpy.utils.unregister_class(cls.MoveUpOperator)
            bpy.utils.unregister_class(cls.MoveDownOperator)

        class AddOperator(bpy.types.Operator):
            bl_idname = f"import_dscs.OBJECT_OT_{identifier}PanelAdd".lower()
            
            bl_label       = "Add Item"
            bl_description = "Adds a new Uniform to the Property List."
            bl_options     = {'REGISTER'}   
              
            def invoke(self, context, event):
                obj = props_getter(context)
                obj.active_unhandled_uniform_idx.add()
                obj.active_unhandled_uniform_idx = len(obj.unhandled_uniforms) - 1
                return {'FINISHED'}
        
        
        class DelOperator(bpy.types.Operator):
            bl_idname = f"import_dscs.OBJECT_OT_{identifier}PanelDel".lower()
            
            bl_label       = "Delete Item"
            bl_description = "Removes the selected Uniform from the Property List."
            bl_options     = {'REGISTER'}   
              
            def invoke(self, context, event):
                obj = props_getter(context)
                obj.active_unhandled_uniform_idx.remove(obj.active_unhandled_uniform_idx)
                obj.active_property_idx -= 1
                return {'FINISHED'}
        
        
        class MoveUpOperator(bpy.types.Operator):
            bl_idname = f"import_dscs.OBJECT_OT_{identifier}PanelMoveUp".lower()
            
            bl_label       = "Move Item Up"
            bl_description = "Moves the selected Uniform up in the Property List."
            bl_options     = {'REGISTER'}   
              
            def invoke(self, context, event):
                obj = props_getter(context)
                if obj.active_unhandled_uniform_idx > 0:
                    new_idx = obj.active_unhandled_uniform_idx - 1
                    obj.unhandled_uniforms.move(obj.active_unhandled_uniform_idx, new_idx)
                    obj.active_unhandled_uniform_idx = new_idx
                return {'FINISHED'}
        
        
        class MoveDownOperator(bpy.types.Operator):
            bl_idname = f"import_dscs.OBJECT_OT_{identifier}PanelMoveDown".lower()
            
            bl_label       = "Move Item Down"
            bl_description = "Moves the selected Uniform down in the Property List."
            bl_options     = {'REGISTER'}   
              
            def invoke(self, context, event):
                obj = props_getter(context)
                if obj.active_unhandled_uniform_idx < (len(obj.unhandled_uniforms) - 1):
                    new_idx = obj.active_unhandled_uniform_idx + 1
                    obj.unhandled_uniforms.move(obj.active_unhandled_uniform_idx, new_idx)
                    obj.active_unhandled_uniform_idx = new_idx
                return {'FINISHED'}
    
    PropertyPanel.__name__                  = f"OBJECT_PT_DSCSMaterial{identifier}Panel"
    PropertyPanel.AddOperator.__name__      = PropertyPanel.AddOperator.bl_idname
    PropertyPanel.DelOperator.__name__      = PropertyPanel.DelOperator.bl_idname
    PropertyPanel.MoveUpOperator.__name__   = PropertyPanel.MoveUpOperator.bl_idname
    PropertyPanel.MoveDownOperator.__name__ = PropertyPanel.MoveDownOperator.bl_idname
    return PropertyPanel

OBJECT_PT_DSCSMaterialUnhandledUniformsPanel = makeCustomPropertiesPanel("OBJECT_PT_DSCSMaterialPanel", "UnhandledUniforms", "PROPERTIES", "WINDOW", "material", lambda x: x.material.DSCS_MaterialProperties, lambda self, x: x.material is not None)
