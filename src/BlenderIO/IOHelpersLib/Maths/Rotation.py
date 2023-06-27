from mathutils import Quaternion, Euler


def euler_to_quat(rotation_euler, rotation_mode):
    return Euler(rotation_euler, rotation_mode).to_quaternion()


def quat_to_euler(rotation_quat, rotation_mode):
    return Quaternion(rotation_quat).to_euler(rotation_mode)


def convert_rotation_to_quaternion(rotation_quat, rotation_euler, rotation_mode):
    if rotation_mode == "QUATERNION":
        # pull out quaternion data, normalise
        q = rotation_quat
        mag = sum(e**2 for e in q)
        return Quaternion([e/mag for e in q])
    else:
        return euler_to_quat(rotation_euler, rotation_mode)
