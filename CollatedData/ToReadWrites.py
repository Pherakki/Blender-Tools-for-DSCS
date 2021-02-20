from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from ..FileReaders.GeomReader.MaterialReader import UnknownMaterialData
from ..FileReaders.AnimReader import AnimReader

from ..FileInterfaces.NameInterface import NameInterface
from ..FileInterfaces.SkelInterface import SkelInterface
from ..FileInterfaces.GeomInterface import GeomInterface
# from ..FileInterfaces.AnimInterface import AnimInterface

from ..FileReaders.GeomReader.ShaderUniforms import shader_uniforms_from_names

import os
import numpy as np


def generate_files_from_intermediate_format(filepath, model_data, platform='PC'):
    file_folder = os.path.join(*os.path.split(filepath)[:-1])
    make_nameinterface(filepath, model_data)
    sk = make_skelinterface(filepath, model_data)
    make_geominterface(filepath, model_data, platform)
    #for animation_name in model_data.animations:
    #    make_animreader(file_folder, model_data, animation_name, sk)


def make_nameinterface(filepath, model_data):
    nameInterface = NameInterface()
    nameInterface.bone_names = model_data.skeleton.bone_names
    nameInterface.material_names = model_data.unknown_data['material names']

    nameInterface.to_file(filepath + ".name")


def make_skelinterface(filepath, model_data):
    skelInterface = SkelInterface()
    skelInterface.unknown_0x0C = model_data.skeleton.unknown_data['unknown_0x0C']
    skelInterface.parent_bones = model_data.skeleton.bone_relations
    skelInterface.bone_data = model_data.skeleton.unknown_data['bone_data'] # Don't do this. Calculate it from the bone matrices. Add support for deltas on import later

    skelInterface.unknown_data_1 = model_data.skeleton.unknown_data['unknown_data_1']
    skelInterface.unknown_data_2 = model_data.skeleton.unknown_data['unknown_data_2']
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
        gi_mesh.unknown_0x34 = mesh.unknown_data['unknown_0x34']
        gi_mesh.unknown_0x36 = mesh.unknown_data['unknown_0x36']
        gi_mesh.unknown_0x4C = mesh.unknown_data['unknown_0x4C']

        for uv_type in ['UV', 'UV2', 'UV3']:
            if uv_type in mesh.vertices[0]:
                for vertex in mesh.vertices:
                    u, v = vertex[uv_type]
                    vertex[uv_type] = (u, 1. - v)
        gi_mesh.vertices = mesh.vertices
        gi_mesh.vertex_group_bone_idxs = [vg.bone_idx for vg in mesh.vertex_groups]
        gi_mesh.polygons = [p.indices for p in mesh.polygons]
        gi_mesh.material_id = mesh.material_id

    geomInterface.material_data = []
    for mat in model_data.materials:
        gi_mat = geomInterface.add_material()
        gi_mat.unknown_0x00 = mat.unknown_data['unknown_0x00']
        gi_mat.unknown_0x02 = mat.unknown_data['unknown_0x02']
        gi_mat.shader_hex = mat.shader_hex
        gi_mat.unknown_0x16 = mat.unknown_data['unknown_0x16']

        gi_mat.shader_uniforms = {key: shader_uniforms_from_names[key](value) for key, value in mat.shader_uniforms.items()}
        gi_mat.unknown_material_components = mat.unknown_data['unknown_material_components']

    geomInterface.texture_data = [td.name for td in model_data.textures]
    geomInterface.unknown_cam_data_1 = model_data.unknown_data['unknown_cam_data_1']
    geomInterface.unknown_cam_data_2 = model_data.unknown_data['unknown_cam_data_2']
    geomInterface.inverse_bind_pose_matrices = model_data.skeleton.inverse_bind_pose_matrices
    geomInterface.unknown_footer_data = model_data.unknown_data['unknown_footer_data']

    geomInterface.to_file(filepath + '.geom', platform)

# def make_animreader(file_folder, model_data, animation_name, sk):
#     animation = model_data.animations[animation_name]
#     with open(file_folder + animation_name + '.anim', 'wb') as F:
#         animReader = AnimReader(F, sk)
#         animReader.filetype = '40AE'
#         animReader.animation_duration = animation.num_frames/animation.playback_rate
#         animReader.playback_rate = animation.playback_rate
#
#         animReader.num_bones = sk.num_bones
#         animReader.total_frames = animation.num_frames + 1
#         animReader.always_16384 = 16384
#
#         static_rots, nonstatic_rots = get_static_animation_elements(animation.rotations)
#         static_locs, nonstatic_locs = get_static_animation_elements(animation.locations)
#         static_scls, nonstatic_scls = get_static_animation_elements(animation.scales)
#
#         animReader.initial_pose_bone_rotations_count = len(static_rots)
#         animReader.initial_pose_bone_locations_count = len(static_locs)
#         animReader.initial_pose_bone_scales_count = len(static_scls)
#         animReader.unknown_0x1C = 0  # Hardcoded for now...
#         animReader.keyframe_bone_rotations_count = len(nonstatic_rots)
#         animReader.keyframe_bone_locations_count = len(nonstatic_locs)
#         animReader.keyframe_bone_scales_count = len(nonstatic_scls)
#         animReader.unknown_0x24 = 0  # Hardcoded for now...
#
#         animReader.padding_0x26 = 0
#         animReader.bone_mask_bytes = 0  # Hardcoded for now...
#         animReader.abs_ptr_bone_mask = 0  # Hardcoded for now...
#
#         ###### TODO #########
#         animReader.unknown_0x30 = 0x30 + 0
#         animReader.unknown_0x34 = 0x34 + 0
#         animReader.rel_ptr_initial_pose_bone_rotations = 0x38 + 0
#         animReader.rel_ptr_initial_pose_bone_locations = 0x3C + 0
#         animReader.rel_ptr_initial_pose_bone_scales = 0x40 + 0
#         animReader.unknown_0x44 = 0x44 + 0
#
#         animReader.padding_0x48 = 0
#         animReader.padding_0x4C = 0
#         animReader.padding_0x50 = 0
#         animReader.padding_0x54 = 0
#         animReader.padding_0x58 = 0
#         animReader.padding_0x5C = 0
#
#         #
#
#         animReader.initial_pose_rotations_bone_idxs = static_rots
#         animReader.initial_pose_locations_bone_idxs = static_locs
#         animReader.initial_pose_scales_bone_idxs = static_scls
#         animReader.unknown_bone_idxs_4 = []
#         animReader.keyframe_rotations_bone_idxs = nonstatic_rots
#         animReader.keyframe_locations_bone_idxs = nonstatic_locs
#         animReader.keyframe_scales_bone_idxs = nonstatic_scls
#         animReader.unknown_bone_idxs_8 = []
#
#         #
#
#         animReader.initial_pose_bone_rotations = [animation.rotations[bidx] for bidx in static_rots]
#         animReader.initial_pose_bone_locations = [animation.locations[bidx] for bidx in static_locs]
#         animReader.initial_pose_bone_scales = [animation.scales[bidx] for bidx in static_scls]
#         animReader.unknown_data_4 = []
#
#         #
#
#         keyframe_chunks, frame_splits = chunk_keyframes({bidx: animation.rotations[bidx] for bidx in nonstatic_rots}, nonstatic_rots,
#                                                         {bidx: animation.locations[bidx] for bidx in nonstatic_locs}, nonstatic_locs,
#                                                         {bidx: animation.scales[bidx] for bidx in nonstatic_scls}, nonstatic_scls,
#                                                         animation.num_frames)
#         animReader.num_keyframe_chunks = len(keyframe_chunks)
#         print(len(keyframe_chunks), frame_splits)
#         animReader.keyframe_chunks_ptrs = None  # TODO
#         animReader.keyframe_counts = [(frame_splits[i], frame_splits[i+1]-frame_splits[i])
#                                       for i in range(len(frame_splits)-1)]
#         animReader.bone_masks = None
#         animReader.unknown_data_masks = []  # TODO
#
#         #
#         print(animation_name, animReader.keyframe_counts)
#
#         animReader.prepare_read_op()
#         for keyframe_chunks in animReader.keyframe_chunks:
#             pass  # TODO
#
#
# def get_static_animation_elements(elem_dict):
#     statics = []
#     nonstatics = []
#     for bone_idx, elem in elem_dict.items():
#         (statics if elem.frames == [0] else nonstatics).append(bone_idx)
#     return statics, nonstatics
#
#
# def chunk_keyframes(kf_rots, kf_rots_idxs, kf_locs, kf_locs_idxs, kf_scls, kf_scls_idxs, nframes):
#     kf_chunks = [gen_kf_chunks_structure(kf_rots_idxs, kf_locs_idxs, kf_scls_idxs)]
#     frame_splits = [0]
#     rotbytes = 0
#     locbytes = 0
#     sclbytes = 0
#     for i in range(nframes):
#         rots = {bidx: (i, kf_rots[bidx].values[kf_rots[bidx].frames.index(i)]) for bidx in kf_rots_idxs if i in kf_rots[bidx].frames}
#         locs = {bidx: (i, kf_locs[bidx].values[kf_locs[bidx].frames.index(i)]) for bidx in kf_locs_idxs if i in kf_locs[bidx].frames}
#         scls = {bidx: (i, kf_scls[bidx].values[kf_scls[bidx].frames.index(i)]) for bidx in kf_scls_idxs if i in kf_scls[bidx].frames}
#
#         rotbytes += len(rots)*6
#         locbytes += len(locs)*12
#         sclbytes += len(scls)*12
#
#         if rotbytes > 0xFFFF or locbytes > 0xFFFF or sclbytes > 0xFFFF or (i == nframes-1):
#             kf_chunks.append(gen_kf_chunks_structure(kf_rots_idxs, kf_locs_idxs, kf_scls_idxs))
#             frame_splits.append(i - 1)
#
#             rotbytes = 0
#             locbytes = 0
#             sclbytes = 0
#
#             print(rots)
#             print(locs)
#             print(scls)
#
#         for bidx in rots:
#             kf_chunks[-1][0][bidx].append(rots[bidx])
#         for bidx in locs:
#             kf_chunks[-1][1][bidx].append(locs[bidx])
#         for bidx in scls:
#             kf_chunks[-1][2][bidx].append(scls[bidx])
#
#     if nframes == 0:
#         frame_splits.append(nframes)
#     else:
#         frame_splits.append(nframes-1)
#
#     return kf_chunks, frame_splits
#
#
# def gen_kf_chunks_structure(kf_rots_idxs, kf_locs_idx, kf_scls_idxs):
#     return [{bidx: [] for bidx in kf_rots_idxs},
#             {bidx: [] for bidx in kf_locs_idx},
#             {bidx: [] for bidx in kf_scls_idxs}]
#
#
# def gen_bone_hierarchy(parent_bones):
#     to_return = []
#     parsed_bones = []
#     bones_left_to_parse = [bidx for bidx in parent_bones]
#     while len(bones_left_to_parse) > 0:
#         hierarchy_line, new_parsed_bone_idxs = gen_bone_hierarchy_line(parent_bones, parsed_bones, bones_left_to_parse)
#         to_return.append(hierarchy_line)
#
#         for bidx in new_parsed_bone_idxs[::-1]:
#             parsed_bones.append(bones_left_to_parse[bidx])
#             del bones_left_to_parse[bidx]
#     return to_return
#
#
# def gen_bone_hierarchy_line(parent_bones, parsed_bones, bones_left_to_parse):
#     """It ain't pretty, but it works"""
#     to_return = []
#     new_parsed_bone_idxs = []
#     bone_iter = iter(bones_left_to_parse)
#     prev_j = 0
#     for i in range(4):
#         for j, bone in enumerate(bone_iter):
#             mod_j = j + prev_j
#             parent_bone = parent_bones[bone]
#             if parent_bone == -1 or parent_bone in parsed_bones:
#                 to_return.append(bone)
#                 to_return.append(parent_bone)
#                 new_parsed_bone_idxs.append(mod_j)
#                 prev_j = mod_j + 1
#                 break
#         if mod_j == len(bones_left_to_parse)-1 and len(to_return) < 8:
#             to_return.extend(to_return[-2:])
#     return to_return, new_parsed_bone_idxs
