class IntermediateFormat:
    _version = 0.1
    f"""
    Intermediate Format: v{_version}.
    
    The purpose of the IntermediateFormat class is to describe DSCS model data with a single class.

    The imported data is split across several files, and collating this into a single location makes it more 
    convenient to program against.
    """

    def __init__(self):
        self.skeleton = Skeleton()
        self.meshes = []
        self.materials = []
        self.textures = []
        self.animations = {}
        self.unknown_data = {}
        
    def new_mesh(self):
        md = MeshData()
        self.meshes.append(md)
        return md
        
    def new_material(self):
        md = MaterialData()
        self.materials.append(md)
        return md
        
    def new_texture(self):
        td = TextureData()
        self.textures.append(td)
        return td

    def new_anim(self, key):
        ad = Animation()
        self.animations[key] = ad
        return ad

        
class MeshData:
    def __init__(self):
        self.vertices = []
        self.vertex_groups = []
        self.polygons = []
        self.material_id = None

        self.unknown_data = {}
        
    def add_vertex(self, position=None, normal=None, UV=None, vertex_groups=None, weights=None):
        self.vertices.append(Vertex(position, normal, UV, vertex_groups, weights))

    def add_vertex_group(self, bone_idx, vertex_indices=None, weights=None):
        self.vertex_groups.append(VertexGroup(bone_idx, vertex_indices, weights))
    
    def add_polygon(self, indices):
        self.polygons.append(Polygon(indices))


class Vertex:
    def __init__(self, position, normal, UV, vertex_groups, weights):
        self.position = position
        self.normal = normal
        self.UV = UV
        self.vertex_groups = vertex_groups
        self.vertex_group_weights = weights

        self.unknown_data = {}


class VertexGroup:
    def __init__(self, bone_idx, vertex_indices, weights):
        self.bone_idx = bone_idx
        self.vertex_indices = vertex_indices
        self.weights = weights


class Polygon:
    def __init__(self, indices):
        self.indices = indices


class MaterialData:
    def __init__(self):
        self.name = None
        self.texture_id = None
        self.toon_texture_id = None
        self.rgba = None
        self.specular_coeff = None
        self.shader_hex = None

        self.unknown_data = {}


class TextureData:
    def __init__(self):
        self.name = None
        self.filepath = None


class Skeleton:
    def __init__(self):
        self.bone_names = []
        self.bone_positions = []
        self.bone_xaxes = []
        self.bone_yaxes = []
        self.bone_zaxes = []
        self.bone_relations = []

        self.unknown_data = {}


class Animation:
    def __init__(self):
        self.rotations = {}
        self.locations = {}
        self.scales = {}

    def add_rotation_fcurve(self, bone_idx, frames, values):
        self.rotations[bone_idx] = FCurve(frames, values)

    def add_location_fcurve(self, bone_idx, frames, values):
        self.locations[bone_idx] = FCurve(frames, values)

    def add_scale_fcurve(self, bone_idx, frames, values):
        self.scales[bone_idx] = FCurve(frames, values)


class FCurve:
    def __init__(self, frames, values):
        self.frames = frames
        self.values = values
