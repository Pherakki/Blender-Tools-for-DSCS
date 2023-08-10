from .NodeGenerationLibrary import *


def mk_mesh_attribute_node(nodes, attr_name, name, location, parent):
    if len(attr_name) > 23:
         raise ValueError(f"Attribute name too long: {attr_name}")
    return mk_attribute_node(nodes, "OBJECT", f"DSCS_MeshProperties.{attr_name}", name, location, parent)

def mk_collider_attribute_node(nodes, attr_name, name, location, parent):
    # if len(attr_name) > 18:
    #      raise ValueError(f"Attribute name too long: {attr_name}")
    return mk_attribute_node(nodes, "OBJECT", f"data.DSCS_ColliderProperties.{attr_name}", name, location, parent)

def MeshFloatAttribute(nodes, attr_name, name, location, parent):
    return mk_mesh_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]

def ColliderFloatAttribute(nodes, attr_name, name, location, parent):
    return mk_collider_attribute_node(nodes, attr_name, name, location, parent).outputs["Fac"]


def rebuild_collider_tree(bpy_material):
    props    = bpy_material.DSCS_MaterialProperties
    node_tree = bpy_material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    connect = links.new
    
    # Wipe tree
    nodes.clear()
    
    # Set various settings
    bpy_material.use_backface_culling = False
    bpy_material.blend_method = "BLEND"
    
    start_x = -900
    is_collider = MeshFloatAttribute    (nodes, "is_collider",  "Is Collider?",  (start_x,   0), None)
    is_solid    = ColliderFloatAttribute(nodes, "ragdoll_props.is_solid",     "Is Solid?", (start_x, 300), None)
    is_solid_collider = multiply_scalars(nodes, connect, is_collider, is_solid, "Is Solid Collider?", (start_x + 300, -300), None)
    
    collider_color = lerp_color(nodes, connect, is_solid_collider, [0.0, 0.8, 0.0, 1.0], [1.0, 0.0, 0.4, 1.0], "Collider Color", (-start_x + 600, 300), None)
    mesh_color     = lerp_color(nodes, connect, is_collider, [0.8, 0.8, 0.8, 1.0], collider_color, "Mesh Color", (start_x + 600, 300), None)
    
    mesh_alpha     = lerp_scalar(nodes, connect, is_collider, 0.0, 0.2, "Mesh Alpha", (start_x + 600, 600), None)
    
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    connect(bsdf.inputs["Base Color"], mesh_color)
    connect(bsdf.inputs["Alpha"],      mesh_alpha)
    
    mat_out = nodes.new('ShaderNodeOutputMaterial')
    mat_out.location = (300, 0)
    connect(bsdf.outputs[0], mat_out.inputs["Surface"])
    