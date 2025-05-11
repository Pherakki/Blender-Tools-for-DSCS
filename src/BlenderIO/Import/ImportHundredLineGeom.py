import array
import os
import numpy as np
import struct
from ...serialization.DSCSParsers import DSCSReader
from ....external.blunger.dataproc import ModelTransforms
from ....external.blunger.interface.mesh import create_merged_mesh
from ....external.blunger.interface.mesh import create_loop_normals
from ....external.blunger.interface.mesh import create_uv_map
from ....external.blunger.interface.mesh import create_color_map
from ....external.blunger.interface.object import set_active_obj
from ....external.blunger.interface.collection import init_collection
from ....external.blunger.interface.shader import ShaderNodeGenerator
from ....external.blunger.interface.armature import construct_bone, resize_bone_lengths
from ....external.blunger.interface.object import set_mode, TempSwapActiveObjectMode
from ...filetypes.Geom.Binary.HundredLine import GeomFileBinaryHundredLine, AttributeTypes, PrimitiveTypes
from ...filetypes.Anim.InterfaceHundredLine import AnimFileHundredLine
from ...filetypes.Anim.BinaryHundredLine import AnimFileBinary as AnimFileBinaryHundredLine
from ...filetypes.NameList.Interface import NameList
from ...filetypes.Skel.Interface import SkelFile
from ...utilities.Hash import dscs_hash
from ...filetypes.Texture.DDS import DDS, to_nonsrgb_dds
from mathutils import Matrix
from .Data.Animation import import_base_animation
from .Data.Animation import import_animations

import numpy as np
import bpy

NAMESPACE = "mvgltools"

MODEL_TRANSFORMS = ModelTransforms(world_axis=['X', 'Z', '-Y'], 
                                   bone_axis=['X', 'Y', 'Z'])

class MergedVertex:
    # Specialized implementation
    def __init__(self, position, indices, weights):
        self.position = position[:3]
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

def to_triangles(buffer):
    out = []
    for i, (t1, t2, t3) in enumerate(zip(buffer[0:], buffer[1:], buffer[2:])):
        if len({t1, t2, t3}) < 3:
            continue
        if i % 2:
            out.extend((t2, t1, t3))
        else:
            out.extend((t1, t2, t3))
    return out



def rebuild_basic_tree(bpy_material, tex):
    node_tree = bpy_material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    connect = links.new

    # Wipe tree
    nodes.clear()
    bpy_material.show_transparent_back = True
    
    sg = ShaderNodeGenerator(bpy_material.node_tree)
    RGBA = None
    color_sampler = None
    clut_sampler = None
    
    # Samplers
    if tex is not None:
        color_sampler = sg.texture_sampler("ColorSampler", tex)

    if color_sampler is not None:
        sg.export_surface(color_sampler.color)
        

def import_materials(geom, directory, errorlog, rename_imgs, use_custom_nodes):
    texture_bank = {}
    
    materials = []
    
    mat_hash_lookup = {}
    for mat_offset in geom.name_offsets.material_name_offsets:
        matname = geom.get_string(mat_offset)
        mathash = dscs_hash(matname)
        mat_hash_lookup[mathash] = matname.decode("ascii")
    
    for material in geom.materials:
        # We can figure out the name of the material by hash-matching in a future update.
        material_name = mat_hash_lookup[material.name_hash] # geom.get_string(material.name_offset)
        
        bpy_material = bpy.data.materials.new(name=material_name)
        materials.append(bpy_material)

        # Load up any custom properties we need
        bpy_material.use_backface_culling = True

        # Import extra material data
        tex = None
        for uniform in material.uniforms:
            if uniform.index == 0x18:
                tex_offset = uniform.unpack()[0]
                tex = import_image(geom, tex_offset, texture_bank, directory)
                break

        bpy_material.use_nodes = True
        rebuild_basic_tree(bpy_material, tex)
    
    return materials
        


def import_image(geom, tex_offset, texture_bank, directory):
    if tex_offset in texture_bank:
        return texture_bank[tex_offset]
    else:
        texture_name = geom.get_string(tex_offset).decode("ascii")
        img_path = os.path.join(directory, "images", (texture_name + ".img").lower())

        if os.path.isfile(img_path):
            dds = DDS()
            dds.read(img_path)
            srgb = to_nonsrgb_dds(dds)
            
            
            tmp_filepath = os.path.join(bpy.app.tempdir, texture_name)
            
            try:
                dds.write(tmp_filepath)
                texture_bank[tex_offset] = bpy.data.images.load(tmp_filepath)
                img = texture_bank[tex_offset]
                img.pack()
                img.filepath_raw = texture_name
            finally:
                os.remove(tmp_filepath)
            
            # texture_bank[tex_offset] = bpy.data.images.new(texture_name, img.width, img.height)
            # tex = texture_bank[tex_offset]
            # arr = np.array(array.array('B', img.tobytes())) / 255
            # tex.pixels[:] = arr
            # # tex.name = os.path.splitext(tex.name)[0]
            return img
        else:
            raise ValueError(f"Missing texture {img_path}")

def import_skeleton(geom, armature_name, collection):
    bone_hash_lookup = {}
    bone_names = []
    for bone_offset in geom.name_offsets.bone_name_offsets:
        bone_name = geom.get_string(bone_offset)
        bone_hash = dscs_hash(bone_name)
        bone_hash_lookup[bone_hash] = bone_name.decode("ascii")
        
        bone_names.append(bone_name.decode("ascii"))
    
    bpy_armature_object = bpy.data.objects.new(armature_name, bpy.data.armatures.new(armature_name))
    collection.objects.link(bpy_armature_object)
    
    set_active_obj(bpy_armature_object)
    set_mode("OBJECT")
    with TempSwapActiveObjectMode('EDIT'):
        # Get IBPMs
        list_of_bones = {}
        dscs_to_bpy_bone_map = {}
        bpms = [Matrix([m[0:4],
                        m[4:8],
                        m[8:12],
                        [0., 0., 0., 1.]]).inverted() for m in geom.ibpms]
        
        parent_lookup = {}
        for bidx, pidx in geom.skel.bone_parent_vectors:
            parent_lookup[bidx] = pidx
        
        for bone_idx, (bone_hash, bpm) in enumerate(zip(geom.skel.bone_name_hashes, bpms)):
            bone_name = bone_hash_lookup[bone_hash]
            
            # Throw warning if there is a hash collision
            dscs_to_bpy_bone_map[bone_hash] = len(list_of_bones)
            
            bpy_bone = construct_bone(bone_name, bpy_armature_object, MODEL_TRANSFORMS.transform_bone_matrix4x4(bpms[bone_idx]), 1)
            list_of_bones[bone_idx] = bpy_bone
            
            parent = parent_lookup[bone_idx]
            if parent != 0x7FFF:
                bpy_bone.parent = list_of_bones[parent & 0x7FFF]

    # Edit bone lengths
    model_dims = [e*2 for e in geom.bounding_box_diagonal]
    if all(e < 0.0001 for e in model_dims):
        model_dims = [10., 10., 10.]
    resize_bone_lengths(bpy_armature_object, default_size=[.1*d for d in model_dims], min_bone_length=0.01)
    
    return bpy_armature_object, bone_names
    

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


def add_rest_pose_to_base_anim(si, base_animation):
    for bone_idx, bone in enumerate(si.bones):
        if not len(base_animation.rotations[bone_idx]):
            base_animation.rotations[bone_idx][0] = bone.quat
        if not len(base_animation.positions[bone_idx]):
            base_animation.positions[bone_idx][0] = bone.pos
        if not len(base_animation.scales[bone_idx]):
            base_animation.scales[bone_idx][0] = bone.scale


def import_hl_geom(filepath, errorlog):
    stem = os.path.splitext(filepath)[0]
    model_name = os.path.split(stem)[1]
    
    collection = init_collection(model_name)
    geom = GeomFileBinaryHundredLine()
    geom.read(filepath)
    
    nlst = NameList.from_file(stem + ".nlst")
    mesh_name_lookup = {dscs_hash(n._name_bytes): n.name for n in nlst.mesh_names}
    
    material_list = import_materials(geom, os.path.split(filepath)[0], errorlog, False, True)
    bpy_armature_object, bone_names = import_skeleton(geom, model_name, collection)
    for i, mesh in enumerate(geom.meshes):
        #################
        # PURE GEOMETRY #
        #################
        # First get the primitives
        mesh_primitive_type = mesh.PRIMITIVE_TYPES.get(mesh.primitive_type)
        if mesh_primitive_type == PrimitiveTypes.TRIANGLES:
            buffer = mesh.index_buffer
            faces = [(a,b,c) for a,b,c in zip(buffer[0::3],buffer[1::3], buffer[2::3])]
        elif mesh_primitive_type == PrimitiveTypes.TRIANGLE_STRIP:
            buffer = to_triangles(mesh.index_buffer)
            faces = [(a,b,c) for a,b,c in zip(buffer[0::3],buffer[1::3], buffer[2::3])]
        else:
            errorlog.log_error_message(f"Primitive Type '{mesh.primitive_type}', found on mesh {i}, is not supported")
        
        ###############
        # CREATE MESH #
        ###############
        # Init mesh
        if mesh.name_offset == 0:
            meshobj_name = mesh_name_lookup[mesh.name_hash]
        else:
            meshobj_name = geom.get_string(mesh.name_offset).decode('ascii')
        
        vertices = mesh.unpack_vertices()
        
        if mesh.vertex_groups_per_vertex == 0:
            for vidx in range(len(vertices)):
                vertices[vidx].indices = [0]
                vertices[vidx].weights = [1.0]
        elif mesh.vertex_groups_per_vertex == 1:
            for vidx, v in enumerate(vertices):
                vertices[vidx].indices = [int(v.position[3])]
                vertices[vidx].weights = [1.0]
        else:
            if vertices[0].indices is None:
                assert 0
            
        for vidx, v in enumerate(vertices):
            vertices[vidx].indices = [mesh.matrix_palette[idx] for idx in v.indices]
            
        mesh_info    = create_merged_mesh(meshobj_name, 
                                          vertices,
                                          faces,
                                          MergedVertex,
                                          attempt_merge=True,
                                          errorlog=errorlog)
        
        bpy_mesh = mesh_info.bpy_mesh
        bpy_mesh_object = bpy.data.objects.new(meshobj_name, bpy_mesh)
        collection.objects.link(bpy_mesh_object)

        # Assign materials
        active_material = material_list[mesh.material_idx]
        bpy_mesh_object.active_material = active_material

        set_active_obj(bpy_mesh_object)
        
        #################
        # ADD LOOP DATA #
        #################
        # Assign UVs
        for uv_idx, uv_type in enumerate([AttributeTypes.UV1, AttributeTypes.UV2, AttributeTypes.UV3]):
            if vertices[0][uv_type] is not None:
                #create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type][0], 1-l[uv_type][1]) for l in mesh_info.loops))
                create_uv_map(bpy_mesh, f"UV{uv_idx + 1}", ((l[uv_type]) for l in mesh_info.loops))

        # Assign vertex colours
        if vertices[0][AttributeTypes.COLOR] is not None:
            create_color_map(bpy_mesh, "ColorMap", [l.color for l in mesh_info.loops], "FLOAT")

        ###########
        # RIGGING #
        ###########
        if mesh_info.vertices[0].indices is not None:
            vertex_groups = make_vertex_groups(mesh_info.vertices)
            for bone_idx, vg in vertex_groups.items():
                vertex_group = bpy_mesh_object.vertex_groups.new(name=bone_names[bone_idx])
                for vert_idx, vert_weight in vg:
                    vertex_group.add([vert_idx], vert_weight, 'REPLACE')

        ################
        # ADD MISC DATA #
        #################
        # Load the hashed mesh name
        # signed_hash = struct.unpack('i', struct.pack('I', mesh.name_hash))[0]
        # bpy_mesh_object.data.DSCS_MeshProperties.name_hash = signed_hash

        # Set armature constraint
        bpy_mesh_object.parent = bpy_armature_object
        modifier = bpy_mesh_object.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = bpy_armature_object

        # Assign normals
        # Do this LAST because it can remove some loops
        if vertices[0][AttributeTypes.NORMAL] is not None:
            create_loop_normals(bpy_mesh, (l.normal for l in mesh_info.loops))

        # Tell Blender what we've done
        bpy_mesh.validate(verbose=True, clean_customdata=False)
        bpy_mesh.update()
        bpy_mesh.update()

        # Convert meshes Y up -> Z up
        bpy_mesh.transform(MODEL_TRANSFORMS.world_axis_rotation.matrix4x4)

        # meshes.append(bpy_mesh)

    base_anim = load_hl_anim_file(os.path.splitext(filepath)[0] + ".anim")
    si = SkelFile.from_binary(geom.skel)
    
    add_rest_pose_to_base_anim(si, base_anim)
    
    import_base_animation(model_name, bpy_armature_object, [b.encode('ascii') for b in bone_names], base_anim, errorlog)

def load_hl_anim_file(filepath):
    ab = AnimFileBinaryHundredLine()
    ab.read(filepath)
    return AnimFileHundredLine.from_binary(ab)

def import_hl_anim(bpy_armature_obj, filepath, errorlog):
    bone_names = [b.name for b in bpy_armature_obj.data.bones]
    anim_name = os.path.split(os.path.splitext(filepath)[0])[1]
    ais = {anim_name: load_hl_anim_file(filepath)}
    import_animations(bpy_armature_obj.name, bpy_armature_obj, [b.encode('ascii') for b in bone_names], ais, errorlog)
