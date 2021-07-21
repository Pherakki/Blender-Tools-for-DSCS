from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from ..FileReaders.AnimReader import AnimReader

from ..FileInterfaces.NameInterface import NameInterface
from ..FileInterfaces.SkelInterface import SkelInterface
from ..FileInterfaces.GeomInterface import GeomInterface
from ..FileInterfaces.AnimInterface import AnimInterface

from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names
from ..Utilities.StringHashing import dscs_name_hash

import os


def generate_files_from_intermediate_format(filepath, model_data, platform='PC', animation_only=False):
    file_folder = os.path.join(*os.path.split(filepath)[:-1])

    if not animation_only:
        make_nameinterface(filepath, model_data)
        make_geominterface(filepath, model_data, platform)
    sk = make_skelinterface(filepath, model_data, not animation_only)

    for animation_name in model_data.animations:
        make_animreader(file_folder, model_data, animation_name, os.path.splitext(os.path.split(filepath)[-1])[0], sk)


def make_nameinterface(filepath, model_data):
    nameInterface = NameInterface()
    nameInterface.bone_names = model_data.skeleton.bone_names
    nameInterface.material_names = [mat.name for mat in model_data.materials]

    nameInterface.to_file(filepath + ".name")


def make_skelinterface(filepath, model_data, export=True):
    skelInterface = SkelInterface()
    skelInterface.unknown_0x0C = model_data.skeleton.unknown_data['unknown_0x0C']
    skelInterface.parent_bones = model_data.skeleton.bone_relations
    skelInterface.rest_pose = model_data.skeleton.rest_pose

    skelInterface.unknown_data_1 = model_data.skeleton.unknown_data['unknown_data_1']
    skelInterface.bone_name_hashes = [bytes.fromhex(dscs_name_hash(bone_name)) for bone_name in model_data.skeleton.bone_names]
    skelInterface.unknown_data_3 = model_data.skeleton.unknown_data['unknown_data_3']
    skelInterface.unknown_data_4 = model_data.skeleton.unknown_data['unknown_data_4']

    if export:
        skelInterface.to_file(filepath + ".skel")

    return skelInterface


def make_geominterface(filepath, model_data, platform):
    geomInterface = GeomInterface()

    geomInterface.meshes = []
    for mesh in model_data.meshes:
        gi_mesh = geomInterface.add_mesh()
        gi_mesh.unknown_0x31 = mesh.unknown_data['unknown_0x31']
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

    geomInterface.material_data = []
    for mat in model_data.materials:
        gi_mat = geomInterface.add_material()
        gi_mat.name_hash = dscs_name_hash(mat.name)
        gi_mat.shader_hex = mat.shader_hex
        gi_mat.enable_shadows = mat.enable_shadows

        gi_mat.shader_uniforms = {key: shader_uniforms_from_names[key](value) for key, value in mat.shader_uniforms.items()}
        gi_mat.unknown_material_components = mat.unknown_data['unknown_material_components']

    for cam in model_data.cameras:
        gi_camera = geomInterface.add_camera()
        # Might need to reverse this
        target_bone_hash = dscs_name_hash(cam.bone_name)
        gi_camera.bone_name_hash = target_bone_hash[6:8] + target_bone_hash[4:6] + target_bone_hash[2:4] + target_bone_hash[0:2]
        gi_camera.fov = cam.fov
        gi_camera.maybe_aspect_ratio = cam.maybe_aspect_ratio
        gi_camera.zNear = cam.zNar
        gi_camera.zFar = cam.zFar
        gi_camera.orthographic_scale = gi_camera.orthographic_scale
        gi_camera.projection = cam.projection

    for i, light in enumerate(model_data.light_sources):
        gi_light = geomInterface.add_light_source()
        # Might need to reverse this
        target_bone_hash = dscs_name_hash(light.bone_name)
        gi_light.bone_name_hash = target_bone_hash[6:8] + target_bone_hash[4:6] + target_bone_hash[2:4] + target_bone_hash[0:2]
        gi_light.mode = light.mode
        gi_light.light_id = i
        gi_light.intensity = light.intensity
        gi_light.unknown_fog_param = light.unknown_fog_param

        gi_light.red = light.red
        gi_light.green = light.green
        gi_light.blue = light.blue
        gi_light.alpha = light.alpha

    geomInterface.texture_data = [td.name for td in model_data.textures]
    geomInterface.light_sources = model_data.unknown_data['unknown_cam_data_1']
    geomInterface.cameras = model_data.unknown_data['unknown_cam_data_2']
    geomInterface.inverse_bind_pose_matrices = model_data.skeleton.inverse_bind_pose_matrices
    geomInterface.unknown_footer_data = model_data.unknown_data['unknown_footer_data']

    geomInterface.to_file(filepath + '.geom', platform)


def make_animreader(file_folder, model_data, animation_name, base_name, sk):
    anim_interface = AnimInterface()
    animation = model_data.animations[animation_name]

    anim_interface.playback_rate = animation.playback_rate
    anim_interface.num_bones = sk.num_bones

    for bone_idx, fcurve in animation.rotations.items():
        data = {k: v for k, v in zip(fcurve.frames, fcurve.values)}
        anim_interface.rotations[bone_idx] = data

    for bone_idx, fcurve in animation.locations.items():
        data = {k: v for k, v in zip(fcurve.frames, fcurve.values)}
        anim_interface.locations[bone_idx] = data

    for bone_idx, fcurve in animation.scales.items():
        data = {k: v for k, v in zip(fcurve.frames, fcurve.values)}
        anim_interface.scales[bone_idx] = data

    anim_interface.to_file(os.path.join(file_folder, animation_name) + '.anim', sk, [] if animation_name == base_name else None)
