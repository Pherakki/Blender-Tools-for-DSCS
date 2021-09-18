from ..FileInterfaces.NameInterface import NameInterface
from ..FileInterfaces.SkelInterface import SkelInterface
from ..FileInterfaces.GeomInterface import GeomInterface
from ..FileInterfaces.AnimInterface import AnimInterface
from .IntermediateFormat import IntermediateFormat
from ..Utilities.Rotation import bone_matrix_from_rotation_location, quat_to_matrix, rotation_matrix_to_quat

from ..Utilities.StringHashing import dscs_name_hash, int_to_BE_hex

import os
import numpy as np


def generate_intermediate_format_from_files(filepath, platform, import_anims=True):
    """
    Opens name, skel, geom, and anim files associated with the given filename and generates an
    IntermediateFormat object. Images are assumed to be in a sub-directory of the given file's directory named 'images'.

    Returns
    ------
    An IntermediateFormat representation of the data.
    """
    imported_namedata = NameInterface.from_file(filepath + '.name')
    imported_skeldata = SkelInterface.from_file(filepath + '.skel')
    imported_geomdata = GeomInterface.from_file(filepath + '.geom', platform)

    directory = os.path.split(filepath)
    filename = directory[-1]
    directory = os.path.join(*directory[:-1])

    # Always import the base anim, because it plays a special role in skeleton construction
    imported_animdata = {filename: AnimInterface.from_file(filepath + '.anim', imported_skeldata.num_uv_channels)}
    if import_anims:
        for afile in os.listdir(directory):
            afilepath = os.path.join(directory, afile)

            # Some of the Megido files have a different animation name convention
            if platform == 'Megido' and filename[-3:-1] == 's0':
                matches_name_pattern = afile[:len(filename) - 3] == filename[:-3]
            else:
                matches_name_pattern = afile[:len(filename)] == filename

            if afile[-4:] == 'anim' and matches_name_pattern and afile[:-4] != filename:
                afile_name, afile_ext = os.path.splitext(afile)
                print(afile)
                imported_animdata[afile_name] = AnimInterface.from_file(afilepath, imported_skeldata.num_uv_channels)

    images_directory = os.path.join(*os.path.split(filepath)[:-1], 'images')
    model_data = IntermediateFormat()

    model_data.material_name_hashes = {dscs_name_hash(name): name for name in imported_namedata.material_names}
    model_data.bone_name_hashes = {dscs_name_hash(name): name for name in imported_namedata.bone_names}
    add_meshes(model_data, imported_geomdata)
    add_textures(model_data, imported_geomdata, images_directory)
    add_materials(model_data, imported_namedata, imported_geomdata)
    add_skeleton(model_data, imported_namedata, imported_skeldata, imported_geomdata)
    add_anims(model_data, imported_animdata)
    add_lights(model_data, imported_geomdata.light_sources)
    model_data.cameras = imported_geomdata.cameras

    return model_data


def add_meshes(model_data, imported_geomdata):
    for mesh in imported_geomdata.meshes:
        model_data.new_mesh()
        current_IF_mesh = model_data.meshes[-1]
        for bone_id in mesh.vertex_group_bone_idxs:
            current_IF_mesh.add_vertex_group(bone_id, [], [])

        if 'WeightedBoneID' in mesh.vertices[0]:
            for i, vertex in enumerate(mesh.vertices):
                for vertex_group_idx, weight in zip(vertex['WeightedBoneID'], vertex['BoneWeight']):
                    current_IF_mesh.vertex_groups[vertex_group_idx].vertex_indices.append(i)
                    current_IF_mesh.vertex_groups[vertex_group_idx].weights.append(weight)
        for uv_type in ['UV', 'UV2', 'UV3']:
            if uv_type in mesh.vertices[0]:
                for vertex in mesh.vertices:
                    u, v = vertex[uv_type]
                    vertex[uv_type] = (u, 1. - v)

        current_IF_mesh.vertices = mesh.vertices

        for tri in mesh.polygons:
            current_IF_mesh.add_polygon(tri)
        current_IF_mesh.material_id = mesh.material_id

        # Add unknown data
        current_IF_mesh.name_hash = mesh.name_hash

        model_data.meshes[-1] = current_IF_mesh

    model_data.unknown_data['unknown_footer_data'] = imported_geomdata.unknown_footer_data


def add_materials(model_data, imported_namedata, imported_geomdata):
    material_names = imported_namedata.material_names
    for i, material in enumerate(imported_geomdata.material_data):
        model_data.new_material()

        model_data.materials[-1].name = model_data.material_name_hashes[material.name_hash]
        model_data.materials[-1].shader_hex = material.shader_hex
        model_data.materials[-1].enable_shadows = material.enable_shadows

        model_data.materials[-1].shader_uniforms = {key: value.data for key, value in material.shader_uniforms.items()}
        model_data.materials[-1].unknown_data['unknown_material_components'] = material.unknown_material_components


def add_textures(model_data, imported_geomdata, image_folder_path):
    for texture in imported_geomdata.texture_data:
        directory = os.path.join(image_folder_path, texture) + ".img"
        model_data.new_texture()
        model_data.textures[-1].name = texture
        model_data.textures[-1].filepath = directory


def add_skeleton(model_data, imported_namedata, imported_skeldata, imported_geomdata):
    model_data.skeleton.bone_names = imported_namedata.bone_names
    model_data.skeleton.bone_relations = imported_skeldata.parent_bones
    model_data.skeleton.inverse_bind_pose_matrices = imported_geomdata.inverse_bind_pose_matrices

    # Put the unknown data into the skeleton
    model_data.skeleton.unknown_data['unknown_0x0C'] = imported_skeldata.num_uv_channels
    model_data.skeleton.unknown_data['unknown_data_1'] = imported_skeldata.unknown_data_1
    model_data.skeleton.unknown_data['unknown_data_3'] = imported_skeldata.unknown_data_3
    model_data.skeleton.unknown_data['unknown_data_4'] = imported_skeldata.uv_channel_material_name_hashes
    parent_bones = {p: c for p, c in imported_skeldata.parent_bones}

    # Should be able to replace these with methods in 'Matrices', but some of the data must get edited in these methods...
    model_data.skeleton.rest_pose = [get_total_transform_matrix(i, parent_bones, imported_skeldata.rest_pose) for i in range(len(imported_skeldata.rest_pose))]
    for i, (inverse_matrix, (quat, loc, scl)) in enumerate(zip(imported_geomdata.inverse_bind_pose_matrices, imported_skeldata.rest_pose)):
        bone_matrix = np.zeros((4, 4))
        bone_matrix[:3, :3] = quat_to_matrix(quat)
        bone_matrix[:3, 3] = loc[:3]
        bone_matrix[3, 3] = 1

        bm = calculate_bone_matrix_relative_to_parent(i, parent_bones, model_data.skeleton.inverse_bind_pose_matrices)
        diff = np.dot(np.linalg.inv(bm), bone_matrix)
        diff_quat = rotation_matrix_to_quat(diff[:3, :3])
        diff_pos = diff[:3, 3]
        model_data.skeleton.rest_pose_delta.append([diff_quat, diff_pos, scl[:3]])


def calculate_bone_matrix_relative_to_parent(idx, parent_bones, inv_bind_pose_matrices):
    par = parent_bones[idx]
    if par == -1:
        pbm = np.eye(4)
    else:
        pbm = inv_bind_pose_matrices[par]
    bm = inv_bind_pose_matrices[idx]

    # Remember that bm is the inverse of the bone matrix, and pbm is the inverse of the parent's bone matrix,
    # so what we're really doing here is multiplying the inverse parent matrix by the ordinary child matrix.
    # This leaves us with just the transform of the child relative to the parent, since all the parent's contribution
    # to the child's transform has been taken off
    diff = np.dot(pbm, np.linalg.inv(bm))

    return diff


def add_anims(model_data, imported_animdata):
    for key, ar in imported_animdata.items():
        ad = model_data.new_anim(key)

        ad.playback_rate = ar.playback_rate

        # Set up some data holders
        rotation_fcurves_frames = {bone_idx: list(bone_rotations.keys()) for bone_idx, bone_rotations in ar.rotations.items()}
        rotation_fcurves_values = {bone_idx: list(bone_rotations.values()) for bone_idx, bone_rotations in ar.rotations.items()}
        location_fcurves_frames = {bone_idx: list(bone_locations.keys()) for bone_idx, bone_locations in ar.locations.items()}
        location_fcurves_values = {bone_idx: list(bone_locations.values()) for bone_idx, bone_locations in ar.locations.items()}
        scale_fcurves_frames = {bone_idx: list(bone_scales.keys()) for bone_idx, bone_scales in ar.scales.items()}
        scale_fcurves_values = {bone_idx: list(bone_scales.values()) for bone_idx, bone_scales in ar.scales.items()}

        # Having iterated through the data, we can now add the keyframe data to the intermediate format object.
        for bone_idx in range(ar.num_bones):
            ad.add_rotation_fcurve(bone_idx, rotation_fcurves_frames[bone_idx], rotation_fcurves_values[bone_idx])
            ad.add_location_fcurve(bone_idx, location_fcurves_frames[bone_idx], location_fcurves_values[bone_idx])
            ad.add_scale_fcurve(bone_idx, scale_fcurves_frames[bone_idx], scale_fcurves_values[bone_idx])

        # Do this properly in the future
        ad.uv_data = ar.user_channels


def add_lights(model_data, imported_lightdata):
    for light in imported_lightdata:
        model_light = model_data.new_light()
        target_bone_hash = int_to_BE_hex(light.bone_name_hash)
        model_light.bone_name = model_data.bone_name_hashes.get(target_bone_hash, 'Fog')
        model_light.mode = light.mode
        model_light.intensity = light.intensity
        model_light.unknown_fog_param = light.unknown_fog_param
        model_light.red = light.red
        model_light.green = light.green
        model_light.blue = light.blue
        model_light.alpha = light.alpha


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_total_transform(idx, parent_bones, bone_data):
    if idx == -1:
        rot = np.eye(3)
        loc = np.zeros(3)
        return rot, loc
    else:
        parent_idx = parent_bones[idx]
        parent_rot, parent_loc = get_total_transform(parent_idx, parent_bones, bone_data)

        rot = np.dot(parent_rot.T, quat_to_matrix(bone_data[idx][0]))
        loc = np.dot(parent_rot, np.array(bone_data[idx][1][:3])) + parent_loc

        return rot, loc


def get_total_transform_matrix(idx, parent_bones, bone_data):
    if idx == -1:
        bone_matrix = np.eye(4)
        return bone_matrix
    else:
        parent_idx = parent_bones[idx]
        parent_bone_matrix = get_total_transform_matrix(parent_idx, parent_bones, bone_data)

        diff_bone_matrix = np.zeros((4, 4))
        diff_bone_matrix[:3, :3] = quat_to_matrix(bone_data[idx][0])
        diff_bone_matrix[:, 3] = np.array(bone_data[idx][1])

        return np.dot(parent_bone_matrix, diff_bone_matrix)
