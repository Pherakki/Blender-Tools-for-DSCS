import traceback

import bpy
import numpy as np


class LoopCandidate:
    __slots__ = ("vert_id", "face_id", "face_normal", "face_centre")
    
    def __init__(self, vertex_id, face_id, face_normal, face_centre):
        self.vert_id = vertex_id
        self.face_id = face_id
        self.face_normal = face_normal
        self.face_centre = face_centre


class BlenderVertexInfo:
    __slots__ = ("position", "indices", "weights")
    
    def __init__(self, position, indices, weights):
        self.position = position
        self.indices = indices
        self.weights = weights


def sanitize_mergeable_vertices(vertex_positions, vertex_indices, vertex_weights):
    bad_vertices = []
    for i in range(len(vertex_positions)):
        if any(np.isnan(vertex_positions[i])):
            bad_vertices.append(i)
        elif any(np.isnan(vertex_indices[i])):
            bad_vertices.append(i)
        elif any(np.isnan(vertex_weights[i])):
            bad_vertices.append(i)
    
    return bad_vertices


def merge_vertices(vertex_positions, vertex_indices, vertex_weights, triangles, ignored_vertices=None):
    # TODO: used_vertices = set()
    
    # Remove any vertices we've been told to ignore, for example because they
    # contain invalid data.
    # This option is offered internally so that the facevert map can be built
    # in reference to the "full" vertex indices, not the "clean" ones,
    # since only a subset of vertex data enters this function.
    if ignored_vertices is not None:
        ignore_verts_set = set(ignored_vertices)
        triangles = [tri for tri in triangles if all(idx not in ignore_verts_set for idx in tri)]
        # TODO: # Mark ignore vertices as 'used' so we don't accidentally import them
        # as loose vertices later
        # used_vertices.update(ignore_verts_set)
        
    # First get all vertex-face pairs
    # We plan to merge some of these into Blender vertices (i.e. collections of input vertices with the same position)
    # However, we need to ensure that e.g. vertices making up faces with opposite normals don't get merged unless they
    # form a boundary of the polygon
    # So in this process, we'll also calculate the face normals and centres
    loop_candidates = []
    for triangle_idx, triangle in enumerate(triangles):
        vert_positions = [np.array(vertex_positions[vert_idx]) for vert_idx in triangle]
        edge_1 = vert_positions[1] - vert_positions[0]
        edge_2 = vert_positions[2] - vert_positions[1]
        
        face_normal = np.cross(edge_1, edge_2)
        face_centre = np.mean(vert_positions, axis=0)
        for vert_idx in triangle:
            # TODO: used_vertices.add(vert_idx)
            loop_candidates.append(LoopCandidate(vert_idx, triangle_idx, face_normal, face_centre))

    # Now, loop over the loop candidates and collect them by position, indices, and weights
    # We'll split these collections by face normals after the collections have been populated
    # Can this list be 'consumed' element-by-element by popping elements off the front to waste less memory?
    grouped_loop_candidates = {}
    for loop_candidate in loop_candidates:
        vert_id = loop_candidate.vert_id
        pos     = tuple(vertex_positions[vert_id])
        indices = tuple(vertex_indices[vert_id])
        weights = tuple(vertex_weights[vert_id])
        key = (pos, indices, weights)
        if key not in grouped_loop_candidates:
            grouped_loop_candidates[key] = []
        grouped_loop_candidates[key].append(loop_candidate)

    # Now build the final list of unique loops going into each vertex - these will form the basis of the Blender loops
    new_vertices = []
    old_facevert_to_new_vert = {}
    for (position, indices, weights), candidate_group in grouped_loop_candidates.items():
        # TODO: If any duplicate planes exist, they need to be separated here
        # Do this by first checking if any face centres are the same,
        # and for those faces check if all the vertex positions are the same
        all_centres = np.array([candidate_loop.face_centre for candidate_loop in candidate_group])
        
        # Now find the plane closest to all the face centres
        # We'll store this as the associated covector; i.e. the plane normal
        plane_basis = np.linalg.svd((all_centres - np.mean(all_centres, axis=0)).T)[0]
        covector = plane_basis[:, -1]
        
        # This covector defines a plane of separation we can use to split the candidate loops into two groups: aligned
        # with and anti-aligned with the plane of separation normal
        # Basically, if we have two surfaces directly on top of each other but with opposite normals,
        # this technique will allow us to separate which loop candidates should go into the "upper" surface and which
        # should go into the "lower" surface
        
        start_idx = len(new_vertices)
        group_1 = []
        group_2 = []
        for old_facevertex in candidate_group:
            test_normal = old_facevertex.face_normal
            (group_1 if np.dot(covector, test_normal) >= 0 else group_2).append(old_facevertex)
        
        # Ensure that group 1 will always have at least one element in it
        # This just means the following code can be written with the assumption that group_1 is never empty
        if len(group_2) > len(group_1):
            group_1, group_2 = group_2, group_1
        
        # Finally, output the merged vertex (and one for the lower surface if required)
        new_vertices.append(BlenderVertexInfo(position, indices, weights))
        for old_facevert in group_1:
            old_facevert_to_new_vert[(old_facevert.face_id, old_facevert.vert_id)] = start_idx
        if len(group_2):
            # Requires duplicate lower surface vertex
            new_vertices.append(BlenderVertexInfo(position, indices, weights))
            for old_facevert in group_2:
                old_facevert_to_new_vert[(old_facevert.face_id, old_facevert.vert_id)] = start_idx + 1

    # Now we can generate some new triangles based on our merged vertices
    new_triangles = []
    new_facevert_to_old_facevert_map = {}
    for face_id, triangle in enumerate(triangles):
        new_triangle = []
        for vert_id in triangle:
            new_vert_id = old_facevert_to_new_vert[(face_id, vert_id)]
            new_triangle.append(new_vert_id)
            new_facevert_to_old_facevert_map[(face_id, new_vert_id)] = (face_id, vert_id)
        new_triangles.append(new_triangle)

    # TODO: Add in loose vertices
    # # Finally, let's add back in any vertices that weren't merged
    # for vert_idx in range(len(vertices)):
    #     if vert_idx not in used_vertices:
    #         new_vertices.append(BlenderVertexInfo(vertex_positions[vert_idx], 
    #                                               vertex_indices[vert_idx], 
    #                                               vertex_weights[vert_idx]))

    return new_vertices, new_triangles, new_facevert_to_old_facevert_map


def unmerged_vertices(vertex_positions, vertex_indices, vertex_weights, triangles):
    """
    Returns the same input vertices and triangles in a library-compatible format.
    """
    new_vertices = []
    for vert_idx in range(len(vertex_positions)):
        pos     = vertex_positions[vert_idx]
        indices = vertex_indices[vert_idx]
        weights = vertex_weights[vert_idx]
        new_vertices.append(BlenderVertexInfo(pos, indices, weights))
    new_facevert_to_old_facevert_map = {}
    for face_id, triangle in enumerate(triangles):
        for vert_id in triangle:
            new_facevert_to_old_facevert_map[(face_id, vert_id)] = (face_id, vert_id)
    return new_vertices, triangles, new_facevert_to_old_facevert_map


def try_merge_vertices(vertex_positions, vertex_indices, vertex_weights, triangles, ignored_vertices=None, attempt_merge=True, errorlog=None):
    """
    Given a list of input vertices and polygons, merge vertices with the same position attribute with face normals
    within 90 degrees of the normal of the best-fitting plane of the centres of all faces associated with that position.
    Outputs:
    a list of positions, bone indices, and bone weights to be turned into Blender vertices,
    a list of triangles mapped to the new vertices,
    a map of (new_face_idx, new_vert_idx) to (old_face_idx, old_vert_idx)
    """ 
    exception_generated = False
    try:
        if attempt_merge:
            return merge_vertices(vertex_positions, vertex_indices, vertex_weights, triangles, ignored_vertices)
    except Exception as e:
        if errorlog is None:
            print(''.join(traceback.TracebackException.from_exception(e).format()))
        else:
            errorlog.log_warning_message(f"Vertex merging failed because '{str(e)}'- falling back to unmerged vertices.")
        exception_generated = True
    
    if not attempt_merge or exception_generated:
        return unmerged_vertices(vertex_positions, vertex_indices, vertex_weights, triangles)


class ConstructedMeshInfo:
    def __init__(self, bpy_mesh, vertices, faces, map_of_loops_to_model_verts):
        self.bpy_mesh = bpy_mesh
        self.vertices = vertices
        self.faces    = faces
        
        self.map_of_loops_to_model_verts = map_of_loops_to_model_verts


def create_merged_mesh(mesh_name, vertex_positions, vertex_indices, vertex_weights, faces, sanitize_vertices=True, attempt_merge=True, errorlog=None):
    if sanitize_vertices:
        bad_vertices = sanitize_mergeable_vertices(vertex_positions, vertex_indices, vertex_weights)
    else:
        bad_vertices = None
    new_verts, new_faces, new_facevert_to_old_facevert_map = try_merge_vertices(vertex_positions, vertex_indices, vertex_weights, faces, bad_vertices, attempt_merge, errorlog)
    new_vertex_positions = [v.position for v in new_verts]

    ###############
    # CREATE MESH #
    ###############
    # Init mesh
    bpy_mesh = bpy.data.meshes.new(name=mesh_name)
    bpy_mesh.from_pydata(new_vertex_positions, [], new_faces)
    
    #################
    # ADD LOOP DATA #
    #################
    # Get the loop data
    map_of_loops_to_model_verts = {}
    for new_poly_idx, poly in enumerate(bpy_mesh.polygons):
        for loop_idx in poly.loop_indices:
            new_vert_idx = bpy_mesh.loops[loop_idx].vertex_index
            # Take only the vert id from the old (face_id, vert_id) pair
            old_vert_idx = new_facevert_to_old_facevert_map[(new_poly_idx, new_vert_idx)][1]
            map_of_loops_to_model_verts[loop_idx] = old_vert_idx
    
    return ConstructedMeshInfo(bpy_mesh, 
                               new_verts,
                               new_faces,
                               map_of_loops_to_model_verts)
