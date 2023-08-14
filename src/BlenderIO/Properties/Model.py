import bpy

from ..IOHelpersLib.UI import UIListBase



class DSCSSkelFloatChannel(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty(name="Name")
    obj_hash: bpy.props.IntProperty(name="Hash", subtype="UNSIGNED")
    flags:    bpy.props.IntProperty(name="Flags", min=0, max=255, subtype="UNSIGNED")
    channel: bpy.props.IntProperty(name="Channel", subtype="UNSIGNED", min=0, max=16777215)
    array_idx: bpy.props.IntProperty(name="Array Idx", subtype="UNSIGNED", min=0, max=15)


class ModelProperties(bpy.types.PropertyGroup):
    float_channels: bpy.props.CollectionProperty(type=DSCSSkelFloatChannel, name="Float Channels")
    active_float_channel_idx: bpy.props.IntProperty(name="", default=0)
    extra_clut:     bpy.props.StringProperty(name="Extra CLUT", default="")
    new_cam_parent_bone: bpy.props.StringProperty(name="Assign to")
    new_lgt_parent_bone: bpy.props.StringProperty(name="Assign to")
    
    def get_meshes(self):
        return [obj for obj in self.id_data.children if obj.type == "MESH"]

    def get_colliders(self):
        bpy_meshes = [obj for obj in self.id_data.children if obj.type == "MESH"]
        return [obj for obj in bpy_meshes if obj.data.DSCS_MeshProperties.mesh_type == "COLLIDER"]
    
    def get_solid_colliders(self):
        return [obj for obj in self.get_colliders() if obj.data.DSCS_ColliderProperties.is_solid == True]
    
    def get_nonsolid_colliders(self):
        return [obj for obj in self.get_colliders() if obj.data.DSCS_ColliderProperties.is_solid == False]
    
    def get_cameras(self):
        return find_bpy_objects(bpy.data.objects, self.id_data, [lambda x: x.type == "CAMERA"])
    
    def get_light(self):
        return find_bpy_objects(bpy.data.objects, self.id_data, [lambda x: x.type == "LIGHT"])
