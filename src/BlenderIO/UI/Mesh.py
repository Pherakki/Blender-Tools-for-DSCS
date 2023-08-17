import bpy



class OBJECT_OT_ConvertToBoxCollider(bpy.types.Operator):
    bl_label = "Convert to Box Collider"
    bl_idname = "import_dscs.OBJECT_OT_ConvertToBoxCollider".lower()
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        mesh = context.mesh
        props = mesh.DSCS_MeshProperties
        obj  = context.object
        cprops = obj.DSCS_ColliderProperties
        
        cprops.box_props.height = obj.bound_box[4][0] - obj.bound_box[0][0]
        cprops.box_props.depth  = obj.bound_box[2][1] - obj.bound_box[0][1]
        cprops.box_props.width  = obj.bound_box[1][2] - obj.bound_box[0][2]
        cprops.collider_type = "BOX"
        props.mesh_type = "COLLIDER"
        
        return {'FINISHED'}

class OBJECT_OT_ConvertToComplexCollider(bpy.types.Operator):
    bl_label = "Convert to Complex Collider"
    bl_idname = "import_dscs.OBJECT_OT_ConvertToComplexCollider".lower()
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        mesh = context.mesh
        props = mesh.DSCS_MeshProperties
        obj  = context.object
        cprops = obj.DSCS_ColliderProperties
        
        cprops.collider_type = "COMPLEX"
        props.mesh_type = "COLLIDER"
        
        return {'FINISHED'}


class OBJECT_OT_ConvertToMesh(bpy.types.Operator):
    bl_label = "Convert to Mesh"
    bl_idname = "import_dscs.OBJECT_OT_ConvertToMesh".lower()
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        mesh = context.mesh
        props = mesh.DSCS_MeshProperties
        props.mesh_type = "MESH"
        
        return {'FINISHED'}


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
        
        if props.mesh_type == "MESH":
            layout.operator(OBJECT_OT_ConvertToBoxCollider.bl_idname)
            layout.operator(OBJECT_OT_ConvertToComplexCollider.bl_idname)
            
            layout.prop(props, "name_hash")
            
            layout.prop(props, "is_rendered")
            layout.prop(props, "is_wireframe")
            layout.prop(props, "flag_3")
            layout.prop(props, "flag_4")
            layout.prop(props, "flag_5")
            layout.prop(props, "flag_6")
            layout.prop(props, "flag_7")
        elif props.mesh_type == "COLLIDER":
            layout.operator(OBJECT_OT_ConvertToMesh.bl_idname)
            cprops = obj.DSCS_ColliderProperties
            if cprops.collider_type == "BOX":
                layout.operator(OBJECT_OT_ConvertToComplexCollider)
            elif cprops.collider_type == "COMPLEX":
                layout.operator(OBJECT_OT_ConvertToBoxCollider)
            cprops.display(cprops, layout)
            
    @classmethod
    def register(self):
        bpy.utils.register_class(OBJECT_OT_ConvertToBoxCollider)
        bpy.utils.register_class(OBJECT_OT_ConvertToComplexCollider)
        bpy.utils.register_class(OBJECT_OT_ConvertToMesh)
            
    @classmethod
    def unregister(self):
        bpy.utils.unregister_class(OBJECT_OT_ConvertToBoxCollider)
        bpy.utils.unregister_class(OBJECT_OT_ConvertToComplexCollider)
        bpy.utils.unregister_class(OBJECT_OT_ConvertToMesh)
