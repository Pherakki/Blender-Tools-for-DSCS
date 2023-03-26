import math

import bpy
from mathutils import Matrix, Vector

from ..Context import safe_active_object_switch, set_active_obj


def construct_bone(name, armature, matrix, scale):
    bpy_bone = armature.data.edit_bones.new(name)
    
    tail, roll = mat3_to_vec_roll(matrix.to_3x3())
    tail *= scale
    
    pos_vector = matrix.to_translation()
    bpy_bone.head = pos_vector
    bpy_bone.tail = pos_vector + tail
    bpy_bone.roll = roll
    
    return bpy_bone


def vec_roll_to_mat3(vec, roll):
    """
    Code from
    https://blender.stackexchange.com/a/90240
    with minor edits:
        - Removed 'mathutils' prefix from Matrix classes
        - Fixed invalid operation in penultimate line: * -> @
    """
    #port of the updated C function from armature.c
    #https://developer.blender.org/T39470
    #note that C accesses columns first, so all matrix indices are swapped compared to the C version

    nor = vec.normalized()
    THETA_THRESHOLD_NEGY = 1.0e-9
    THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5

    #create a 3x3 matrix
    bMatrix = Matrix().to_3x3()

    theta = 1.0 + nor[1];

    if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

        bMatrix[1][0] = -nor[0];
        bMatrix[0][1] = nor[0];
        bMatrix[1][1] = nor[1];
        bMatrix[2][1] = nor[2];
        bMatrix[1][2] = -nor[2];
        if theta > THETA_THRESHOLD_NEGY_CLOSE:
            #If nor is far enough from -Y, apply the general case.
            bMatrix[0][0] = 1 - nor[0] * nor[0] / theta;
            bMatrix[2][2] = 1 - nor[2] * nor[2] / theta;
            bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta;

        else:
            #If nor is too close to -Y, apply the special case.
            theta = nor[0] * nor[0] + nor[2] * nor[2];
            bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta;
            bMatrix[2][2] = -bMatrix[0][0];
            bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta;

    else:
        #If nor is -Y, simple symmetry by Z axis.
        bMatrix = Matrix().to_3x3()
        bMatrix[0][0] = bMatrix[1][1] = -1.0;

    #Make Roll matrix
    rMatrix = Matrix.Rotation(roll, 3, nor)

    #Combine and output result
    mat = rMatrix @ bMatrix
    return mat


def mat3_to_vec_roll(mat):
    """
    Code from
    https://blender.stackexchange.com/a/38337
    https://blender.stackexchange.com/a/90240
    """
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv @ mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll


@safe_active_object_switch
def resize_bones(armature, default_size, min_bone_length):
    set_active_obj(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    for editbone in armature.data.edit_bones:
        resize_bone(editbone, default_size, min_bone_length)
    bpy.ops.object.mode_set(mode='OBJECT')


def resize_bone(bpy_bone, default_size, min_bone_length):
    position = bpy_bone.head
    head_to_tail = bpy_bone.tail - bpy_bone.head
    
    if len(bpy_bone.children):
        # Find out if there's an obvious successor bone
        possible_successors = []
        possible_successor_dot_products = []
        dot_products = []
        angular_discriminator = math.cos(1*math.pi/180) # Checking for bones aligned within 1 degree of separation
        for child in bpy_bone.children:
            child_target = child.head - bpy_bone.head
            
            projection = child_target.normalized().dot(head_to_tail.normalized())
            dot_products.append(projection)
            if projection > angular_discriminator:
                possible_successors.append(child)
                possible_successor_dot_products.append(projection)
            
        # Now decide the bone length after we've gathered all necessary
        # info
        if len(possible_successors) == 1:
            # Just link bone to its successor
            length = (possible_successors[0].head - bpy_bone.head).length
        elif len(possible_successors):
            # Take a weighted average of successor positions,
            # where the weighting factor is parameterised by how aligned
            # the bonehead->bonetail vector is to the 
            # bonehead->childhead vector
            length = 0.
            total_weight = 0.
            for successor, dp in zip(possible_successors, dot_products):
                weight = (dp-.99*angular_discriminator) # Always +ve for successors
                length +=  weight*(successor.head - bpy_bone.head).length
                total_weight += weight
            length /= total_weight
            length = abs(length)
        else:
            # Average together child positions
            # Should probably do something smarter than this
            tail_target = list(zip(*[c.head for c in bpy_bone.children]))
            tail_target = Vector([sum(coord)/len(coord) for coord in tail_target])
            head_to_target = tail_target - position
            
            alignment_factor = abs(head_to_target.normalized().dot(head_to_tail.normalized()))
            length = abs(head_to_target.length * alignment_factor) + abs(sum(default_size)/3 * (1 - alignment_factor))
            
        # Set some minimum length scale...
        if length < min_bone_length:
            length = min_bone_length
    else:
        own_direction = (head_to_tail).normalized()
        projected_dim = abs(own_direction.dot(default_size))
        
        if bpy_bone.parent is None:
            length = projected_dim
        else:
            parent_direction = (bpy_bone.parent.tail - bpy_bone.parent.head).normalized()
            projection = abs((own_direction).dot(parent_direction))
                
            length = bpy_bone.parent.length * projection + projected_dim * (1 - projection)
    
    if length <= 0:
        raise ValueError("FATAL INTERNAL ERROR: ATTEMPTED TO GIVE A BONE A NEGATIVE LENGTH")
    
    bpy_bone.length = length
