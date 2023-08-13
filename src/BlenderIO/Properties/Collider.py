import struct
import bpy
from ..IOHelpersLib.Meshes.Generation import make_cuboid

class RagdollProperties(bpy.types.PropertyGroup):
    unknown_vector: bpy.props.FloatVectorProperty(name="Unknown Vector", size=3, default=[0.20000000298023224, 0.20000000298023224, 0.6000000238418579])
    unknown_float: bpy.props.FloatProperty("Unknown Float", name="Unknown Float", default=0.)
    is_solid: bpy.props.BoolProperty(name="Is Solid", description="True if the collider prevents other colliders moving through it. Disable this for colliders that are used to trigger events", default=True)

    @staticmethod
    def display(self, layout):
        layout.prop(self, "unknown_vector")
        layout.prop(self, "unknown_float")
        layout.prop(self, "is_solid")

def height_getter(self):
    if "height" not in self:
        self["height"] = 1.
    return self["height"]

def height_setter(self, value):
    self["height"] = value
    self.rebuild_mesh()

def width_getter(self):
    if "width" not in self:
        self["width"] = 1.
    return self["width"]

def width_setter(self, value):
    self["width"] = value
    self.rebuild_mesh()

def depth_getter(self):
    if "depth" not in self:
        self["depth"] = 1.
    return self["depth"]

def depth_setter(self, value):
    self["depth"] = value
    self.rebuild_mesh()

class BoxColliderProperties(bpy.types.PropertyGroup):
    height: bpy.props.FloatProperty(name="Height", default=1., get=height_getter, set=height_setter)
    width:  bpy.props.FloatProperty(name="Width",  default=1., get=width_getter,  set=width_setter)
    depth:  bpy.props.FloatProperty(name="Depth",  default=1., get=depth_getter,  set=depth_setter)
    cached_material: bpy.props.PointerProperty(type=bpy.types.Material, name="Cached Material",
        description="HIDDEN PROPERTY. This is used to reconstruct the mesh when swapping collider types."\
            "DO NOT USE FOR EXPORT. This property will only be updated when swapping collider types, and"\
            "thus will be out-of-date when exporting"
    )
    
    @staticmethod
    def display(self, layout):
        layout.prop(self, "height")
        layout.prop(self, "width")
        layout.prop(self, "depth")
    

    
    def rebuild_mesh(self):
        bpy_mesh = self.id_data
        
        # base_scale = min(bpy_mesh.scale)
        # self["height"] *= bpy_mesh.scale[0]/base_scale
        # self["width"]  *= bpy_mesh.scale[1]/base_scale
        # self["depth"]  *= bpy_mesh.scale[2]/base_scale
        # bpy_mesh.scale = [base_scale, base_scale, base_scale]
        
        bpy_mesh.clear_geometry()
        bpy_mesh.from_pydata(*make_cuboid(self["height"], self["width"], self["depth"], [1, 1, 1]))
        bpy_mesh.use_auto_smooth = False
        for poly in bpy_mesh.polygons:
            poly.use_smooth = False


class ComplexColliderProperties(bpy.types.PropertyGroup):
    @property
    def cached_verts(self):
        return self["cached_verts"]
    @cached_verts.setter
    def cached_verts(self, value):
        self["cached_verts"] = value
        
    @property
    def cached_indices(self):
        return self["cached_indices"]
    @cached_indices.setter
    def cached_indices(self, value):
        self["cached_indices"] = value
        
    @staticmethod
    def display(self, layout):
        print(self.cached_verts)
        


class ColliderProperties(bpy.types.PropertyGroup):
    collider_type: bpy.props.EnumProperty(items=[
        ("BOX", "Box", "Box Collider"),
        ("COMPLEX", "Complex", "Complex Collider"),
    ], name="Collider Type")

    # Every collider instance needs unique ragdoll props.
    ragdoll_props: bpy.props.PointerProperty(type=RagdollProperties, name="Ragdoll Properties")
    
    # Each collider uses one of these sets of properties. In principle these can be shared
    # between multiple collider instances alongside the collider mesh itself.
    box_props:     bpy.props.PointerProperty(type=BoxColliderProperties, name="Box Properties")
    complex_props: bpy.props.PointerProperty(type=ComplexColliderProperties, name="Complex Properties")

    @staticmethod
    def display(self, layout):
        layout.prop(self, "collider_type")
        self.ragdoll_props.display(self.ragdoll_props, layout)
        if self.collider_type == "BOX":
            self.box_props.display(self.box_props, layout)
        elif self.collider_type == "COMPLEX":
            self.complex_props.display(self.complex_props, layout)
        
