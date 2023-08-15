import bpy

from ..IOHelpersLib.Objects import find_bpy_objects
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
    
    nonrendered_mesh_toggle_is_show: bpy.props.BoolProperty(default=True)
    solidcollider_toggle_is_show:    bpy.props.BoolProperty(default=False)
    nonsolidcollider_toggle_is_show: bpy.props.BoolProperty(default=False)
        
    def are_all_visible(self, collection):
        return all(m.visible_get() for m in collection)

    def get_meshes(self, bpy_object):
        return [obj for obj in bpy_object.children if obj.type == "MESH"]

    def get_nonrendered_meshes(self, bpy_object):
        bpy_meshes = self.get_meshes(bpy_object)
        bpy_meshes = [obj for obj in bpy_meshes if obj.data.DSCS_MeshProperties.mesh_type == "MESH" and obj.active_material is not None]
        return [obj for obj in bpy_meshes if obj.active_material.DSCS_MaterialProperties.shader_name == "00000000_00000000_00000000_00000000"]
    
    def all_nonrendered_meshes_visible(self, bpy_object):
        return self.are_all_visible(self.get_nonrendered_meshes(bpy_object))
    
    def get_colliders(self, bpy_object):
        bpy_meshes = [obj for obj in bpy_object.children if obj.type == "MESH"]
        return [obj for obj in bpy_meshes if obj.data.DSCS_MeshProperties.mesh_type == "COLLIDER"]
    
    def get_solid_colliders(self, bpy_object):
        return [obj for obj in self.get_colliders(bpy_object) if obj.DSCS_ColliderProperties.ragdoll_props.is_solid == True]
    
    def all_solid_colliders_visible(self, bpy_object):
        return self.are_all_visible(self.get_solid_colliders(bpy_object))
    
    def get_nonsolid_colliders(self, bpy_object):
        return [obj for obj in self.get_colliders(bpy_object) if obj.DSCS_ColliderProperties.ragdoll_props.is_solid == False]
    
    def all_nonsolid_colliders_visible(self, bpy_object):
        return self.are_all_visible(self.get_nonsolid_colliders(bpy_object))
    
    def get_cameras(self):
        return find_bpy_objects(bpy.data.objects, self.id_data, [lambda x: x.type == "CAMERA"])
    
    def get_light(self):
        return find_bpy_objects(bpy.data.objects, self.id_data, [lambda x: x.type == "LIGHT"])
