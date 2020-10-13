from ..FileReaders.NameReader import NameReader
from ..FileReaders.SkelReader import SkelReader
from ..FileReaders.GeomReader import GeomReader
from .IntermediateFormat import IntermediateFormat

import os


def generate_intermediate_format_from_files(filepath):
    """
    Opens name, skel, and geom files associated with the given filename and generates an IntermediateFormat object.
    Images are assumed to be in a sub-directory of the given file's directory named 'images'.

    Returns
    ------
    An IntermediateFormat representation of the data.
    """
    with open(filepath + '.name', 'rb') as F:
        imported_namedata = NameReader(F)
        imported_namedata.read()
    with open(filepath + '.skel', 'rb') as F:
        imported_skeldata = SkelReader(F)
        imported_skeldata.read()
    with open(filepath + '.geom', 'rb') as F:
        imported_geomdata = GeomReader(F)
        imported_geomdata.read()

    images_directory = os.path.join(*os.path.split(filepath)[:-1], 'images')

    model_data = IntermediateFormat()
    add_meshes(model_data, imported_geomdata)
    add_materials(model_data, imported_namedata, imported_geomdata, os.path.split(filepath)[-1])
    add_textures(model_data, imported_geomdata, images_directory)
    add_skeleton(model_data, imported_namedata, imported_skeldata, imported_geomdata)

    return model_data


##################################
#  Polygon data type converters  #
##################################
def triangle_strips_to_polys(idxs):
    triangles = []
    for i, tri in enumerate(zip(idxs, idxs[1:], idxs[2:])):
        order = i % 2
        tri = (tri[0 + order], tri[1 - order], tri[2])
        triangle = set(tri)
        if not (len(triangle) != 3 or tri in triangles):
            triangles.append(tri)
    return triangles


def triangles_to_polys(idxs):
    triangles = []
    for tri, (idx_a, idx_b, idx_c) in enumerate(zip(idxs[::3], idxs[1::3], idxs[2::3])):
        triangles.append((idx_a, idx_b, idx_c))
    return triangles


triangle_converters = {'Triangles': triangles_to_polys,
                       'TriangleStrips': triangle_strips_to_polys}


##############################
#  Factory helper functions  #
##############################
def add_meshes(model_data, imported_geomdata):
    for mesh in imported_geomdata.meshes:
        model_data.new_mesh()
        current_IF_mesh = model_data.meshes[-1]
        for bone_id in mesh.weighted_bone_idxs:
            current_IF_mesh.add_vertex_group(bone_id, [], [])

        for i, vertex in enumerate(mesh.vertex_data):
            pos = vertex.get('Position')
            if len(pos) > 3:
                assert 0
            norm = vertex.get('Normal')
            uv = vertex.get('UV')
            vgroups = vertex.get('WeightedBoneID')
            weights = vertex.get('BoneWeight')
            if uv is not None:
                uv = (uv[0], 1 - uv[-1])
            if 'WeightedBoneID' in vertex:
                for j, (three_x_bone_id, weight) in enumerate(zip(vgroups, weights)):
                    if weight == 0:
                        continue
                    vertex_group_idx = three_x_bone_id // 3
                    vgroups[j] = vertex_group_idx
                    current_IF_mesh.vertex_groups[vertex_group_idx].vertex_indices.append(i)
                    current_IF_mesh.vertex_groups[vertex_group_idx].weights.append(weight)
            current_IF_mesh.add_vertex(pos, norm, uv, vgroups, weights)

        triangles = triangle_converters[mesh.polygon_data_type](mesh.polygon_data)
        for tri in triangles:
            current_IF_mesh.add_polygon(tri)
        current_IF_mesh.material_id = mesh.material_id

        # Add unknown data
        current_IF_mesh.unknown_data['unknown_0x30'] = mesh.unknown_0x30
        current_IF_mesh.unknown_data['unknown_0x31'] = mesh.unknown_0x31
        current_IF_mesh.unknown_data['unknown_0x34'] = mesh.unknown_0x34
        current_IF_mesh.unknown_data['unknown_0x36'] = mesh.unknown_0x36
        current_IF_mesh.unknown_data['unknown_0x44'] = mesh.unknown_0x44
        current_IF_mesh.unknown_data['unknown_0x50'] = mesh.unknown_0x50
        current_IF_mesh.unknown_data['unknown_0x5C'] = mesh.unknown_0x5C

        model_data.meshes[-1] = current_IF_mesh
    model_data.unknown_data['geom_unknown_0x14'] = imported_geomdata.unknown_0x14
    model_data.unknown_data['geom_unknown_0x20'] = imported_geomdata.unknown_0x20

    model_data.unknown_data['unknown_cam_data_1'] = imported_geomdata.unknown_cam_data_1
    model_data.unknown_data['unknown_cam_data_2'] = imported_geomdata.unknown_cam_data_2

    model_data.unknown_data['unknown_footer_data'] = imported_geomdata.unknown_footer_data


def add_materials(model_data, imported_namedata, imported_geomdata, filename):
    #assert len(imported_namedata.material_names) == len(imported_geomdata.material_data), \
    #    f"Mismatch between material names and unique material data. {len(imported_namedata.material_names)} {len(imported_geomdata.material_data)}"
    model_data.unknown_data['material names'] = imported_namedata.material_names
    for i, material in enumerate(imported_geomdata.material_data):
        model_data.new_material()
        # I can't figure out how to match up the material names to the materials yet when there are fewer names than materials
        model_data.materials[-1].name = filename + "_mat_{:03d}".format(i)  # str(i)  # model_data.unknown_data['material names'][i]

        # Add unknown data
        model_data.materials[-1].unknown_data['unknown_0x00'] = material.unknown_0x00
        model_data.materials[-1].unknown_data['unknown_0x10'] = material.unknown_0x10
        model_data.materials[-1].unknown_data['unknown_0x11'] = material.unknown_0x11
        model_data.materials[-1].unknown_data['unknown_0x12'] = material.unknown_0x12
        model_data.materials[-1].unknown_data['unknown_0x16'] = material.unknown_0x16

        for i, material_component in enumerate(material.material_components):
            # Appears to mark the block as identifying a texture ID
            if material_component.component_type == 50:
                model_data.materials[-1].texture_id = material_component.data[0]
            elif material_component.component_type == 51:
                model_data.materials[-1].rgba = material_component.data
            elif material_component.component_type == 56:
                model_data.materials[-1].specular_coeff = material_component.data[0]
            model_data.materials[-1].unknown_data[f'type_1_component_{material_component.component_type}'] = material_component.data

        for i, material_component in enumerate(material.unknown_data):
            model_data.materials[-1].unknown_data[f'type_2_component_{material_component.maybe_component_type}'] = material_component.data


def add_textures(model_data, imported_geomdata, image_folder_path):
    for texture in imported_geomdata.texture_data:
        directory = os.path.join(image_folder_path, texture) + ".img"
        model_data.new_texture()
        model_data.textures[-1].name = texture
        model_data.textures[-1].filepath = directory


def add_skeleton(model_data, imported_namedata, imported_skeldata, imported_geomdata):
    model_data.skeleton.bone_names = imported_namedata.bone_names
    model_data.skeleton.bone_relations = imported_skeldata.parent_bones
    for bone_data in imported_geomdata.bone_data:
        position = (-bone_data.xpos, -bone_data.ypos, -bone_data.zpos)
        model_data.skeleton.bone_positions.append(position)
        model_data.skeleton.bone_xvecs.append((bone_data.unknown_0x00, bone_data.unknown_0x04, bone_data.unknown_0x08))
        model_data.skeleton.bone_yvecs.append((bone_data.unknown_0x0C, bone_data.unknown_0x10, bone_data.unknown_0x14))
        model_data.skeleton.bone_zvecs.append((bone_data.unknown_0x1A, bone_data.unknown_0x1E, bone_data.unknown_0x22))

    # Put the unknown data into the skeleton
    model_data.skeleton.unknown_data['unknown_0x0C'] = imported_skeldata.unknown_0x0C
    model_data.skeleton.unknown_data['unknown_parent_child_data'] = imported_skeldata.unknown_parent_child_data
    model_data.skeleton.unknown_data['bone_data'] = imported_skeldata.bone_rotation_quaternions_xyz
    model_data.skeleton.unknown_data['unknown_data_1'] = imported_skeldata.unknown_data_1
    model_data.skeleton.unknown_data['unknown_data_2'] = imported_skeldata.unknown_data_2
    model_data.skeleton.unknown_data['unknown_data_3'] = imported_skeldata.unknown_data_3
    model_data.skeleton.unknown_data['unknown_data_4'] = imported_skeldata.unknown_data_4
