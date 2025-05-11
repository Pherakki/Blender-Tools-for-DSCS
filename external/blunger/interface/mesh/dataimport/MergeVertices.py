from collections import defaultdict

import bpy
import numpy as np

from ....dataproc.geometry import try_merge_vertices


class Loops:
    def __init__(self, cmi, model_verts):
        self.cmi         = cmi
        self.model_verts = model_verts
        
    def __len__(self):
        return len(self.cmi.bpy_mesh.loops)
    
    def __iter__(self):
        for vert_idx in self.cmi.loops_to_modelverts_map:
            yield self.model_verts[vert_idx]
        
    def __getitem__(self, index):
        return self.model_verts[self.cmi.loops_to_modelverts_map[index]]


class ConstructedMeshInfo:
    __slots__ = ("bpy_mesh", "vertices", "faces", "_loops", "loops_to_modelverts_map", "verts_to_modelverts_map")
    
    def __init__(self, bpy_mesh, vertices, faces, loops_to_modelverts_map, verts_to_modelverts_map, model_verts):
        self.bpy_mesh = bpy_mesh
        self.vertices = vertices
        self.faces    = faces
        self._loops  = Loops(self, model_verts)
        
        self.loops_to_modelverts_map = loops_to_modelverts_map
        self.verts_to_modelverts_map = verts_to_modelverts_map
    
    @property
    def loops(self):
        return self._loops


def create_merged_mesh(mesh_name, vertices, faces, VertexType, sanitize_vertices=True, attempt_merge=True, errorlog=None):
    geometry = try_merge_vertices(vertices, faces, VertexType, None, sanitize_vertices, attempt_merge, errorlog)

    ###############
    # CREATE MESH #
    ###############
    # Init mesh
    bpy_mesh = bpy.data.meshes.new(name=mesh_name)
    bpy_mesh.from_pydata([v.position for v in geometry.vertices], [], geometry.triangles)
    
    #################
    # ADD LOOP DATA #
    #################
    # Get the loop data
    new_facevert_to_old_facevert_map = geometry.new_facevert_to_old_facevert_map
    loops_to_modelverts_map = np.empty((len(bpy_mesh.loops)), dtype=np.uint32)
    verts_to_modelverts_map = defaultdict(set)
    for new_poly_idx, poly in enumerate(bpy_mesh.polygons):
        for loop_idx in poly.loop_indices:
            bpy_vert_idx = bpy_mesh.loops[loop_idx].vertex_index
            # Take only the vert id from the old (face_id, vert_id) pair
            mdl_vert_idx = new_facevert_to_old_facevert_map[(new_poly_idx, bpy_vert_idx)][1]
            
            loops_to_modelverts_map[loop_idx] = mdl_vert_idx
            verts_to_modelverts_map[bpy_vert_idx].add(mdl_vert_idx)
    verts_to_modelverts_map = {k: sorted(v) for k, v in verts_to_modelverts_map.items()}

    # Also need to add in loose vertices here too!
    
    return ConstructedMeshInfo(bpy_mesh, 
                               geometry.vertices,
                               geometry.triangles,
                               loops_to_modelverts_map,
                               verts_to_modelverts_map,
                               vertices)

