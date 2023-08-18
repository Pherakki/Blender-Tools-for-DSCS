import numpy as np
import bpy
from mathutils import Matrix



class OBJECT_OT_ConvertToBoxCollider(bpy.types.Operator):
    bl_label = "Convert to Box Collider"
    bl_idname = "import_dscs.OBJECT_OT_ConvertToBoxCollider".lower()
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        mesh = context.mesh
        props = mesh.DSCS_MeshProperties
        obj  = context.object
        cprops = obj.DSCS_ColliderProperties
        
        # Generate mesh
        dims, centre, orientation = self.create_bounding_box(obj, [0, 1])
        cprops.box_props["height"] = dims[0]
        cprops.box_props["depth" ] = dims[1]
        cprops.box_props["width" ] = dims[2]
        cprops.collider_type = "BOX"
        props.mesh_type = "COLLIDER"
        cprops.box_props.rebuild_mesh()
        
        # Shift object
        rmode = obj.rotation_mode
        if rmode not in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']:
            rmode = "XYZ"

        orientation = Matrix(orientation)
        euler = Matrix(orientation).to_euler('XYZ')
        euler[0] *= -1
        for i in range(len(centre)):
            obj.location[i] = centre[i]
        obj.rotation_euler = euler.to_matrix().to_euler(rmode)
        obj.rotation_quaternion = obj.rotation_euler.to_quaternion()
        obj.scale = [1., 1., 1.]

        return {'FINISHED'}

    def create_bounding_box(self, obj, plane):
        # Get vertex cloud relative to object parent
        mesh = obj.data
        transform = np.array(obj.matrix_local)
        vertices = transform @ np.array([(*v.co, 1) for v in mesh.vertices]).T
        
        # Find principal axes of the vertex cloud
        cov = np.cov(vertices[plane])
        eigval, eigvec = np.linalg.eig(cov)

        # Generate full rotation matrix from planar principal axes
        orientation = np.eye(3)
        for e_idx, o_idx in enumerate(plane):
            for e_idx2, o_idx2 in enumerate(plane):
                orientation[o_idx, o_idx2] = eigvec[e_idx, e_idx2]
        
        # Align verts to our reference frame and measure width/height range
        aligned_verts = orientation.T @ (vertices[:3])
        southwest_corner = np.min(aligned_verts,axis=1)
        northeast_corner = np.max(aligned_verts,axis=1)
        
        # Get box dims
        dims   = (northeast_corner - southwest_corner)
        centre = orientation @ ((northeast_corner + southwest_corner)/2)

        
        return dims, centre, orientation


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
                layout.operator(OBJECT_OT_ConvertToComplexCollider.bl_idname)
            elif cprops.collider_type == "COMPLEX":
                layout.operator(OBJECT_OT_ConvertToBoxCollider.bl_idname)
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
