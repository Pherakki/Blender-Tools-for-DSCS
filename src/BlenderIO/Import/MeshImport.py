import array
import math
import struct

import bpy
from mathutils import Vector, Quaternion

from ...Core.FileFormats.Geom.GeomBinary.MeshBinary.Base import PrimitiveTypes
from ...Core.FileFormats.Geom.Constants import AttributeTypes
from ..IOHelpersLib.Meshes import merge_vertices, import_loop_normals, create_uv_map
from ..IOHelpersLib.Context import safe_active_object_switch, set_active_obj, set_mode

class VertexAttributeTracker:
    __slots__ = ("bpy_mesh_objs", "normals", "tangents", "binormals", "colors", "uv1s", "uv2s", "uv3s")
    
    def __init__(self):
        self.bpy_mesh_objs = []
        self.normals   = []
        self.tangents  = []
        self.binormals = []
        self.colors    = []
        self.uv1s      = []
        self.uv2s      = []
        self.uv3s      = []
        
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


@safe_active_object_switch
def import_meshes(collection, model_name, ni, gi, armature, material_list, errorlog, try_merge_vertices):
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
            raise Exception(f"Primitive Type '{mesh.indices.primitive_type}' not supported")

        # Now merge OpenGL vertices into Blender vertices
        new_verts, new_tris, new_facevert_to_old_facevert_map = merge_vertices(mesh.vertices, faces, try_merge_vertices, errorlog)
        vert_positions = [Vector(v.position[:3]) for v in new_verts]

        ###############
        # CREATE MESH #
        ###############
        # Init mesh
        meshobj_name = f"{model_name}_{i}"
        bpy_mesh = bpy.data.meshes.new(name=meshobj_name)
        bpy_mesh_object = bpy.data.objects.new(meshobj_name, bpy_mesh)

        bpy_mesh_object.data.from_pydata(vert_positions, [], new_tris)
        collection.objects.link(bpy_mesh_object)

        # Assign materials
        active_material = material_list[mesh.material_id]
        bpy.data.objects[meshobj_name].active_material = active_material
        
        matname = active_material.name
        if matname not in meshes_using_material:
            meshes_using_material[matname] = VertexAttributeTracker()
        meshes_using_material[matname].log_mesh(bpy_mesh_object, mesh)
        
        set_active_obj(bpy_mesh_object)
        
        #################
        # ADD LOOP DATA #
        #################
        # Get the loop data
        n_loops = len(bpy_mesh.loops)
        map_of_loops_to_model_verts = {}
        for new_poly_idx, poly in enumerate(bpy_mesh.polygons):
            for loop_idx in poly.loop_indices:
                assert loop_idx not in map_of_loops_to_model_verts, "Loop already exists!"
                new_vert_idx = bpy_mesh.loops[loop_idx].vertex_index
                # Take only the vert id from the old (face_id, vert_id) pair
                old_vert_idx = new_facevert_to_old_facevert_map[(new_poly_idx, new_vert_idx)][1]
                map_of_loops_to_model_verts[loop_idx] = old_vert_idx

        loop_data = [mesh.vertices[map_of_loops_to_model_verts[loop_idx]] for loop_idx in range(n_loops)]

        # Assign UVs
        for uv_idx, uv_type in enumerate([AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3]):
            if mesh.vertices[0][uv_type] is not None:
                create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type][0], (l[uv_type][1]*-1) + 1) for l in loop_data))

        # Assign vertex colours
        if mesh.vertices[0][AttributeTypes.COLOR] is not None:
            colour_map = bpy_mesh.vertex_colors.new(name="Map", do_init=True)
            for loop_idx, loop in enumerate(bpy_mesh.loops):
                colour_map.data[loop_idx].color = loop_data[loop_idx].color

        # Rig the vertices
        vertex_groups = make_vertex_groups(new_verts)
        for bone_idx, vg in vertex_groups.items():
            vertex_group = bpy_mesh_object.vertex_groups.new(name=ni.bone_names[bone_idx])
            for vert_idx, vert_weight in vg:
                vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        #################
        # ADD MISC DATA #
        #################
        # Load the hashed mesh name
        signed_hash = struct.unpack('i', struct.pack('I', mesh.name_hash))[0]
        bpy_mesh_object.data.DSCS_MeshProperties.name_hash = signed_hash

        # Set armature constraint
        bpy_mesh_object.parent = armature
        modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = armature

        # Assign normals
        # Do this LAST because it can remove some loops
        if mesh.vertices[0][AttributeTypes.NORMAL] is not None:
            import_loop_normals(bpy_mesh, (l.normal for l in loop_data))

        # Tell Blender what we've done
        bpy_mesh.validate(verbose=True, clean_customdata=False)
        bpy_mesh.update()
        bpy_mesh.update()

        # Convert meshes Y up -> Z up
        bpy_mesh.transform(Quaternion([1/(2**.5), 1/(2**.5), 0, 0]).to_matrix().to_4x4())

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
            props.requires_uv1s = True
        else:
            props.requires_uv1s = False
            
        # UV2
        if any(vas.uv2s):
            if not all(vas.uv2s):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess UV Map 2 - assuming the material requires UV Map 2")
            props.requires_uv2s = True
        else:
            props.requires_uv2s = False
            
        # UV3
        if any(vas.uv3s):
            if not all(vas.uv3s):
                errorlog.log_warning_message(f"Meshes using material '{matname}' inconsistently possess UV Map 3 - assuming the material requires UV Map 3")
            props.requires_uv3s = True
        else:
            props.requires_uv3s = False


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
