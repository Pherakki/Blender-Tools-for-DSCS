import struct
import bpy

def flags_getter(self):
    v = 0
    v |= self.is_rendered  << 0
    v |= self.is_wireframe << 1
    #v |= self.flag_2 << 2
    v |= self.flag_3       << 3
    v |= self.flag_4       << 4
    v |= self.flag_5       << 5
    v |= self.flag_6       << 6
    v |= self.flag_7       << 7
    return v

def force_ui_redraw(self, context):
    for region in context.area.regions:
        if region.type == "UI":
            region.tag_redraw()
    return None

class MeshProperties(bpy.types.PropertyGroup):
    mesh_type: bpy.props.EnumProperty(items=[
        ("MESH", "Mesh", "Mesh"),
        ("COLLIDER", "Collider", "Collider")
    ], name="Type", update=force_ui_redraw)
    
    name_hash: bpy.props.IntProperty(name="Name Hash", default=0)

    is_rendered:    bpy.props.BoolProperty(name="Rendered",  default=True)
    is_wireframe:   bpy.props.BoolProperty(name="Wireframe", default=False)
    #flag_2:    bpy.props.BoolProperty("Flag 2", default=False) # Consecutive mesh indices
    flag_3:    bpy.props.BoolProperty(name="Flag 3", default=False)
    flag_4:    bpy.props.BoolProperty(name="Flag 4", default=False)
    flag_5:    bpy.props.BoolProperty(name="Flag 5", default=False)
    flag_6:    bpy.props.BoolProperty(name="Flag 6", default=False)
    flag_7:    bpy.props.BoolProperty(name="Flag 7", default=False)

    flags:     bpy.props.IntProperty(name="Flags", get=flags_getter, options={'HIDDEN'})
    
    is_mesh:     bpy.props.BoolProperty(name="Is Mesh",     get=lambda self: self.mesh_type=="MESH")
    is_collider: bpy.props.BoolProperty(name="Is Collider", get=lambda self: self.mesh_type=="COLLIDER")

    def max_vertex_weights(self):
        bpy_mesh = self.id_data
        return max(len(v.groups) for v in bpy_mesh.vertices)
