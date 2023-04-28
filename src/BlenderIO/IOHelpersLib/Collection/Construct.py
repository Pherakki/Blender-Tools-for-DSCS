import bpy


def init_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    if parent is None:
        parent = bpy.context.scene.collection
    parent.children.link(c)
    return c
