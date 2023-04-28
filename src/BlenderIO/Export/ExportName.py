import bpy
from mathutils import Matrix

from ...Core.FileFormats.Name.NameInterface import NameInterface


def extract_name(errorlog, bpy_to_dscs_bone_map, material_names):
    ni = NameInterface()
    
    ni.bone_names = [nm for idx, nm in sorted((idx, nm) for nm, idx in bpy_to_dscs_bone_map.items())]
    ni.material_names = material_names
    
    return ni
