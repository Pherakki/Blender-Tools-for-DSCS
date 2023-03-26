import array

from mathutils import Vector


def import_loop_normals(bpy_mesh, normals):
    """
    Loads per-loop normal vectors into a mesh.
    
    Works thanks to this stackexchange answer https://blender.stackexchange.com/a/75957,
    which a few of these comments below are also taken from.
    """
    bpy_mesh.create_normals_split()
    bpy_mesh.calc_normals_split()
    #  mesh.normals_split_custom_set( [(1, 1, 0) for v in mesh.loops] )???
    for face in bpy_mesh.polygons:
        face.use_smooth = True  # loop normals have effect only if smooth shading ?

    # Set loop normals
    loop_normals = [Vector([normal[0], normal[1], normal[2]]) for normal in normals]
    bpy_mesh.loops.foreach_set("normal", [subitem for item in loop_normals for subitem in item])

    bpy_mesh.validate(clean_customdata=False)  # important to not remove loop normals here!
    bpy_mesh.update()

    clnors = array.array('f', [0.0] * (len(bpy_mesh.loops) * 3))
    bpy_mesh.loops.foreach_get("normal", clnors)

    bpy_mesh.polygons.foreach_set("use_smooth", [True] * len(bpy_mesh.polygons))
    # This line is pretty smart (came from the stackoverflow answer)
    # 1. Creates three copies of the same iterator over clnors
    # 2. Splats those three copies into a zip
    # 3. Each iteration of the zip now calls the iterator three times, meaning that three consecutive elements
    #    are popped off
    # 4. Turn that triplet into a tuple
    # In this way, a flat list is iterated over in triplets without wasting memory by copying the whole list
    bpy_mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))

    bpy_mesh.use_auto_smooth = True


def create_uv_map(bpy_mesh, name, uvs):
    uv_layer = bpy_mesh.uv_layers.new(name=name, do_init=True)
    for loop_idx, (loop, (u, v)) in enumerate(zip(bpy_mesh.loops, uvs)):
        uv_layer.data[loop_idx].uv = (u, v)
