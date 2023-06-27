import math
from mathutils import Matrix, Quaternion


#############
# INTERFACE #
#############
def transform_bone_matrix(matrix, model_transforms): 
    world_axis_rotation   = model_transforms.world_axis_rotation
    bone_axis_permutation = model_transforms.bone_axis_permutation

    return world_axis_rotation @ matrix @ bone_axis_permutation

def parent_relative_to_bind_relative(bpy_bone, positions, rotations, scales, model_transforms=None):
    return _parent_relative_bind_relative_swap(bpy_bone, positions, rotations, scales, model_transforms, True)


def bind_relative_to_parent_relative(bpy_bone, positions, rotations, scales, model_transforms=None):

    return _parent_relative_bind_relative_swap(bpy_bone, positions, rotations, scales, model_transforms, False)

def parent_relative_to_bind_relative_preblend(bpy_bone, positions, rotations, scales, model_transforms=None):
    return _parent_relative_bind_relative_preblend_swap(bpy_bone, positions, rotations, scales, model_transforms, True)


def bind_relative_to_parent_relative_preblend(bpy_bone, positions, rotations, scales, model_transforms=None):
    return _parent_relative_bind_relative_preblend_swap(bpy_bone, positions, rotations, scales, model_transforms, False)


def align_quaternion_signs(rotations, reference_rotations):
    """
    Fix quaternion signs
    The furthest two quaternions can be apart is 360 degrees, i.e. q and -q,
    because quaternions are elements of SU(2) rather than the 3D rotation
    group SO(3), where elements can be at most 180 degrees apart.
    We will detect if a quaternion has inadvertently flipped sign by
    seeing if neighbouring quaternions are less than or greater than 180
    degrees apart, since this will tell us if it's closer to the +q or -q 
    solution.
    If this measurement is different before and after transforming the
    quaternions, then the quaternion has flipped signs and needs correction.
    """
    
    # Input validation
    t_rotations = rotations
    r_rotations = reference_rotations
    if len(t_rotations) <= 1:
        return t_rotations
    
    # Find if any rotations cross into the other relative quaternion sphere 
    # for both rotation sets (i.e., rotations larger than 180 degrees)
    r_distances = [((q1.inverted() @ q2).angle < math.pi) for q1, q2 in zip(r_rotations, r_rotations[1:])]
    t_distances = [((q1.inverted() @ q2).angle < math.pi) for q1, q2 in zip(t_rotations, t_rotations[1:])]
    # 1 if both crossed/did not cross, -1 otherwise
    differences = [-2*(b1 ^ b2) + 1 for b1, b2 in zip(r_distances, t_distances)]
    # Now convert the "boundary crossings" above into sign flips
    flip_signs = [1]
    for i in range(len(differences)):
        flip_signs.append(differences[i]*flip_signs[i])
    
    return [sgn*v for v, sgn in zip(t_rotations, flip_signs)]


##################
# IMPLEMENTATION #
##################
def _parent_relative_bind_relative_swap(bpy_bone, positions, rotations, scales, model_transforms, parent_to_bind):
    # Generate fallback matrices and local bind
    if model_transforms is None:
        inverse_world_axis_rotation = Matrix.Identity(4)
        bone_axis_permutation       = Matrix.Identity(4)
    else:    
        inverse_world_axis_rotation = model_transforms.world_axis_rotation_inverse
        bone_axis_permutation       = model_transforms.bone_axis_permutation
        
    if bpy_bone.parent is not None:
        local_bind_matrix = bone_axis_permutation @ bpy_bone.parent.matrix_local.inverted() @ bpy_bone.matrix_local
    else:
        local_bind_matrix = inverse_world_axis_rotation @ bpy_bone.matrix_local
    
    # Create matrices used in transform
    # This can DEFINITELY be made more efficient if it's a bottleneck
    bind_pose_translation, bind_pose_quaternion, _ = local_bind_matrix.decompose()
    bind_pose_rotation        = bind_pose_quaternion.to_matrix().to_4x4()
    inv_bind_pose_translation = Matrix.Translation(bind_pose_translation).inverted()
    inv_bind_pose_rotation    = bind_pose_rotation.inverted()
    inv_bone_axis_permutation = bone_axis_permutation.inverted()
    
    # Transform the keyframes
    # Why can't python have if constexpr...
    rotations = list(rotations)  # Evaluate any generator expressions, since we need to re-use the values
    if parent_to_bind:
        b_positions = (inv_bind_pose_rotation    @ Matrix.Translation(v[:3])          @ inv_bind_pose_translation @ bind_pose_rotation    for v in positions)
        b_rotations = (inv_bind_pose_rotation    @ Quaternion(v).to_matrix().to_4x4()                             @ bone_axis_permutation for v in rotations)
        b_scales    = (inv_bone_axis_permutation @ Matrix.Diagonal([*v[:3], 1.])                                  @ bone_axis_permutation for v in scales   )
    else: # bind_to_parent
        bind_pose_translation = Matrix.Translation(bind_pose_translation)
        b_positions = (bind_pose_rotation    @ Matrix.Translation(v)              @ inv_bind_pose_rotation    @ bind_pose_translation  for v in positions)
        b_rotations = (bind_pose_rotation    @ Quaternion(v).to_matrix().to_4x4() @ inv_bone_axis_permutation                          for v in rotations)
        b_scales    = (bone_axis_permutation @ Matrix.Diagonal([*v[:3], 1.])      @ inv_bone_axis_permutation                          for v in scales   )
    
    # Prepare return variables
    b_positions = [v.to_translation() for v in b_positions]
    b_rotations = [q.to_quaternion()  for q in b_rotations]
    b_scales    = [v.to_scale()       for v in b_scales   ]
    
    # Revert any sign flips that were introduced by converting to and from
    # rotation matrices
    align_quaternion_signs(b_rotations, rotations)
    
    return b_positions, b_rotations, b_scales


def _parent_relative_bind_relative_preblend_swap(bpy_bone, positions, rotations, scales, model_transforms, parent_to_bind):
    # Generate fallback matrices and local bind
    if model_transforms is None:
        inverse_world_axis_rotation = Matrix.Identity(4)
        bone_axis_permutation       = Matrix.Identity(4)
    else:    
        inverse_world_axis_rotation = model_transforms.world_axis_rotation_inverse
        bone_axis_permutation       = model_transforms.bone_axis_permutation
        
    if bpy_bone.parent is not None:
        local_bind_matrix = bone_axis_permutation @ bpy_bone.parent.matrix_local.inverted() @ bpy_bone.matrix_local
    else:
        local_bind_matrix = inverse_world_axis_rotation @ bpy_bone.matrix_local
    
    # Create matrices used in transform
    # This can DEFINITELY be made more efficient if it's a bottleneck
    _, bind_pose_quaternion, _ = local_bind_matrix.decompose()
    bind_pose_rotation        = bind_pose_quaternion.to_matrix().to_4x4()
    inv_bind_pose_rotation    = bind_pose_rotation.inverted()
    inv_bone_axis_permutation = bone_axis_permutation.inverted()
    
    # Transform the keyframes
    # Why can't python have if constexpr...
    rotations = list(rotations)  # Evaluate any generator expressions, since we need to re-use the values
    if parent_to_bind:
        b_positions = (inv_bind_pose_rotation    @ Matrix.Translation(v)               @ bind_pose_rotation    for v in positions)
        b_rotations = (inv_bone_axis_permutation @ Quaternion(v).to_matrix().to_4x4()  @ bone_axis_permutation for v in rotations)
        b_scales    = (inv_bone_axis_permutation @ Matrix.Diagonal([*v[:3], 1.])       @ bone_axis_permutation for v in scales   )
    else: # bind_to_parent
        b_positions = (bind_pose_rotation    @ Matrix.Translation(v)               @ inv_bind_pose_rotation    for v in positions)
        b_rotations = (bone_axis_permutation @ Quaternion(v).to_matrix().to_4x4()  @ inv_bone_axis_permutation for v in rotations)
        b_scales    = (bone_axis_permutation @ Matrix.Diagonal([*v[:3], 1.])       @ inv_bone_axis_permutation for v in scales   )
    
    # Prepare return variables
    b_positions = [v.to_translation() for v in b_positions]
    b_rotations = [q.to_quaternion()  for q in b_rotations]
    b_scales    = [v.to_scale()       for v in b_scales   ]

    # Revert any sign flips that were introduced by converting to and from
    # rotation matrices
    align_quaternion_signs(b_rotations, rotations)
    
    return b_positions, b_rotations, b_scales
