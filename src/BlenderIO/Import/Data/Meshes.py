import struct

import bpy
import numpy as np
from mathutils import Quaternion

from .....external.blunger.interface.object import preserve_initial_active_object
from .....external.blunger.interface.object import set_active_obj
from .....external.blunger.interface.mesh import create_merged_mesh
from .....external.blunger.interface.mesh import create_loop_normals
from .....external.blunger.interface.mesh import create_uv_map
from .....external.blunger.interface.mesh import create_color_map

from ....filetypes.Geom.Binary.Mesh.Base import PrimitiveTypes
from ....filetypes.Geom.Constants import AttributeTypes

from ...Globals import MODEL_TRANSFORMS

class MergedVertex:
    # Specialized implementation
    def __init__(self, position, indices, weights):
        self.position = position
        self.indices  = indices
        self.weights  = weights
        
    # Required interface
    @classmethod
    def from_unmerged(cls, unmerged_verts):
        # All vertices entering this should have the same position, indices, and weights
        v0 = unmerged_verts[0]
        instance = cls(v0.position, v0.indices, v0.weights)

        return instance

    @staticmethod
    def get_position(v):
        return v.position

    @staticmethod
    def get_merge_attributes(v):
        return [v.indices, v.weights]
    
    @staticmethod
    def is_invalid(v):
        return any(any(np.isnan(l)) for l in (v.position, v.indices, v.weights))


class VertexAttributeTracker:
    __slots__ = ("bpy_mesh_objs", "normals", "tangents", "binormals", "colors", "uv1s", "uv2s", "uv3s")
    
    def __init__(self):
        self.bpy_mesh_objs = []
        self.normals       = []
        self.tangents      = []
        self.binormals     = []
        self.colors        = []
        self.uv1s          = []
        self.uv2s          = []
        self.uv3s          = []
        
    def log_mesh(self, bpy_mesh_obj, dscs_mesh):
        self.bpy_mesh_objs.append(bpy_mesh_obj)
        if len(dscs_mesh.vertices):
            v = dscs_mesh.vertices[0]
            self.normals  .append(v.normal   is not None)
            self.tangents .append(v.tangent  is not None)
            self.binormals.append(v.binormal is not None)
            self.colors   .append(v.color    is not None)
            self.uv1s     .append(v.UV1      is not None)
            self.uv2s     .append(v.UV2      is not None)
            self.uv3s     .append(v.UV3      is not None)
        else:
            self.normals  .append(False)
            self.tangents .append(False)
            self.binormals.append(False)
            self.colors   .append(False)
            self.uv1s     .append(False)
            self.uv2s     .append(False)
            self.uv3s     .append(False)


@preserve_initial_active_object
def import_meshes(collection, model_name, bone_names, gi, bpy_armature_object, material_list, errorlog, attempt_merge):
    meshes = []
    meshes_using_material = {}
    for i, mesh in enumerate(gi.meshes):
        #################
        # PURE GEOMETRY #
        #################
        # First get the primitives
        if mesh.indices.primitive_type == PrimitiveTypes.TRIANGLES:
            faces = mesh.indices.unpack()
        elif mesh.indices.primitive_type == PrimitiveTypes.TRIANGLE_STRIP:
            faces = mesh.indices.to_triangles().unpack()
        else:
            errorlog.log_error_message(f"Primitive Type '{mesh.indices.primitive_type}', found on mesh {i}, is not supported")

        ###############
        # CREATE MESH #
        ###############
        # Init mesh
        meshobj_name = f"{model_name}_{i}"
        mesh_info    = create_merged_mesh(meshobj_name, 
                                          mesh.vertices,
                                          faces,
                                          MergedVertex,
                                          attempt_merge=attempt_merge,
                                          errorlog=errorlog)
        
        bpy_mesh = mesh_info.bpy_mesh
        bpy_mesh_object = bpy.data.objects.new(meshobj_name, bpy_mesh)
        collection.objects.link(bpy_mesh_object)

        # Assign materials
        active_material = material_list[mesh.material_id]
        bpy.data.objects[meshobj_name].active_material = active_material
        if active_material.DSCS_MaterialProperties.shader_name == "00000000_00000000_00000000_00000000":
            bpy_mesh_object.hide_set(True)
        matname = active_material.name
        if matname not in meshes_using_material:
            meshes_using_material[matname] = VertexAttributeTracker()
        meshes_using_material[matname].log_mesh(bpy_mesh_object, mesh)
        
        set_active_obj(bpy_mesh_object)
        
        #################
        # ADD LOOP DATA #
        #################
        # Assign UVs
        for uv_idx, uv_type in enumerate([AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3]):
            if mesh.vertices[0][uv_type] is not None:
                create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type][0], 1-l[uv_type][1]) for l in mesh_info.loops))

        # Assign vertex colours
        if mesh.vertices[0][AttributeTypes.COLOR] is not None:
            create_color_map(bpy_mesh, "ColorMap", [l.color for l in mesh_info.loops], "FLOAT")

        ###########
        # RIGGING #
        ###########
        vertex_groups = make_vertex_groups(mesh_info.vertices)
        for bone_idx, vg in vertex_groups.items():
            vertex_group = bpy_mesh_object.vertex_groups.new(name=bone_names[bone_idx])
            for vert_idx, vert_weight in vg:
                vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        #################
        # ADD MISC DATA #
        #################
        # Load the hashed mesh name
        signed_hash = struct.unpack('i', struct.pack('I', mesh.name_hash))[0]
        bpy_mesh_object.data.DSCS_MeshProperties.name_hash = signed_hash

        # Set armature constraint
        bpy_mesh_object.parent = bpy_armature_object
        modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = bpy_armature_object

        # Assign normals
        # Do this LAST because it can remove some loops
        if mesh.vertices[0][AttributeTypes.NORMAL] is not None:
            create_loop_normals(bpy_mesh, (l.normal for l in mesh_info.loops))

        # Tell Blender what we've done
        bpy_mesh.validate(verbose=True, clean_customdata=False)
        bpy_mesh.update()
        bpy_mesh.update()

        # Convert meshes Y up -> Z up
        bpy_mesh.transform(MODEL_TRANSFORMS.world_axis_rotation.matrix4x4)

        meshes.append(bpy_mesh)

    set_material_vertex_attributes(meshes_using_material, errorlog)


def set_material_vertex_attributes(meshes_using_material, errorlog):
    for matname, vas in meshes_using_material.items():
        bpy_mat = bpy.data.materials[matname]
        props = bpy_mat.DSCS_MaterialProperties

        # Normals
        if any(vas.normals):
            if not all(vas.normals):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess vertex normals - assuming the material requires normals")
            props.requires_normals = True
        else:
            props.requires_normals = False
        
        # Tangents
        if any(vas.tangents):
            if not all(vas.tangents):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess vertex tangents - assuming the material requires tangents")
            props.requires_tangents = True
        else:
            props.requires_tangents = False

        # Binormals
        if any(vas.binormals):
            if not all(vas.binormals):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess vertex binormals - assuming the material requires binormals")
            props.requires_binormals = True
        else:
            props.requires_binormals = False

        # Color
        if any(vas.colors):
            if not all(vas.colors):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess vertex colors - assuming the material requires a color map")
            props.requires_colors = True
        else:
            props.requires_colors = False
            
        # UV1
        if any(vas.uv1s):
            if not all(vas.uv1s):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess UV Map 1 - assuming the material requires UV Map 1")
            props.requires_uv1 = True
        else:
            props.requires_uv1 = False
            
        # UV2
        if any(vas.uv2s):
            if not all(vas.uv2s):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess UV Map 2 - assuming the material requires UV Map 2")
            props.requires_uv2 = True
        else:
            props.requires_uv2 = False
            
        # UV3
        if any(vas.uv3s):
            if not all(vas.uv3s):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess UV Map 3 - assuming the material requires UV Map 3")
            props.requires_uv3 = True
        else:
            props.requires_uv3 = False
        
        props.build_bpy_material()
        


def make_vertex_groups(blender_vert_infos):
    groups = {}
    for vert_idx, vert in enumerate(blender_vert_infos):
        for bone_idx, weight in zip(vert.indices, vert.weights):
            if weight == 0.:
                continue
            elif bone_idx not in groups:
                groups[bone_idx] = []
            groups[bone_idx].append((vert_idx, weight))
    return groups
