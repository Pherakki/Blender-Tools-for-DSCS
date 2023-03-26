from mathutils import Matrix, Quaternion, Vector


def parent_relative_to_bind_relative(bpy_bone, positions, rotations, scales, inverse_world_axis_rotation, bone_axis_permutation):
    # Get the matrices required to convert animations from DSCS -> Blender
    if bpy_bone.parent is not None:
        local_bind_matrix = bone_axis_permutation @ bpy_bone.parent.matrix_local.inverted() @ bpy_bone.matrix_local
    else:
        local_bind_matrix = inverse_world_axis_rotation @ bpy_bone.matrix_local
    
    # This can DEFINITELY be made more efficient if it's a bottleneck
    bind_pose_translation, bind_pose_quaternion, _ = local_bind_matrix.decompose()
    bind_pose_rotation        = bind_pose_quaternion.to_matrix().to_4x4()
    inv_bind_pose_rotation    = bind_pose_rotation.inverted()
    inv_bone_axis_permutation = bone_axis_permutation.inverted()
    
    b_positions = (inv_bind_pose_rotation    @ Matrix.Translation(Vector(v[:3]) - bind_pose_translation) @ bind_pose_rotation    for v in positions)
    b_rotations = (inv_bind_pose_rotation    @ Quaternion(v).to_matrix().to_4x4()                        @ bone_axis_permutation for v in rotations)
    b_scales    = (inv_bone_axis_permutation @ Matrix.Diagonal([*v[:3], 1.])                             @ bone_axis_permutation for v in scales   )
    
    b_positions = [v.decompose()[0] for v in b_positions]
    b_rotations = [q.decompose()[1] for q in b_rotations]
    b_scales    = [v.decompose()[2] for v in b_scales   ]
    
    return b_positions, b_rotations, b_scales


def parent_relative_to_bind_relative_preblend(bpy_bone, positions, rotations, scales, inverse_world_axis_rotation, bone_axis_permutation):
    if bpy_bone.parent is not None:
        local_bind_matrix = bone_axis_permutation @ bpy_bone.parent.matrix_local.inverted() @ bpy_bone.matrix_local
    else:
        local_bind_matrix = inverse_world_axis_rotation @ bpy_bone.matrix_local
    
    # This can DEFINITELY be made more efficient if it's a bottleneck
    bind_pose_translation, bind_pose_quaternion, _ = local_bind_matrix.decompose()
    bind_pose_rotation        = bind_pose_quaternion.to_matrix().to_4x4()
    inv_bind_pose_rotation    = bind_pose_rotation.inverted()
    inv_bone_axis_permutation = bone_axis_permutation.inverted()
    
    b_positions = (inv_bind_pose_rotation    @ Matrix.Translation(v)               @ bind_pose_rotation    for v in positions)
    b_rotations = (inv_bone_axis_permutation @ Quaternion(v).to_matrix().to_4x4()  @ bone_axis_permutation for v in rotations)
    b_scales    = (inv_bone_axis_permutation @ Matrix.Diagonal([*v, 1.])           @ bone_axis_permutation for v in scales   )
    
    b_positions = [v.decompose()[0] for v in b_positions]
    b_rotations = [q.decompose()[1] for q in b_rotations]
    b_scales    = [v.decompose()[2] for v in b_scales   ]

    return b_positions, b_rotations, b_scales
