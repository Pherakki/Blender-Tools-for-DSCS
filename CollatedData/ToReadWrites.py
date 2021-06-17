from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from ..FileReaders.AnimReader import AnimReader

from ..FileInterfaces.NameInterface import NameInterface
from ..FileInterfaces.SkelInterface import SkelInterface
from ..FileInterfaces.GeomInterface import GeomInterface
from ..FileInterfaces.AnimInterface import AnimInterface

from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names
from ..Utilities.Rotation import rotation_matrix_to_quat
from ..Utilities.StringHashing import dscs_name_hash

import os
import numpy as np


def generate_files_from_intermediate_format(filepath, model_data, platform='PC'):
    file_folder = os.path.join(*os.path.split(filepath)[:-1])
    make_nameinterface(filepath, model_data)
    sk = make_skelinterface(filepath, model_data)
    make_geominterface(filepath, model_data, platform)
    for animation_name in model_data.animations:
        make_animreader(file_folder, model_data, animation_name, os.path.splitext(os.path.split(filepath)[-1])[0], sk)


def make_nameinterface(filepath, model_data):
    nameInterface = NameInterface()
    nameInterface.bone_names = model_data.skeleton.bone_names
    nameInterface.material_names = model_data.unknown_data['material names']

    nameInterface.to_file(filepath + ".name")


def make_skelinterface(filepath, model_data):
    skelInterface = SkelInterface()
    skelInterface.unknown_0x0C = model_data.skeleton.unknown_data['unknown_0x0C']
    skelInterface.parent_bones = model_data.skeleton.bone_relations
    skelInterface.rest_pose = model_data.skeleton.rest_pose

    skelInterface.unknown_data_1 = model_data.skeleton.unknown_data['unknown_data_1']
    skelInterface.bone_name_hashes = [dscs_name_hash(bone_name) for bone_name in model_data.skeleton.bone_names]
    skelInterface.unknown_data_3 = model_data.skeleton.unknown_data['unknown_data_3']
    skelInterface.unknown_data_4 = model_data.skeleton.unknown_data['unknown_data_4']

    skelInterface.to_file(filepath + ".skel")

    return skelInterface


def make_geominterface(filepath, model_data, platform):
    geomInterface = GeomInterface()

    geomInterface.meshes = []
    for mesh in model_data.meshes:
        gi_mesh = geomInterface.add_mesh()
        gi_mesh.unknown_0x31 = mesh.unknown_data['unknown_0x31']
        gi_mesh.name_hash = mesh.name_hash
        gi_mesh.unknown_0x4C = mesh.unknown_data['unknown_0x4C']

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

    geomInterface.texture_data = [td.name for td in model_data.textures]
    geomInterface.unknown_cam_data_1 = model_data.unknown_data['unknown_cam_data_1']
    geomInterface.unknown_cam_data_2 = model_data.unknown_data['unknown_cam_data_2']
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
