import struct

import bpy

from ...Core.FileFormats.Geom.GeomInterface import GeomInterface
from ...Core.FileFormats.Geom.GeomBinary.MeshBinary.Base import Vertex
from ...Utilities.Hash import dscs_hash_string
from ...Utilities.List import natural_sort
from ..IOHelpersLib.Meshes.VertexSplitting import bpy_mesh_to_VAO_IBO
from ..IOHelpersLib.Meshes.VertexSplitting import get_normals
from ..IOHelpersLib.Meshes.VertexSplitting import get_tangents
from ..IOHelpersLib.Meshes.VertexSplitting import get_binormals
from ..IOHelpersLib.Meshes.VertexSplitting import get_uvs
from ..IOHelpersLib.Meshes.VertexSplitting import get_colors
from ..IOHelpersLib.ErrorLog import DisplayableVerticesError
from ..IOHelpersLib.ErrorLog import DisplayableMeshesError


class MissingVertexGroupsError(DisplayableVerticesError):
    def __init__(self, mesh, vertex_indices, bone_names):
        newline = '\n'
        msg = f"Mesh '{mesh.name}' has {len(vertex_indices)} vertices weighted to bones that do not exist. These vertices have been selected for you. If you wish to ignore this error, check the 'Strip Missing Vertex Groups' option when exporting. The missing bones are:{newline}{newline.join(bone_names)}"
        super().__init__(msg, mesh, vertex_indices)

    def warning_message(self):
        mesh = self.bpy_mesh_obj
        vertex_indices = self.vertex_indices
        return f"Mesh '{mesh.name}' has {len(vertex_indices)} vertices weighted to bones that do not exist. These have been stripped from the export."


class TooManyIndicesError(DisplayableVerticesError):
    def __init__(self, mesh, vertex_indices):
        msg = f"Mesh '{mesh.name}' has {len(vertex_indices)} vertices that belong to more than 4 vertex groups. Ensure that all vertices belong to, at most, 4 groups before exporting."
        super().__init__(msg, mesh, vertex_indices)


class PartiallyUnriggedMeshError(DisplayableVerticesError):
    def __init__(self, mesh, vertex_indices):
        msg = f"Mesh '{mesh.name}' has {len(vertex_indices)}/{len(mesh.data.vertices)} vertices that are unrigged. These vertices have been selected for you."
        super().__init__(msg, mesh, vertex_indices)

    def warning_message(self):
        mesh = self.bpy_mesh_object
        vertex_indices = self.vertex_indices
        return f"Mesh '{mesh.name}' has {len(vertex_indices)}/{len(mesh.data.vertices)} vertices that are unrigged."


class TooManyVertexGroupsError(DisplayableMeshesError):
    def __init__(self, bpy_mesh_obj, group_count):
        msg = f"Mesh '{bpy_mesh_obj.name}' has {group_count} vertex groups with at least one vertex. A maximum of 54 vertex groups can be used per mesh. You should split this mesh such that each piece of the mesh contains less than 54 non-empty vertex groups."
        super().__init__(msg, [bpy_mesh_obj])
        

def is_constraint_child_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "CHILD_OF":
                if constr.target == parent_obj:
                    return True
    return False

def is_copy_transforms_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "COPY_TRANSFORMS":
                if constr.target == parent_obj:
                    return True
    return False

def find_bpy_objects(obj_list, parent_obj, predicates):
    out = []
    for obj in obj_list:
        if any((obj.parent == parent_obj,
               is_constraint_child_of(obj, parent_obj),
               is_copy_transforms_of(obj, parent_obj))) \
        and all([p(obj) for p in predicates]):
            out.append(obj)
    return out


def get_parent_info(obj):
    for constr in obj.constraints:
        if constr.type == "CHILD_OF":
            return (constr.target, constr.subtarget)
        elif constr.type == "COPY_TRANSFORMS":
            return (constr.target, constr.subtarget)
    return (obj.parent, obj.parent_bone)


def extract_meshes(gi, armature_obj, errorlog,  bone_names, material_names):
    bpy_meshes = natural_sort([obj for obj in armature_obj.children if obj.type == "MESH"], lambda x: x.name)
    
    # Get material names
    for bpy_mesh_obj in bpy_meshes:
        if bpy_mesh_obj.active_material is not None:
            mat_name = bpy_mesh_obj.active_material.name
            if mat_name not in material_names:
                material_names.append(mat_name)
    material_names_table = {nm: i for i, nm in enumerate(material_names)}
    
    #########################################
    # TODO: Bake mesh transforms into vertices!
    ##########################################
    
    # Export meshes
    for bpy_mesh_obj in bpy_meshes:
        props = bpy_mesh_obj.data.DSCS_MeshProperties
        
        mat = bpy_mesh_obj.active_material
                
        if mat is None:
            errorlog.missing_material_meshes.append(bpy_mesh_obj)
            continue
        elif len(bpy_mesh_obj.data.materials) > 1:
            errorlog.multiple_material_meshes.append(bpy_mesh_obj)
        
        material_idx = material_names_table[bpy_mesh_obj.active_material.name]
        
        vertices, indices, dscs_to_bpy_vert_map = extract_vertices(bpy_mesh_obj, errorlog, bone_names)

        unsigned_hash = struct.unpack('I', struct.pack('i', props.name_hash))[0]
        m = gi.add_mesh(unsigned_hash, props.flags, material_idx, vertices, indices)
        m.vertex_attributes = None  # Setting to 'None' will cause the attributes to be auto-calculated
        

def extract_vertices(bpy_mesh_obj, errorlog, bone_names):
    bpy_mesh = bpy_mesh_obj.data
    
    if bpy_mesh_obj.active_material is None:
        return [], []
    
    mat = bpy_mesh_obj.active_material
    props = mat.DSCS_MaterialProperties
    
    # Extract data
    loop_data = [
        get_normals(bpy_mesh_obj,   props.requires_normals,  4),
        get_uvs(bpy_mesh_obj,       props.requires_uv1,      "UV1", 6, errorlog),
        get_uvs(bpy_mesh_obj,       props.requires_uv2,      "UV2", 6, errorlog),
        get_uvs(bpy_mesh_obj,       props.requires_uv3,      "UV3", 6, errorlog),
        get_colors(bpy_mesh_obj,    props.requires_colors,   "Map", errorlog),
        get_tangents (bpy_mesh_obj, props.requires_tangents,  4, transform=lambda x, l: (*x, l.bitangent_sign)),
        get_binormals(bpy_mesh_obj, props.requires_binormals, 4)
    ]
    
    # Convert to VAO/IBO
    # Things to do here...
    # - Auto-split multimaterial meshes if asked
    # - Auto-split meshes with too many indices
    # o Strip missing vertex indices
    vertex_group_idx_to_name_map = {g.index: g.name for g in bpy_mesh_obj.vertex_groups}
    vget = VertexGetter(vertex_group_idx_to_name_map, bone_names, errorlog)
    vertices, indices, vao_to_dscs_vert_map = bpy_mesh_to_VAO_IBO(bpy_mesh, vget, loop_data, make_vertex)
    vget.log_errors(errorlog, bpy_mesh_obj, vertices)
    
    return vertices, indices, vao_to_dscs_vert_map
    

class VertexGetter:
    def __init__(self, vertex_group_idx_to_name_map, bone_names, errorlog):
        self.vweight_floor = 0. # errorlog.vweight_floor
        self.vertex_group_idx_to_name_map = vertex_group_idx_to_name_map
        self.bone_names = bone_names
        self.too_many_indices_verts = []
        self.unrigged_verts         = []
        self.missing_bone_names     = []
        self.missing_weight_verts   = []
        self.all_indices = set()
        
        self.log_missing_weights = (errorlog.missing_weights_policy == "STRIP")
        
    def __call__(self, vert_idx, vertex):
        vweight_floor                = self.vweight_floor
        too_many_indices_verts       = self.too_many_indices_verts
        unrigged_verts               = self.unrigged_verts
        bone_names                   = self.bone_names
        vertex_group_idx_to_name_map = self.vertex_group_idx_to_name_map
        missing_bone_names           = self.missing_bone_names
        missing_weight_verts         = self.missing_weight_verts
        
        ###########################
        # CLEAN UP VERTEX WEIGHTS #
        ###########################
        
        # Extract bone weights and check for any errors with them
        group_indices = [grp for grp in vertex.groups if grp.weight > vweight_floor]
        skin_indices  = [0, 0, 0, 0]
        skin_weights  = [0., 0., 0., 0.]
        grp_idx = 0
        has_missing_weights = False
            
        for grp in group_indices[:4]:
            # Check each index, strip if it does not exist
            bone_name = vertex_group_idx_to_name_map[grp.group]
            grp_bone_idx = bone_names.get(bone_name)
            if grp_bone_idx is None:
                if self.log_missing_weights:
                    has_missing_weights = True
                    missing_bone_names.add(bone_name)
            else:
                skin_indices[grp_idx] = grp_bone_idx
                skin_weights[grp_idx] = grp.weight
                self.all_indices.add(grp_bone_idx)
                grp_idx += 1
                
        if grp_idx:
            skin_indices = skin_indices[:grp_idx]
            skin_weights = skin_weights[:grp_idx]
            if grp_idx > 4:
                too_many_indices_verts.append(vert_idx)
        else:
            skin_indices = None
            skin_weights = None
            unrigged_verts.append(vert_idx)
            
        if has_missing_weights:
            missing_weight_verts.append(vert_idx)
            
        # Normalise the group weights
        total_weight = sum(skin_weights)
        if total_weight > 0.:
            skin_weights = [wght / total_weight for wght in skin_weights]
        
        ##########
        # RETURN #
        ##########
        return (vertex.co, skin_indices, skin_weights)
    
    def log_errors(self, errorlog, bpy_mesh_obj, vertices):
        # Too many indices
        if len(self.too_many_indices_verts):
            errorlog.log_error(TooManyIndicesError(bpy_mesh_obj, self.too_many_indices_verts))
        
        # Unrigged verts
        if 0 < len(self.unrigged_verts) < len(vertices):
            err = PartiallyUnriggedMeshError(bpy_mesh_obj, self.unrigged_verts)
            if errorlog.partially_unrigged_mesh_policy == "WARN":
                errorlog.log_warning_message(err.warning_message())
            elif errorlog.partially_unrigged_mesh_policy == "ERROR":
                errorlog.log_error(err)
            else:
                raise NotImplementedError(f"Unknown Partially Unrigged Mesh Policy option '{errorlog.partially_unrigged_mesh_policy}'")
        
        # Missing weights
        if len(self.missing_weight_verts):
            err = MissingVertexGroupsError(bpy_mesh_obj, self.missing_weight_verts, self.missing_bone_names)
            if errorlog.missing_weights_policy == "STRIP":
                errorlog.log_warning_message(err.warning_message())
            elif errorlog.missing_weights_policy == "ERROR":
                errorlog.log_error(err)
            else:
                raise NotImplementedError(f"Unknown Missing Weights Policy option '{errorlog.missing_weights_policy}'")
        
        # Too many vertex groups
        if len(self.all_indices) > 54:
            errorlog.log_error(TooManyVertexGroupsError(bpy_mesh_obj, len(self.all_indices)))


def make_vertex(vertex_data, loop_data):
    pos, skin_indices, skin_weights = vertex_data
    
    vb = Vertex()
    vb.position = pos
    vb.normal   = loop_data[0]
    vb.UV1      = loop_data[1]
    vb.UV2      = loop_data[2]
    vb.UV3      = loop_data[3]
    vb.color    = loop_data[4]
    vb.tangent  = loop_data[5]
    vb.binormal = loop_data[6]
    
    vb.indices = skin_indices
    vb.weights = skin_weights
    
    return vb


def extract_materials(gi, material_names):
    if None in material_names:
        material_names.remove(None)
    bpy_mats = [bpy.data.materials[nm] for nm in material_names]
    
    # Get unique texture names in DSCS order
    if len(bpy_mats):
        texture_names = []
        for bpy_mat in bpy_mats:
            tex_names = bpy_mat.DSCS_MaterialProperties.get_textures()
            for tex_name in tex_names:
                if tex_name not in texture_names:
                    texture_names.append(tex_name)
    else:
        texture_names = []
    
    texture_map   = {nm: i for i, nm in enumerate(texture_names)}
    for bpy_mat in bpy_mats:
        props   = bpy_mat.DSCS_MaterialProperties
        mat     = gi.add_material(dscs_hash_string(bpy_mat.name), props.flags, props.get_split_shader_name())
        
        extract_shader_uniforms(bpy_mat, mat, texture_map)
        extract_opengl_settings(bpy_mat, mat)
    
    return texture_names

def extract_shader_uniforms(bpy_mat, dscs_mat, texture_map):
    props = bpy_mat.DSCS_MaterialProperties
    
    def extract_texture_uniform(idx, prop):
        if prop.active: 
            dscs_mat.add_texture_uniform(idx, prop.extract_data(texture_map))
    
    def extract_shader_uniform(idx, bool_prop, data_prop):
        if bool_prop:
            if type(data_prop) is float:
                data_prop = [data_prop]
            dscs_mat.add_shader_uniform(idx, data_prop)
    
    # Normal Mapping
    extract_texture_uniform(0x35, props.normal_sampler)
    extract_texture_uniform(0x45, props.overlay_normal_sampler)
    extract_shader_uniform (0x36, props.use_bumpiness,         props.bumpiness)
    extract_shader_uniform (0x46, props.use_overlay_bumpiness, props.overlay_bumpiness)
    extract_shader_uniform (0x4F, props.use_parallax_bias_x,   props.parallax_bias_x)
    extract_shader_uniform (0x50, props.use_parallax_bias_y,   props.parallax_bias_y)
    extract_shader_uniform (0x64, props.use_distortion,        props.distortion_strength)
    
    # Diffuse
    extract_texture_uniform(0x32, props.color_sampler)
    extract_texture_uniform(0x44, props.overlay_color_sampler)
    extract_shader_uniform (0x33, props.use_diffuse_color,    props.diffuse_color)
    extract_shader_uniform (0x47, props.use_overlay_strength, props.overlay_strength)
    extract_texture_uniform(0x43, props.lightmap_sampler)
    extract_shader_uniform (0x71, props.use_lightmap_power,    props.lightmap_power)
    extract_shader_uniform (0x72, props.use_lightmap_strength, props.lightmap_strength)
    
    # Lighting
    extract_texture_uniform(0x48, props.clut_sampler)
    extract_shader_uniform (0x38, props.use_specular_strength, props.specular_strength)
    extract_shader_uniform (0x39, props.use_specular_power,    props.specular_power   )
    
    # Reflection
    extract_texture_uniform(0x3A, props.env_sampler)
    extract_shader_uniform (0x3B, props.use_reflections, props.reflection_strength)
    extract_shader_uniform (0x3C, props.use_fresnel_min, props.fresnel_min)
    extract_shader_uniform (0x3D, props.use_fresnel_exp, props.fresnel_exp)
    
    # Subsurface
    extract_shader_uniform (0x3E, props.use_surface_color,    props.surface_color)
    extract_shader_uniform (0x3F, props.use_subsurface_color, props.subsurface_color)
    extract_shader_uniform (0x40, props.use_fuzzy_spec_color, props.fuzzy_spec_color)
    extract_shader_uniform (0x41, props.use_rolloff,          props.rolloff)
    extract_shader_uniform (0x42, props.use_velvet_strength,  props.velvet_strength)
    
    # UV Transforms
    extract_shader_uniform (0x55, props.uv_1.use_scroll_speed, props.uv_1.scroll_speed)
    extract_shader_uniform (0x58, props.uv_2.use_scroll_speed, props.uv_2.scroll_speed)
    extract_shader_uniform (0x5B, props.uv_3.use_scroll_speed, props.uv_3.scroll_speed)
    extract_shader_uniform (0x5E, props.uv_1.use_offset,       props.uv_1.offset)
    extract_shader_uniform (0x61, props.uv_2.use_offset,       props.uv_2.offset)
    extract_shader_uniform (0x74, props.uv_3.use_offset,       props.uv_3.offset)
    extract_shader_uniform (0x78, props.uv_1.use_rotation,     props.uv_1.rotation)
    extract_shader_uniform (0x7B, props.uv_2.use_rotation,     props.uv_2.rotation)
    extract_shader_uniform (0x7E, props.uv_3.use_rotation,     props.uv_3.rotation)
    extract_shader_uniform (0x81, props.uv_1.use_scale,        props.uv_1.scale)
    extract_shader_uniform (0x84, props.uv_2.use_scale,        props.uv_2.scale)
    extract_shader_uniform (0x87, props.uv_3.use_scale,        props.uv_3.scale)
    
    # Scene
    extract_shader_uniform (0x54, props.use_time,              props.time)
    
    # extract_texture_uniform(0x32, props.envs_sampler)
    
    for u in props.unhandled_uniforms: 
        dscs_mat.add_shader_uniform(*u.extract_data(texture_map))


def extract_opengl_settings(bpy_mat, dscs_mat):
    props = bpy_mat.DSCS_MaterialProperties

    # 0xA8
    # 0xA4
    # 0xA3
    # 0xA6
    
    for u in props.unhandled_settings:
        dscs_mat.add_opengl_setting(u.index, u.data)
    # GL ALPHA
    if props.use_gl_alpha:
        dscs_mat.add_opengl_setting(0xA1, [1, 0, 0, 0])
        func = props.gl_alpha_func
        if   func == "GL_NEVER":    gl_func = 0x200
        elif func == "GL_LESS":     gl_func = 0x201
        elif func == "GL_EQUAL":    gl_func = 0x202
        elif func == "GL_LEQUAL":   gl_func = 0x203
        elif func == "GL_GREATER":  gl_func = 0x204
        elif func == "GL_NOTEQUAL": gl_func = 0x205
        elif func == "GL_GEQUAL":   gl_func = 0x206
        elif func == "GL_ALWAYS":   gl_func = 0x207
        elif func == "INVALID":     gl_func = props.gl_alpha_invalid_value
        dscs_mat.add_opengl_setting(0xA0, [gl_func, props.gl_alpha_threshold, 0, 0])
    # GL BLEND
    if props.use_gl_blend:
        dscs_mat.add_opengl_setting(0xA4, [1, 0, 0, 0])
    if not bpy_mat.use_backface_culling:
        dscs_mat.add_opengl_setting(0xA6, [0, 0, 0, 0])

import os

class BaseImageExtractor:
    def get_data(self):
        raise NotImplementedError
        
    def peek_data(self, offset, size):
        raise NotImplementedError

    def export(self, path):
        raise NotImplementedError


class PackedImageExtractor(BaseImageExtractor):
    def __init__(self, image, export_name):
        self.export_name = export_name
        self.image       = image
        self.packed_file = image.packed_file
        
    def get_data(self):
        return self.packed_file.data
    
    def peek_data(self, offset, size):
        return self.packed_file.data[offset:offset+size]
    
    def export(self, path):
        filepath = os.path.join(path, self.export_name + ".img")
        with open(filepath, 'wb') as F:
            F.write(self.packed_file.data)
        

class UnpackedImageExtractor(BaseImageExtractor):
    def __init__(self, image, export_name):
        self.export_name = export_name
        self.image       = image
        self.filepath    = image.filepath_from_user()
        
    def get_data(self):
        with open(self.filepath, 'rb') as F:
            return F.read()
    
    def peek_data(self, offset, size):
        with open(self.filepath, 'rb') as F:
            F.seek(0)
            return F.read(size)
    
    def export(self, path):
        filepath = os.path.join(path, self.export_name + ".img")
        with open(filepath, 'wb') as F:
            F.write(self.get_data())
        
        
def extract_textures(gi, texture_names, errorlog):
    valid_textures = {}
    for texture_name in texture_names:
        if texture_name not in bpy.data.images:
            valid_textures[texture_name] = None
            continue
        
        bpy_image = bpy.data.images[texture_name]
        if len(texture_name) <= 32:
            valid_textures[texture_name] = bpy_image
        else:
            # Shorten name to 32 chars, check if any other texture already has
            # that name
            trunc_name = texture_name[:32]
            if trunc_name in valid_textures:
                # If so, chop off the final four characters because we'll
                # start renaming the textures as e.g. tex.001, tex.002
                # until we find a texture that is not a duplicate
                trunc_name = trunc_name[:-4]
                if trunc_name in valid_textures:
                    for name_idx in range(1000):
                        new_name = f"{trunc_name}.{name_idx:0>3}"
                        if new_name not in valid_textures:
                            trunc_name = new_name
                            break
                    else: # If all 1000 slots are used up...
                        errorlog.log_error("Congratulations, you successfully misnamed so many textures that the exporter has used up all 1000 of its fallback texture name slots trying to fix them. This can only happen if you are using over 1000 textures on a model that begin with the same 32 characters. You should probably reconsider what you are trying to do.")
            errorlog.log_warning_message(f"Texture name '{texture_name}' exceeds 32 characters and was exported as '{trunc_name}'")
            valid_textures[trunc_name] = bpy_image

    texture_extractors = []
    for texture_name, bpy_image in valid_textures.items():
        bpy_image = bpy.data.images[texture_name]
        if bpy_image is None:
            raise NotImplementedError("NEED TO EXPORT PLACEHOLDER DDS HERE") # Export dummy DDS
        elif bpy_image.packed_file is not None:
            texture_extractors.append(PackedImageExtractor(bpy_image, texture_name))
        elif bpy_image.source == "FILE" and os.path.exists(bpy_image.filepath_from_user()):
            texture_extractors.append(UnpackedImageExtractor(bpy_image, texture_name))
        else:
            errorlog.log_error_message(f"Image '{bpy_image.name}' if not a packed file or a file that exists on disk. Only packed files or images with valid filepaths can currently be exported.")
    
    gi.textures = [ex.export_name for ex in texture_extractors]
            
    return texture_extractors


def extract_cameras(gi, armature, errorlog, bpy_to_dscs_bone_map):
    proj_lookup = {
        "PERSP": 0,
        "ORTHO": 1
    }
    
    bpy_camera_objs = natural_sort(find_bpy_objects(bpy.data.objects, armature, [lambda x: x.type == "CAMERA"]), lambda x: x.name)
    for bpy_camera_obj in bpy_camera_objs:
        camera = bpy_camera_obj.data
        
        fov = camera.angle
        aspect_ratio = camera.DSCS_CameraProperties.aspect_ratio
        zNear = camera.clip_start
        zFar = camera.clip_end
        orthographic_scale = camera.orthographic_scale
        
        # Throw error if projection not in lookup
        proj = camera.projection
        if proj not in proj_lookup:
            errorlog.log_warning(f"Unavailable camera projection '{camera.projection}' - defaulting to Perspective.")
        projection = proj_lookup.get(proj, 0)
        
        # Get bone
        _, bone_name = get_parent_info(bpy_camera_obj)
        if bone_name == "":
            errorlog.log_warning_message(f"Camera '{bpy_camera_obj.name}' not attached to a bone - exporting with null parent")
            bone_name_hash = 0
        else:
            if bone_name in bpy_to_dscs_bone_map:
                bone_name_hash = bpy_to_dscs_bone_map[bone_name].name_hash
            else:
                bone_name_hash = 0
                errorlog.log_warning_message(f"Camera '{bpy_camera_obj.name}' attached to non-existent bone '{bone_name}' - exporting with null parent")
            
            gi.add_camera(bone_name_hash, fov, aspect_ratio, zNear, zFar, orthographic_scale, projection)


def extract_lights(gi, armature, errorlog, bpy_to_dscs_bone_map):
    bpy_light_objs = natural_sort(find_bpy_objects(bpy.data.objects, armature, [lambda x: x.type == "LIGHT"]), lambda x: x.name)
    for bpy_light_obj in bpy_light_objs:
        bpy_light = bpy_light_obj.data
        
        lookup = {
            0: "POINT",
            1: "UNKNOWN",
            2: "AMBIENT",
            3: "DIRECTIONAL",
            4: "FOG"
        }
        inverse_lookup = {v: k for k, v in lookup.items()}
        
        props = bpy_light.DSCS_LightProperties
        
        # Get bone
        _, bone_name = get_parent_info(bpy_light_obj)
        if bone_name == "":
            bone_name_hash = props.bone_hash
        else:
            if bone_name in bpy_to_dscs_bone_map:
                bone_name_hash = bpy_to_dscs_bone_map[bone_name].name_hash
            else:
                bone_name_hash = 0
                errorlog.log_warning_message(f"Light '{bpy_light_obj.name}' attached to non-existent bone '{bone_name}' - exporting with null parent")
                
        # props
        mode         = inverse_lookup[props.mode]
        light_id     = props.light_id
        intensity    = props.intensity
        fog_height   = props.fog_height
        alpha        = props.alpha
        unknown_0x20 = props.unknown_0x20
        unknown_0x24 = props.unknown_0x24
        unknown_0x28 = props.unknown_0x28
        unknown_0x2C = props.unknown_0x2C
        red, green, blue = bpy_light.color
            
        gi.add_light(bone_name_hash, mode, light_id, intensity, fog_height, red, green, blue, alpha, unknown_0x20, unknown_0x24, unknown_0x28, unknown_0x2C)
        
        
def extract_IBPMs(gi, armature_obj):
    armature = armature_obj.data
    
    for bone in armature.bones:
        bone_matrix = bone.matrix_local.inverted()
        gi.ibpms.append([*bone_matrix[0], *bone_matrix[1], *bone_matrix[2]])


def extract_geom(armature_obj, errorlog, bpy_to_dscs_bone_map, material_names):
    armature = armature_obj.data
    
    gi = GeomInterface()
    extract_meshes(gi, armature_obj, errorlog, bpy_to_dscs_bone_map, material_names)
    texture_names      = extract_materials(gi, material_names)
    texture_extractors = extract_textures(gi, texture_names, errorlog)
    extract_cameras(gi, armature_obj, errorlog, bpy_to_dscs_bone_map)
    extract_lights(gi, armature_obj, errorlog, bpy_to_dscs_bone_map)
    extract_IBPMs(gi, armature_obj)
    extra_clut = armature.DSCS_ModelProperties.extra_clut
    if extra_clut != "":
        gi.extra_clut = bytes.fromhex(extra_clut) # Can we make this an image?

    return gi, texture_extractors
