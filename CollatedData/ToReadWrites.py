import copy
import os
import numpy as np

from ..FileInterfaces.NameInterface import NameInterface
from ..FileInterfaces.SkelInterface import SkelInterface
from ..FileInterfaces.GeomInterface import GeomInterface
from ..FileInterfaces.AnimInterface import AnimInterface
from ..FileInterfaces.PhysInterface import PhysInterface

from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names
from ..Utilities.StringHashing import dscs_name_hash
from ..Utilities.Matrices import get_total_transform_matrix


def generate_files_from_intermediate_format(filepath, model_data, model_name, platform='PC', animation_only=False, create_physics=False):
    file_folder = os.path.join(*os.path.split(filepath)[:-1])
        
    si = make_skelinterface(filepath, model_data, not animation_only)
    if not animation_only:
        ni = make_nameinterface(filepath, model_data)
        gi = make_geominterface(filepath, model_data, si, platform)
        if create_physics:
            pi = PhysInterface.from_model(ni, si, gi)
            pi.to_file(filepath + ".phys")

    for animation_name in model_data.animations:
        make_animreader(file_folder, model_data, animation_name, model_name, si)


def make_nameinterface(filepath, model_data):
    nameInterface = NameInterface()
    nameInterface.bone_names = model_data.skeleton.bone_names
    nameInterface.material_names = [mat.name for mat in model_data.materials]

    nameInterface.to_file(filepath + ".name")
    return nameInterface


def make_skelinterface(filepath, model_data, export=True):
    skelInterface = SkelInterface()
    skelInterface.num_uv_channels = model_data.skeleton.unknown_data.get('unknown_0x0C', 0)
    skelInterface.parent_bones = model_data.skeleton.bone_relations
    skelInterface.rest_pose = model_data.skeleton.rest_pose
    
    skelInterface.unknown_data_1 = list(model_data.skeleton.unknown_data.get('unknown_data_1', [0]*skelInterface.num_uv_channels))
    skelInterface.bone_name_hashes = [bytes.fromhex(dscs_name_hash(bone_name)) for bone_name in model_data.skeleton.bone_names]
    skelInterface.unknown_data_3 = list(model_data.skeleton.unknown_data.get('unknown_data_3', [0]*skelInterface.num_uv_channels))
    skelInterface.uv_channel_material_name_hashes = model_data.skeleton.unknown_data.get('unknown_data_4', [0]*skelInterface.num_uv_channels)

    if export:
        skelInterface.to_file(filepath + ".skel")

    return skelInterface


def get_transformed_vertices(gi_mesh, transforms, switch_idx=2):
    if "WeightedBoneID" in gi_mesh.vertices[0]:
        transformed_vertices = np.array([np.zeros(3)] * len(gi_mesh.vertices))
        transformed_vertices[switch_idx, 2] = transformed_vertices[2, switch_idx]
        for i, vertex in enumerate(gi_mesh.vertices):
            bone_ids = vertex["WeightedBoneID"]
            bone_weights = vertex["BoneWeight"]
            vertex_transform = np.sum([weight * transforms[gi_mesh.vertex_group_bone_idxs[_id]] for _id, weight in
                                       zip(bone_ids, bone_weights)], axis=0)
            transformed_vertices[i] = np.dot(vertex_transform, [*vertex["Position"], 1])[:3]
    else:
        transformed_vertices = np.array([vertex["Position"] for vertex in gi_mesh.vertices])
    return transformed_vertices


def make_geominterface(filepath, model_data, sk, platform):
    geomInterface = GeomInterface()

    bone_matrices = [get_total_transform_matrix(i, {p: c for p, c in sk.parent_bones}, sk.rest_pose) for i in range(sk.num_bones)]
    transforms = [np.dot(transform, ibpm) for transform, ibpm in zip(bone_matrices, model_data.skeleton.inverse_bind_pose_matrices)]

    all_vertices = []
    geomInterface.meshes = []
    for mesh in model_data.meshes:
        gi_mesh = geomInterface.add_mesh()
        gi_mesh.meshflags = mesh.unknown_data['meshflags']
        gi_mesh.name_hash = mesh.name_hash

        for uv_type in ['UV', 'UV2', 'UV3']:
            if uv_type in mesh.vertices[0]:
                for vertex in mesh.vertices:
                    u, v = vertex[uv_type]
                    vertex[uv_type] = (u, 1. - v)

        gi_mesh.vertex_group_bone_idxs = [vg.bone_idx for vg in mesh.vertex_groups]
        gi_mesh.vertices = mesh.vertices
        gi_mesh.polygons = [p.indices for p in mesh.polygons]
        gi_mesh.material_id = mesh.material_id

        transformed_vertices = list(get_transformed_vertices(gi_mesh, transforms))

        is_billboard = False  # Fix by (presumably) asking the shader hex if it's a billboard... figure that out later
        if is_billboard:
            transformed_vertices.extend(list(get_transformed_vertices(gi_mesh, transforms, 0)))
            transformed_vertices.extend(list(get_transformed_vertices(gi_mesh, transforms, 1)))
        transformed_vertices = np.array(transformed_vertices)

        minvs = np.min(transformed_vertices, axis=0)
        maxvs = np.max(transformed_vertices, axis=0)
        assert len(maxvs) == 3
        assert np.sum(transformed_vertices ** 2, axis=1).shape == (len(transformed_vertices),), f"{transformed_vertices.shape}, {np.sum(transformed_vertices ** 2, axis=1).shape}"  # Check that I got the summation axis right

        gi_mesh.mesh_centre = (maxvs + minvs) / 2
        gi_mesh.bounding_box_lengths = (maxvs - minvs) / 2

        bind_vertices = np.array([vertex["Position"] for vertex in gi_mesh.vertices])
        maxrad = np.max(np.sum((bind_vertices - gi_mesh.mesh_centre) ** 2, axis=1))

        gi_mesh.bounding_sphere_radius = maxrad ** .5

        all_vertices.extend(transformed_vertices)

    if len(all_vertices):
        minvs = np.min(all_vertices, axis=0)
        maxvs = np.max(all_vertices, axis=0)
    else:
        minvs = np.zeros(3)
        maxvs = np.zeros(3)
    mesh_centre = (maxvs + minvs) / 2

    geomInterface.mesh_centre = mesh_centre
    geomInterface.bounding_box_lengths = (maxvs - minvs) / 2

    geomInterface.material_data = []
    for mat in model_data.materials:
        gi_mat = geomInterface.add_material()
        gi_mat.name_hash = dscs_name_hash(mat.name)
        gi_mat.shader_hex = mat.shader_hex
        gi_mat.enable_shadows = mat.enable_shadows

        gi_mat.shader_uniforms = {key: shader_uniforms_from_names[key](list(value)) for key, value in mat.shader_uniforms.items()}
        gi_mat.unknown_material_components = mat.unknown_data['unknown_material_components']


    geomInterface.camera = []
    for cam in model_data.cameras:
        gi_camera = geomInterface.add_camera()
        target_bone_hash = dscs_name_hash(cam.bone_name)
        target_bone_hash = target_bone_hash[6:8] + target_bone_hash[4:6] + target_bone_hash[2:4] + target_bone_hash[0:2]
        gi_camera.bone_name_hash = int(target_bone_hash, 16)
        gi_camera.fov = cam.fov
        gi_camera.maybe_aspect_ratio = cam.maybe_aspect_ratio
        gi_camera.zNear = cam.zNear
        gi_camera.zFar = cam.zFar
        gi_camera.orthographic_scale = cam.orthographic_scale
        gi_camera.projection = cam.projection

    geomInterface.light_sources = []
    for i, light in enumerate(model_data.light_sources):
        gi_light = geomInterface.add_light_source()
        target_bone_hash = dscs_name_hash(light.bone_name)
        target_bone_hash = target_bone_hash[6:8] + target_bone_hash[4:6] + target_bone_hash[2:4] + target_bone_hash[0:2]
        gi_light.bone_name_hash = int(target_bone_hash, 16)
        gi_light.mode = light.mode
        gi_light.light_id = i
        gi_light.intensity = light.intensity
        gi_light.unknown_fog_param = light.unknown_fog_param

        gi_light.red = light.red
        gi_light.green = light.green
        gi_light.blue = light.blue
        gi_light.alpha = light.alpha

    geomInterface.texture_data = [td.name for td in model_data.textures]
    geomInterface.inverse_bind_pose_matrices = model_data.skeleton.inverse_bind_pose_matrices
    geomInterface.unknown_footer_data = model_data.unknown_data['unknown_footer_data']

    print(">> USED MATERIALS BEFORE DUMP", len(geomInterface.material_data))
    geomInterface.to_file(filepath + ".geom", platform)
    return geomInterface


def validate_anim_data(fcurve):
    use_frames = fcurve.frames
    use_values = fcurve.values
    if len(use_frames):
        if use_frames[0] != 0:
            use_frames = [0, *use_frames]
            use_values = [use_values[0], *use_values]
    return {k: v for k, v in zip(use_frames, use_values)}


def make_animreader(file_folder, model_data, animation_name, base_name, sk):
    anim_interface = AnimInterface()
    animation = model_data.animations[animation_name]

    anim_interface.playback_rate = animation.playback_rate
    anim_interface.num_bones = sk.num_bones

    for bone_idx, fcurve in animation.rotations.items():
        data = validate_anim_data(fcurve)
        anim_interface.rotations[bone_idx] = data

    for bone_idx, fcurve in animation.locations.items():
        data = validate_anim_data(fcurve)
        anim_interface.locations[bone_idx] = data

    for bone_idx, fcurve in animation.scales.items():
        data = validate_anim_data(fcurve)
        anim_interface.scales[bone_idx] = data

    # Do this properly later
    anim_interface.user_channels = animation.uv_data

    anim_interface.to_file(os.path.join(file_folder, animation_name) + '.anim', sk, animation_name == base_name)
