import numpy as np
from .Rotation import quat_to_matrix, rotation_matrix_to_quat


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


def generate_transform_delta(parent_bones, rest_pose, inverse_bind_pose_matrices):
    result = []
    for i, (inverse_matrix, (quat, loc, scl)) in enumerate(zip(inverse_bind_pose_matrices, rest_pose)):
        bone_matrix = np.zeros((4, 4))
        bone_matrix[:3, :3] = quat_to_matrix(quat)
        bone_matrix[:3, 3] = loc[:3]
        bone_matrix[3, 3] = 1

        bm = calculate_bone_matrix_relative_to_parent(i, parent_bones, inverse_bind_pose_matrices)
        diff = np.dot(np.linalg.inv(bm), bone_matrix)
        diff_quat = rotation_matrix_to_quat(diff[:3, :3])
        diff_pos = diff[:3, 3]
        result.append([diff_quat, diff_pos, scl[:3]])
    return result


def apply_transform_to_keyframe():
    pass