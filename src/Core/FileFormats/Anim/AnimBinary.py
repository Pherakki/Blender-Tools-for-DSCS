import math

from ...serialization.Serializable import Serializable


class AnimBinary(Serializable):
    """
    A class to read anim files. These files are split into eight main sections:
        1.  The header, which gives file pointers to split the file into its major sections, plus counts of what appears
            in each section.
        2.  A section that contains up to eight lists of bone indices, depending on non-zero counts in the header.
        3.  A section that defines static rotations of bones.
        4.  A section that defines static locations of bones.
        5.  A section that defines static scales of bones.
        6.  A section of static non-transform values.
        7.  A section that contains lengths and start pointers for a set of keyframe chunks.
        8.  A section that contains cumulative frame counts and number of frames per Keyframe chunk.
        9.  A section of 0s and -1s, marking which bones (if any) are not animated.
        10. A list of keyframe chunks, which contain data very similar to sections 3-6.

    Completion status
    ------
    (o) AnimReader can successfully parse all anim files in DSDB archive within current constraints.
    (o) AnimReader can fully interpret all anim data in DSDB archive.
    (o) AnimReader can write data to anim files.
    """

    @property
    def KEYFRAME_CHUNKS_OFFSETS_OFFSET_OFFSET(self): return 0x30
    @property
    def KEYFRAME_CHUNKS_COUNTS_OFFSET_OFFSET (self): return 0x34
    @property
    def STATIC_ROTATIONS_OFFSET_OFFSET       (self): return 0x38
    @property
    def STATIC_LOCATIONS_OFFSET_OFFSET       (self): return 0x3C
    @property
    def STATIC_SCALES_OFFSET_OFFSET          (self): return 0x40
    @property
    def STATIC_FLOAT_CHANNELS_OFFSET_OFFSET  (self): return 0x44

    def __init__(self, skel_binary_ref):
        super().__init__()

        self.skel_binary_ref = skel_binary_ref

        # Header variables
        self.filetype = b'40AE'
        self.animation_duration = None  # Seconds
        self.playback_rate = None  # Keyframes per second

        self.animation_masks_offset = None
        self.bone_count = None
        self.frame_count = None
        self.keyframe_chunk_count = None  # part 5 is 8x this count, part 6 is 4x this count: count of KeyframeChunks.
        self.always_0x4000 = 0x4000  # Always 0x4000; maybe the precision of the rotations

        self.static_rotations_count        = None
        self.static_locations_count        = None
        self.static_scales_count           = None
        self.static_float_channel_count    = None
        self.animated_rotations_count      = None
        self.animated_locations_count      = None
        self.animated_scales_count         = None
        self.animated_float_channel_count  = None
        self.padding_0x26                  = 0  # Always 0
        self.animation_masks_size          = None  # Specifies size of the bone mask
        self.bone_mask_offset              = None

        self.keyframe_chunks_offsets_offset = None
        self.keyframe_chunks_counts_offset  = None
        self.static_rotations_offset        = None
        self.static_locations_offset        = None
        self.static_scales_offset           = None
        self.static_float_channels_offset    = None

        # Data holders
        self.static_rotation_idxs        = None
        self.static_location_idxs        = None
        self.static_scale_idxs           = None
        self.static_float_channel_idxs   = None
        self.animated_rotation_idxs      = None
        self.animated_location_idxs      = None
        self.animated_scale_idxs         = None
        self.animated_float_channel_idxs = None

        self.static_rotations        = None
        self.static_locations        = None
        self.static_scales           = None
        self.static_float_channels   = None
        self.bone_masks              = None
        self.float_channel_masks     = None
        self.keyframe_chunks         = None

    def read_write(self, rw):
        self.rw_header(rw)
        self.rw_bone_idx_lists(rw)
        self.rw_static_rotations(rw)
        self.rw_static_locations(rw)
        self.rw_static_scales(rw)
        self.rw_static_float_channels(rw)
        self.rw_keyframe_chunk_offsets(rw)
        self.rw_keyframe_chunk_counts(rw)
        self.rw_animation_masks(rw)
        self.rw_keyframe_chunk_data(rw)
        rw.assert_at_eof()

    def rw_header(self, rw):
        rw.assert_local_file_pointer_now_at("Start of File", 0)
        self.filetype = rw.rw_bytestring(self.filetype, 4)
        rw.assert_equal(self.filetype, b"40AE")

        self.animation_duration     = rw.rw_float32(self.animation_duration)
        self.playback_rate          = rw.rw_float32(self.playback_rate)
        self.animation_masks_offset = rw.rw_uint16(self.animation_masks_offset)
        self.bone_count             = rw.rw_uint16(self.bone_count)
        self.frame_count            = rw.rw_uint16(self.frame_count)
        self.keyframe_chunk_count   = rw.rw_uint16(self.keyframe_chunk_count)
        self.always_0x4000          = rw.rw_uint16(self.always_0x4000)

        self.static_rotations_count       = rw.rw_uint16(self.static_rotations_count)
        self.static_locations_count       = rw.rw_uint16(self.static_locations_count)
        self.static_scales_count          = rw.rw_uint16(self.static_scales_count)
        self.static_float_channel_count   = rw.rw_uint16(self.static_float_channel_count)
        self.animated_rotations_count     = rw.rw_uint16(self.animated_rotations_count)
        self.animated_locations_count     = rw.rw_uint16(self.animated_locations_count)
        self.animated_scales_count        = rw.rw_uint16(self.animated_scales_count)
        self.animated_float_channel_count = rw.rw_uint16(self.animated_float_channel_count)
        self.padding_0x26                 = rw.rw_uint16(self.padding_0x26)

        self.animation_masks_size         = rw.rw_uint32(self.animation_masks_size)
        self.bone_mask_offset             = rw.rw_uint32(self.bone_mask_offset)

        self.keyframe_chunks_offsets_offset = rw.rw_offset_uint32(self.keyframe_chunks_offsets_offset, self.KEYFRAME_CHUNKS_OFFSETS_OFFSET_OFFSET)
        self.keyframe_chunks_counts_offset  = rw.rw_offset_uint32(self.keyframe_chunks_counts_offset , self.KEYFRAME_CHUNKS_COUNTS_OFFSET_OFFSET)
        self.static_rotations_offset        = rw.rw_offset_uint32(self.static_rotations_offset       , self.STATIC_ROTATIONS_OFFSET_OFFSET)
        self.static_locations_offset        = rw.rw_offset_uint32(self.static_locations_offset       , self.STATIC_LOCATIONS_OFFSET_OFFSET)
        self.static_scales_offset           = rw.rw_offset_uint32(self.static_scales_offset          , self.STATIC_SCALES_OFFSET_OFFSET)
        self.static_float_channels_offset   = rw.rw_offset_uint32(self.static_float_channels_offset  , self.STATIC_FLOAT_CHANNELS_OFFSET_OFFSET)

        rw.align(0x48, 0x60)

    def rw_bone_idx_lists(self, rw):
        self.static_rotation_idxs      = rw.rw_uint16s(self.static_rotation_idxs, self.static_rotations_count)
        rw.align_with(rw.local_tell(), 0x10, 'H', self.bone_count)
        self.static_location_idxs      = rw.rw_uint16s(self.static_location_idxs, self.static_locations_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.bone_count)
        self.static_scale_idxs         = rw.rw_uint16s(self.static_scale_idxs, self.static_scales_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.bone_count)
        self.static_float_channel_idxs = rw.rw_uint16s(self.static_float_channel_idxs, self.static_float_channel_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.skel_binary_ref.float_channel_count)

        self.animated_rotation_idxs = rw.rw_uint16s(self.animated_rotation_idxs, self.animated_rotations_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.bone_count)
        self.animated_location_idxs = rw.rw_uint16s(self.animated_location_idxs, self.animated_locations_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.bone_count)
        self.animated_scale_idxs    = rw.rw_uint16s(self.animated_scale_idxs,    self.animated_scales_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.bone_count)
        self.animated_float_channel_idxs = rw.rw_uint16s(self.animated_float_channel_idxs, self.animated_float_channel_count)
        rw.align_with(rw.local_tell(), 0x08, 'H', self.skel_binary_ref.float_channel_count)

        rw.align(rw.local_tell(), 0x10)

    def rw_static_rotations(self, rw):
        if self.static_rotations_offset:
            rw.assert_local_file_pointer_now_at("Static Rotations", self.static_rotations_offset)
            self.static_rotations = rw.rw_s3Quats(self.static_rotations, self.static_rotations_count)
            rw.align(rw.local_tell(), 0x10)

    def rw_static_locations(self, rw):
        if self.static_locations_offset:
            rw.assert_local_file_pointer_now_at("Static Locations", self.static_locations_offset)
            self.static_locations = rw.rw_float32s(self.static_locations, (self.static_locations_count, 3))
            rw.align(rw.local_tell(), 0x10)

    def rw_static_scales(self, rw):
        if self.static_scales_offset:
            rw.assert_local_file_pointer_now_at("Static Scales", self.static_scales_offset)
            self.static_scales = rw.rw_float32s(self.static_scales, (self.static_scales_count, 3))

    def rw_static_float_channels(self, rw):
        if self.static_float_channels_offset:
            rw.assert_local_file_pointer_now_at("Static Float Channels", self.static_float_channels_offset)
            self.static_float_channels = rw.rw_float32s(self.static_float_channels, self.static_float_channel_count)
            rw.align(rw.local_tell(), 0x10)

    def rw_keyframe_chunk_offsets(self, rw):
        if rw.mode() == "read":
            self.keyframe_chunks = [KeyframeChunk() for _ in range(self.keyframe_chunk_count)]

        if self.keyframe_chunks_offsets_offset:
            rw.assert_local_file_pointer_now_at("Keyframe Chunk Offsets", self.keyframe_chunks_offsets_offset)
            for kf in self.keyframe_chunks:
                rw.rw_obj_method(kf, kf.rw_block_info)

    def rw_keyframe_chunk_counts(self, rw):
        if self.keyframe_chunks_counts_offset:
            rw.assert_local_file_pointer_now_at("Keyframe Chunk Counts", self.keyframe_chunks_counts_offset)
            for kf in self.keyframe_chunks:
                rw.rw_obj_method(kf, kf.rw_count_info)
            rw.align(rw.local_tell(), 0x10)

    def rw_animation_masks(self, rw):
        rw.assert_local_file_pointer_now_at("Animation Masks", self.animation_masks_offset)
        if self.bone_mask_offset:
            self.bone_masks = rw.rw_uint8s(self.bone_masks, self.bone_count)
            rw.align(rw.local_tell(), 4)
            self.float_channel_masks = rw.rw_uint8s(self.float_channel_masks, self.skel_binary_ref.float_channel_count)
            rw.align(rw.local_tell(), 0x10)
        rw.assert_local_file_pointer_now_at("End of Animation Masks", self.animation_masks_offset + self.animation_masks_size)

    def rw_keyframe_chunk_data(self, rw):
        keyframes_size = (self.animated_rotations_count + self.animated_locations_count + self.animated_scales_count + self.animated_float_channel_count) / 8
        for kf in self.keyframe_chunks:
            kf.rw_data(rw, keyframes_size)


class KeyframeChunk(Serializable):
    def __init__(self):
        super().__init__()

        self.padding_0x00 = 0
        self.size = None
        self.offset = None

        self.keyframe_start = None
        self.keyframe_count = None

        self.frame_0_rotations_bytecount        = None
        self.frame_0_locations_bytecount        = None
        self.frame_0_scales_bytecount           = None
        self.frame_0_float_channels_bytecount   = None
        self.keyframed_rotations_bytecount      = None
        self.keyframed_locations_bytecount      = None
        self.keyframed_scales_bytecount         = None
        self.keyframed_float_channels_bytecount = None

        self.frame_0_rotations        = None
        self.frame_0_locations        = None
        self.frame_0_scales           = None
        self.frame_0_float_channels   = None
        self.keyframes_in_use         = None
        self.keyframed_rotations      = None
        self.keyframed_locations      = None
        self.keyframed_scales         = None
        self.keyframed_float_channels = None

    def rw_block_info(self, rw):
        self.padding_0x00 = rw.rw_uint16(self.padding_0x00)
        self.size         = rw.rw_uint16(self.size)
        self.offset       = rw.rw_uint32(self.offset)

    def rw_count_info(self, rw):
        self.keyframe_start = rw.rw_uint16(self.keyframe_start)
        self.keyframe_count = rw.rw_uint16(self.keyframe_count)

    def rw_data(self, rw, keyframes_size):
        rw.assert_local_file_pointer_now_at("Keyframe Chunk Data", self.offset)
        self.frame_0_rotations_bytecount        = rw.rw_uint16(self.frame_0_rotations_bytecount)
        self.frame_0_locations_bytecount        = rw.rw_uint16(self.frame_0_locations_bytecount)
        self.frame_0_scales_bytecount           = rw.rw_uint16(self.frame_0_scales_bytecount)
        self.frame_0_float_channels_bytecount   = rw.rw_uint16(self.frame_0_float_channels_bytecount)
        self.keyframed_rotations_bytecount      = rw.rw_uint16(self.keyframed_rotations_bytecount)
        self.keyframed_locations_bytecount      = rw.rw_uint16(self.keyframed_locations_bytecount)
        self.keyframed_scales_bytecount         = rw.rw_uint16(self.keyframed_scales_bytecount)
        self.keyframed_float_channels_bytecount = rw.rw_uint16(self.keyframed_float_channels_bytecount)

        self.frame_0_rotations        = rw.rw_s3Quats(self.frame_0_rotations, self.frame_0_rotations_bytecount // 6)
        self.frame_0_locations        = rw.rw_float32s(self.frame_0_locations, (self.frame_0_locations_bytecount // 12, 3))
        self.frame_0_scales           = rw.rw_float32s(self.frame_0_scales, (self.frame_0_scales_bytecount // 12, 3))
        rw.align(rw.local_tell(), 0x04)
        self.frame_0_float_channels   = rw.rw_float32s(self.frame_0_float_channels, self.frame_0_float_channels_bytecount // 4)
        self.keyframes_in_use         = rw.rw_bytestring(self.keyframes_in_use, int(math.ceil(keyframes_size * self.keyframe_count)))
        self.keyframed_rotations      = rw.rw_s3Quats (self.keyframed_rotations, self.keyframed_rotations_bytecount // 6)
        self.keyframed_locations      = rw.rw_float32s(self.keyframed_locations, (self.keyframed_locations_bytecount // 12, 3))
        self.keyframed_scales         = rw.rw_float32s(self.keyframed_scales, (self.keyframed_scales_bytecount // 12, 3))
        rw.align(rw.local_tell(), 0x04)
        self.keyframed_float_channels = rw.rw_float32s(self.keyframed_float_channels, self.keyframed_float_channels_bytecount // 4)
        rw.align(rw.local_tell(), 0x10)
