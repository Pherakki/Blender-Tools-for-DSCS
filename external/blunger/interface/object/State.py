
##########################
# OBJECT STATE UTILITIES #
##########################
def lock_obj_transforms(obj, state):
    obj.lock_location[0] = state
    obj.lock_location[1] = state
    obj.lock_location[2] = state
    
    obj.lock_rotation[0] = state
    obj.lock_rotation[1] = state
    obj.lock_rotation[2] = state
    obj.lock_rotation_w  = state
    
    obj.lock_scale[0]    = state
    obj.lock_scale[1]    = state
    obj.lock_scale[2]    = state

