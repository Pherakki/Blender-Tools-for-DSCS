def lock_obj_transforms(obj):
    obj.lock_location[0] = True
    obj.lock_location[1] = True
    obj.lock_location[2] = True
    
    obj.lock_rotation[0] = True
    obj.lock_rotation[1] = True
    obj.lock_rotation[2] = True
    obj.lock_rotation_w  = True
    
    obj.lock_scale[0]    = True
    obj.lock_scale[1]    = True
    obj.lock_scale[2]    = True


def is_constraint_child_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "CHILD_OF":
                if constr.target == parent_obj:
                    return True
    return False

def is_copy_transforms_of(obj, parent_obj):
    if len(obj.constraints):
        for constr in obj.constraints:
            if constr.type == "COPY_TRANSFORMS":
                if constr.target == parent_obj:
                    return True
    return False

def find_bpy_objects(obj_list, parent_obj, predicates):
    out = []
    for obj in obj_list:
        if any((obj.parent == parent_obj,
               is_constraint_child_of(obj, parent_obj),
               is_copy_transforms_of(obj, parent_obj))) \
        and all([p(obj) for p in predicates]):
            out.append(obj)
    return out
