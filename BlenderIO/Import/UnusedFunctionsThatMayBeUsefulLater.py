def build_loops_and_verts(self, model_vertices, model_polygons):
    # Currently unused because it doesn't distinguish overlapping polygons with the same vertices but different vertex orders
    set_compliant_model_vertex_positions = [tuple(vert['Position']) for vert in model_vertices]
    verts = set(set_compliant_model_vertex_positions)
    verts = list(verts)

    map_of_model_verts_to_verts = {i: verts.index(vert) for i, vert in
                                   enumerate(set_compliant_model_vertex_positions)}

    map_of_loops_to_model_vertices = {}
    polys = []
    for poly_idx, poly in enumerate(model_polygons):
        poly_verts = []
        for model_vertex_idx in poly.indices:
            vert_idx = map_of_model_verts_to_verts[model_vertex_idx]
            map_of_loops_to_model_vertices[(poly_idx, vert_idx)] = model_vertex_idx
            poly_verts.append(vert_idx)
        polys.append(poly_verts)

    return verts, polys, map_of_loops_to_model_vertices, map_of_model_verts_to_verts


    # Merge this with import_skeleton
def import_rest_pose_skeleton(parent_obj, armature_name, model_data):
    model_armature = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    bpy.context.collection.objects.link(model_armature)
    model_armature.parent = parent_obj

    # Rig
    list_of_bones = {}

    bpy.context.view_layer.objects.active = model_armature
    bpy.ops.object.mode_set(mode='EDIT')

    bone_matrices = model_data.skeleton.rest_pose
    for i, relation in enumerate(model_data.skeleton.bone_relations):
        child, parent = relation
        child_name = model_data.skeleton.bone_names[child]
        if child_name in list_of_bones:
            continue

        bone_matrix = bone_matrices[i]
        bone = model_armature.data.edit_bones.new(child_name)

        list_of_bones[child_name] = bone
        bone.head = np.array([0., 0., 0.])
        bone.tail = np.array([0., 0.2, 0.])  # Make this scale with the model size in the future, for convenience
        bone.transform(Matrix(bone_matrix.tolist()))

        if parent != -1:
            bone.parent = list_of_bones[model_data.skeleton.bone_names[parent]]

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = parent_obj


def import_boundboxes(model_data, filename, armature_name):
    bbox_material = bpy.data.materials.new(name='bbox_material')
    bbox_material.use_backface_culling = True
    bbox_material.blend_method = 'BLEND'
    bbox_material.use_nodes = True
    bsdf_node = bbox_material.node_tree.nodes.get('Principled BSDF')
    bsdf_node.inputs['Alpha'].default_value = 0.2
    for i, IF_mesh in enumerate(model_data.meshes):
        bbox_name = f"{filename}_{i}_boundingbox"
        bbox_mesh = bpy.data.meshes.new(name=bbox_name)
        bbox_mesh_object = bpy.data.objects.new(bbox_name, bbox_mesh)
        mults = [np.array([1., 1., 1.]),
                 np.array([1., 1., -1.]),
                 np.array([1., -1., -1.]),
                 np.array([1., -1., 1.]),
                 np.array([-1., 1., 1.]),
                 np.array([-1., 1., -1.]),
                 np.array([-1., -1., -1.]),
                 np.array([-1., -1., 1.])]

        bbox_verts = [Vector(np.array(IF_mesh.unknown_data['bbc']) + np.array(IF_mesh.unknown_data['bb'])*mult) for mult in mults]

        bbox_faces = [(0, 1, 2, 3), (4, 5, 6, 7),
                      (0, 1, 5, 4), (2, 3, 7, 6),
                      (3, 0, 4, 7), (1, 2, 6, 5)]

        bbox_mesh_object.data.from_pydata(bbox_verts, [], bbox_faces)
        bpy.context.collection.objects.link(bbox_mesh_object)
        bpy.data.objects[bbox_name].active_material = bpy.data.materials['bbox_material']

        bpy.data.objects[bbox_name].select_set(True)
        bpy.data.objects[armature_name].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[armature_name]
        bpy.ops.object.parent_set(type='ARMATURE')

        bbox_mesh.validate(verbose=True)
        bbox_mesh.update()

        bpy.data.objects[bbox_name].select_set(False)
        bpy.data.objects[armature_name].select_set(False)

def modify_animation(filename, model_data):
    # Needs to be rest pose delta?
    rest_pose = [item for item in model_data.skeleton.rest_pose_delta]
    base_animation = model_data.animations[filename]

    for bone_idx, rest_data in enumerate(rest_pose):
        fcurve = base_animation.rotations[bone_idx]
        if not len(fcurve.frames):
            fcurve.frames.append(0)
            fcurve.values.append(np.roll(rest_data[0], 1))
        fcurve = base_animation.locations[bone_idx]
        if not len(fcurve.frames):
            fcurve.frames.append(0)
            fcurve.values.append(rest_data[1])
        fcurve = base_animation.scales[bone_idx]
        if not len(fcurve.frames):
            fcurve.frames.append(0)
            fcurve.values.append(rest_data[2])

    return rest_pose

def generate_animation_shifts(self, rest_pose, inverse_bind_pose, animation_pose):
    # Can vectorise this with tensordot if the inputs are numpy arrays rather than lists of numpy arrays?
    retval = []
    for bone_rest_pose, bone_inverse_bind_pose, bone_animation_pose in zip(rest_pose, inverse_bind_pose,
                                                                           animation_pose):
        # Probably need to put the inverse bind pose & rest pose in here as well as the animation diff
        # retval.append(np.dot((bone_inverse_bind_pose), bone_rest_pose))
        retval.append(bone_rest_pose)
    return retval



def generate_shifted_animation_data(animation_name, model_data, pose_delta):
    base_animation = model_data.animations[animation_name]

    result = {'rotation_quaternion': {},
              'location': {},
              'scale': {}}

    for bone_idx, rest_data in enumerate(pose_delta):
        fcurve = base_animation.rotations[bone_idx]
        result['rotation_quaternion'][bone_idx] = {k: v for k, v in zip(fcurve.frames, fcurve.values)} if len(fcurve.frames) else {0: np.roll(rest_data[0], 1)}
        fcurve = base_animation.locations[bone_idx]
        result['location'][bone_idx] = {k: v for k, v in zip(fcurve.frames, fcurve.values)} if len(fcurve.frames) else {0: rest_data[1][:3]}
        fcurve = base_animation.scales[bone_idx]
        result['scale'][bone_idx] = {k: v for k, v in zip(fcurve.frames, fcurve.values)} if len(fcurve.frames) else {0: rest_data[2][:3]}

    return result


def set_new_shifted_animation(animation_name, model_data, shifted_animation_data):
    del model_data.animations[animation_name]
    new_anim = model_data.new_anim(animation_name)
    for bone_idx, rotation_data in shifted_animation_data['rotation_quaternion'].items():
        new_anim.add_rotation_fcurve(bone_idx, list(rotation_data.keys()), list(rotation_data.values()))
    for bone_idx, location_data in shifted_animation_data['location'].items():
        new_anim.add_location_fcurve(bone_idx, list(location_data.keys()), list(location_data.values()))
    for bone_idx, scale_data in shifted_animation_data['scale'].items():
        new_anim.add_scale_fcurve(bone_idx, list(scale_data.keys()), list(scale_data.values()))


def shift_animation_reference_frames(filename, model_data):
    pose_delta = generate_composite_pose_delta(filename, model_data)
    for animation_name in model_data.animations:
        shifted_animation_data = generate_shifted_animation_data(animation_name, model_data, pose_delta)
        set_new_shifted_animation(animation_name, model_data, shifted_animation_data)



