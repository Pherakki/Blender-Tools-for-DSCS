from .NodeValue import BaseValue
from .NodeValue import ShaderVector
from .NodeValue import ShaderColorAlpha


class ShaderNodeGenerator:
    def __init__(self, node_tree):
        self.node_tree = node_tree
        self.nodes = node_tree.nodes
        self.links = node_tree.links
        self.connect = self.links.new

    def export_surface(self, value):
        surface_out = self.nodes.new('ShaderNodeOutputMaterial')
        try:
            self.connect(value.var, surface_out.inputs[0])
        except Exception as e:
            raise NotImplementedError(f"Invalid surface shader return value '{type(value)}'") from e
    
    def texture_sampler(self, name, image, uv=None, parent=None):
        sampler_node = self.nodes.new('ShaderNodeTexImage')
        sampler_node.name     = name
        sampler_node.label    = name
        sampler_node.parent   = parent
        sampler_node.image    = image
        if uv is not None:
            try:
                sampler_node.inputs[0] = uv.var
            except Exception as e:
                raise ValueError("Invalid UV coordinate type '{type(uv)}'") from e
        return ShaderColorAlpha(self, sampler_node.outputs[0], sampler_node.outputs[1])

