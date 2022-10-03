from ...serialization.Serializable import Serializable


class SkelFile(Serializable):
    """
    A class to read skel files. These files are split into eight main sections:
        1. The header, which gives file pointers to split the file into its major sections, plus counts of what appears
           in each section.
        2. Pairs of bone indices that create parent-bone relationships procedurally, 8 int16s per element
        3. A section of 12 floats per bone
        4. A section of 1 int16 per bone that gives the parent of each bone
        5. A section of one-multiple-of-8 per shader uniform channel
        6. A section of 4 bytes per bone
        7. A section of 1 uint32 per user channel, identifying which shader uniform the channel is for.
        8. A section of material/camera/light name hashes for the shader uniform channels.

    Completion status
    ------
    (o) SkelReader can successfully parse all name files in DSDB archive within current constraints.
    (x) SkelReader cannot yet fully interpret all data in name files in DSDB archive.
    (o) SkelReader can write data to skel files.

    Current hypotheses and observations
    ------
    1. Currently not 100% clear what the 0/8/16 per shader uniform channel is for, but is connected to the type...
       could be a flag?
    """
    def __init__(self):
        super().__init__()

        # Variables that appear in the file header
        self.filetype = None
        self.total_bytes = None
        self.remaining_bytes_after_parent_bones_chunk = None
        self.num_bones = None
        self.num_uv_channels = None
        self.num_bone_hierarchy_data_lines = None

        self.rel_ptr_to_end_of_bone_hierarchy_data = None
        self.rel_ptr_to_end_of_bone_defs = None
        self.rel_ptr_to_end_of_parent_bones_chunk = None
        self.rel_ptr_bone_name_hashes = None
        self.unknown_rel_ptr_3 = None
        self.rel_ptr_to_end_of_parent_bones = None

        # These hold the data stored within the file
        self.bone_hierarchy_data = None
        self.bone_data = None
        self.parent_bones = None
        self.unknown_data_1 = None
        self.bone_name_hashes = None
        self.unknown_data_3 = None
        self.uv_channel_material_name_hashes = None

        # Utility variables
        self.filesize = None

        self.abs_ptr_bone_hierarchy_data = None
        self.abs_ptr_bone_defs = None
        self.abs_ptr_parent_bones = None
        self.abs_ptr_end_of_parent_bones_chunk = None
        self.abs_ptr_bone_name_hashes = None
        self.abs_ptr_unknown_3 = None
        self.abs_ptr_unknown_4 = None