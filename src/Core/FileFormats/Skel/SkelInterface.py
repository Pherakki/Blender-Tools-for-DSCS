from .SkelBinary import SkelBinary, BoneTransforms
from ...serialization.BinaryTargets import OffsetTracker
import struct


class SkelInterface:
    def __init__(self):
        self.bones = []
        self.float_channels = []

    @property
    def bone_count(self):
        return len(self.bones)

    @property
    def float_channel_count(self):
        return len(self.float_channels)

    @classmethod
    def from_file(cls, path):
        sb = SkelBinary()
        sb.read(path)
        return cls.from_binary(sb)

    @classmethod
    def from_binary(cls, sb):
        instance = cls()
        instance.bones = []
        for name_hash, parent, transforms in zip(sb.bone_name_hashes, sb.parent_bones, sb.bone_transforms):
            b = Bone()
            b.name_hash = name_hash
            b.parent    = parent
            b.quat      = transforms.quat.data
            b.pos       = transforms.pos
            b.scale     = transforms.scale
            instance.bones.append(b)

        for data_line in sb.parent_bone_datalines:
            for child, parent in zip(data_line[0::2], data_line[1::2]):
                instance.bones[child].flag = (parent & 0x8000) >> 15

        for name_hash, flags, index in zip(sb.float_channel_object_name_hashes, sb.float_channel_flags, sb.float_channel_array_indices):
            fc = FloatChannel()
            fc.name_hash = name_hash
            fc.flags = flags
            fc.array_index = index
            instance.float_channels.append(fc)

        return instance

    def to_file(self, path):
        sb = self.to_binary()
        sb.write(path)

    def to_binary(self):
        sb = SkelBinary()

        # Temporarily set some variables to satisfy an internal consistency check
        sb.filesize = 0
        sb.bone_name_hashes_offset = 0
        sb.hashes_section_bytecount = 0

        # Data
        sb.bone_name_hashes      = [b.name_hash for b in self.bones]
        sb.parent_bones          = [b.parent for b in self.bones]
        sb.parent_bone_datalines = gen_bone_hierarchy({i: p for i, p in enumerate(sb.parent_bones)})
        sb.bone_transforms       = [BoneTransforms.from_transforms(b.quat, b.pos, b.scale) for b in self.bones]

        for data_line in sb.parent_bone_datalines:
            for i, (child, parent) in enumerate(zip(data_line[0::2], data_line[1::2])):
                # Inject flag
                # + 0x8000, & 0x7FFF stuff is just to convert -1 to 0x7FFF and leave all else unchanged
                data_line[i*2 + 1] = struct.unpack('h', struct.pack('H', ((parent + 0x8000) & 0x7FFF) | (self.bones[child].flag << 15)))[0]

        sb.float_channel_flags              = [fc.flags for fc in self.float_channels]
        sb.float_channel_array_indices      = [fc.array_index for fc in self.float_channels]
        sb.float_channel_object_name_hashes = [fc.name_hash for fc in self.float_channels]

        # Offsets / Sizes
        sb.bone_count = len(self.bones)
        sb.float_channel_count = len(self.float_channels)
        sb.parent_bone_dataline_count = len(sb.parent_bone_datalines)

        ot = OffsetTracker()
        ot.rw_obj_method(sb, sb.rw_header)
        ot.rw_obj_method(sb, sb.rw_parent_bone_datalines)
        sb.bone_transforms_offset             = ot.tell(); ot.rw_obj_method(sb, sb.rw_bone_transforms)
        sb.parent_bones_offset                = ot.tell(); ot.rw_obj_method(sb, sb.rw_parent_bones)
        sb.float_channel_flags_offset         = ot.tell(); ot.rw_obj_method(sb, sb.rw_float_channel_flags)

        hashes_section_start = ot.tell()
        sb.bone_name_hashes_offset            = ot.tell(); ot.rw_obj_method(sb, sb.rw_bone_name_hashes)
        sb.float_channel_array_indices_offset = ot.tell(); ot.rw_obj_method(sb, sb.rw_float_channel_array_indices)
        sb.float_channel_name_hashes_offset   = ot.tell(); ot.rw_obj_method(sb, sb.rw_float_channel_object_names)

        # Counts
        sb.filesize = ot.tell()
        sb.hashes_section_bytecount = sb.filesize - hashes_section_start

        return sb


class Bone:
    def __init__(self):
        self.name_hash = None
        self.flag      = None
        self.parent    = None
        self.quat      = None
        self.pos       = None
        self.scale     = None


class FloatChannel:
    def __init__(self):
        self.name_hash   = None
        self.flags       = None
        self.array_index = None


def gen_bone_hierarchy(parent_bones):
    to_return = []
    parsed_bones = []
    bones_left_to_parse = [bidx for bidx in parent_bones]
    while len(bones_left_to_parse) > 0:
        hierarchy_line, new_parsed_bone_idxs = gen_bone_hierarchy_line(parent_bones, parsed_bones, bones_left_to_parse)
        to_return.append(hierarchy_line)

        for bidx in new_parsed_bone_idxs[::-1]:
            parsed_bones.append(bones_left_to_parse[bidx])
            del bones_left_to_parse[bidx]
    return to_return


def gen_bone_hierarchy_line(parent_bones, parsed_bones, bones_left_to_parse):
    """It ain't pretty, but it works"""
    to_return = []
    new_parsed_bone_idxs = []
    bone_iter = iter(bones_left_to_parse)
    prev_j = 0
    mod_j = -1
    for i in range(4):
        for j, bone in enumerate(bone_iter):
            mod_j = j + prev_j
            parent_bone = parent_bones[bone]
            if parent_bone == -1 or parent_bone in parsed_bones:
                to_return.append(bone)
                to_return.append(parent_bone)
                new_parsed_bone_idxs.append(mod_j)
                prev_j = mod_j + 1
                break
        if mod_j == len(bones_left_to_parse)-1 and len(to_return) < 8:
            to_return.extend(to_return[-2:])
    return to_return, new_parsed_bone_idxs
