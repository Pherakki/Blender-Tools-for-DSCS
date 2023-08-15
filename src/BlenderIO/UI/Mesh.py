import bpy


class OBJECT_PT_DSCSMeshPanel(bpy.types.Panel):
    bl_label       = "DSCS Mesh"
    bl_idname      = "OBJECT_PT_DSCSMeshPanel"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"
    bl_options     = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        return context.mesh is not None

    def draw(self, context):
        mesh = context.mesh
        obj  = context.object
        layout = self.layout
        props = mesh.DSCS_MeshProperties
        
        layout.prop(props, "mesh_type")
        if props.mesh_type == "MESH":
            layout.prop(props, "name_hash")
            
            layout.prop(props, "is_rendered")
            layout.prop(props, "is_wireframe")
            layout.prop(props, "flag_3")
            layout.prop(props, "flag_4")
            layout.prop(props, "flag_5")
            layout.prop(props, "flag_6")
            layout.prop(props, "flag_7")
        elif props.mesh_type == "COLLIDER":
            obj.DSCS_ColliderProperties.display(obj.DSCS_ColliderProperties, layout)
