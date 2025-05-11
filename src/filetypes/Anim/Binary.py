import math
import struct

from ...serialization.DSCSStructs import DSCSSerializable
from ...serialization.DSCSFormatters import HEX32_formatter
from ...serialization import OffsetMarker

def alignment_bytes(pos, width):
    return (width - (pos % width)) % width

def roundup(pos, width):
    return pos + alignment_bytes(pos, width)


class TryGetFloatChannelsFromIndices:
    def deserialize(rw, binary):
        if alignment_bytes(rw.tell(), 0x08) != 0 and binary.float_channel_count == 0:
                binary.float_channel_count = rw.rw_uint16(binary.float_channel_count)
    def serialize(rw, binary):
        pass
    def count(rw, binary):
        pass


class AnimFileBinary(DSCSSerializable):
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

    def __init__(self, float_channel_count=0):
        super().__init__()

        # Util variables that *could* be obtained from a skel file...
        self.float_channel_count = float_channel_count

        # Header variables
        self.filetype = b'40AE'
        self.animation_duration = 0  # Seconds
        self.playback_rate      = 0  # Keyframes per second

        self.animation_masks_offset  = 0
        self.bone_count              = 0
        self.frame_count             = 0
        self.keyframe_chunk_count    = 0
        self.max_keyframe_chunk_size = 0x4000

        self.static_rotations_count        = 0
        self.static_locations_count        = 0
        self.static_scales_count           = 0
        self.static_float_channel_count    = 0
        self.animated_rotations_count      = 0
        self.animated_locations_count      = 0
        self.animated_scales_count         = 0
        self.animated_float_channel_count  = 0
        self.padding_0x26                  = 0  # Always 0
        self.animation_masks_size          = 0  # Specifies size of the bone mask
        self.bone_mask_offset              = 0

        self.keyframe_chunks_offsets_offset = 0
        self.keyframe_chunks_counts_offset  = 0
        self.static_rotations_offset        = 0
        self.static_locations_offset        = 0
        self.static_scales_offset           = 0
        self.static_float_channels_offset   = 0

        # Data holders
        self.static_rotation_idxs        = None
        self.static_location_idxs        = None
        self.static_scale_idxs           = None
        self.static_float_channel_idxs   = None
        self.animated_rotation_idxs      = None
        self.animated_location_idxs      = None
        self.animated_scale_idxs         = None
        self.animated_float_channel_idxs = None

        self.static_rotations        = []
        self.static_locations        = []
        self.static_scales           = []
        self.static_float_channels   = []
        self.bone_masks              = []
        self.float_channel_masks     = []
        self.keyframe_chunks         = []
        
        self.keyframe_chunks_offsets_marker = OffsetMarker().subscribe(self, "keyframe_chunks_offsets_offset")
        self.keyframe_chunks_counts_marker  = OffsetMarker().subscribe(self, "keyframe_chunks_counts_offset")
        self.static_rotations_marker        = OffsetMarker().subscribe(self, "static_rotations_offset")
        self.static_locations_marker        = OffsetMarker().subscribe(self, "static_locations_offset")
        self.static_scales_marker           = OffsetMarker().subscribe(self, "static_scales_offset")
        self.static_float_channels_marker   = OffsetMarker().subscribe(self, "static_float_channels_offset")
        self.animation_masks_marker         = OffsetMarker().subscribe(self, "animation_masks_offset")
        self.bone_mask_marker               = OffsetMarker().subscribe(self, "bone_mask_offset")
        self.animation_masks_size_marker    = OffsetMarker().subscribe_callback(lambda rw: setattr(self, "animation_masks_size", rw.tell() - self.animation_masks_offset))

    def exbip_rw(self, rw):
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
        rw.assert_eof()

    def rw_header(self, rw):
        self.filetype = rw.rw_bytestring(self.filetype, 4)
        rw.assert_equal(self.filetype, b"40AE")

        self.animation_duration      = rw.rw_float32(self.animation_duration)
        self.playback_rate           = rw.rw_float32(self.playback_rate)
        self.animation_masks_offset  = rw.rw_uint16(self.animation_masks_offset)
        self.bone_count              = rw.rw_uint16(self.bone_count)
        self.frame_count             = rw.rw_uint16(self.frame_count)
        self.keyframe_chunk_count    = rw.rw_uint16(self.keyframe_chunk_count)
        self.max_keyframe_chunk_size = rw.rw_uint16(self.max_keyframe_chunk_size)

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

        self.keyframe_chunks_offsets_offset = rw.rw_shifted_uint32(self.keyframe_chunks_offsets_offset, self.KEYFRAME_CHUNKS_OFFSETS_OFFSET_OFFSET)
        self.keyframe_chunks_counts_offset  = rw.rw_shifted_uint32(self.keyframe_chunks_counts_offset , self.KEYFRAME_CHUNKS_COUNTS_OFFSET_OFFSET)
        self.static_rotations_offset        = rw.rw_shifted_uint32(self.static_rotations_offset       , self.STATIC_ROTATIONS_OFFSET_OFFSET)
        self.static_locations_offset        = rw.rw_shifted_uint32(self.static_locations_offset       , self.STATIC_LOCATIONS_OFFSET_OFFSET)
        self.static_scales_offset           = rw.rw_shifted_uint32(self.static_scales_offset          , self.STATIC_SCALES_OFFSET_OFFSET)
        self.static_float_channels_offset   = rw.rw_shifted_uint32(self.static_float_channels_offset  , self.STATIC_FLOAT_CHANNELS_OFFSET_OFFSET)

        rw.align(0x48, 0x60)

    def rw_bone_idx_lists(self, rw):
        bone_count_bytes  = struct.pack('H', self.bone_count)
        float_count_bytes = struct.pack('H', self.float_channel_count)
        
        self.static_rotation_idxs      = rw.rw_uint16s(self.static_rotation_idxs, self.static_rotations_count)
        rw.fill(rw.tell(), 0x10, bone_count_bytes)
        self.static_location_idxs      = rw.rw_uint16s(self.static_location_idxs, self.static_locations_count)
        rw.fill(rw.tell(), 0x08, bone_count_bytes)
        self.static_scale_idxs         = rw.rw_uint16s(self.static_scale_idxs, self.static_scales_count)
        rw.fill(rw.tell(), 0x08, bone_count_bytes)
        self.static_float_channel_idxs = rw.rw_uint16s(self.static_float_channel_idxs, self.static_float_channel_count)
        rw.rw_descriptor(TryGetFloatChannelsFromIndices, self)
        rw.fill(rw.tell(), 0x08, float_count_bytes)
        
        self.animated_rotation_idxs      = rw.rw_uint16s(self.animated_rotation_idxs, self.animated_rotations_count)
        rw.fill(rw.tell(), 0x08, bone_count_bytes)
        self.animated_location_idxs      = rw.rw_uint16s(self.animated_location_idxs, self.animated_locations_count)
        rw.fill(rw.tell(), 0x08, bone_count_bytes)
        self.animated_scale_idxs         = rw.rw_uint16s(self.animated_scale_idxs,    self.animated_scales_count)
        rw.fill(rw.tell(), 0x08, bone_count_bytes)
        self.animated_float_channel_idxs = rw.rw_uint16s(self.animated_float_channel_idxs, self.animated_float_channel_count)
        rw.rw_descriptor(TryGetFloatChannelsFromIndices, self)
        rw.fill(rw.tell(), 0x08, float_count_bytes)
        
        rw.align(rw.tell(), 0x10)

    def rw_static_rotations(self, rw):
        #if rw.section_exists(self.static_rotations_offset, self.static_rotations_count):
        rw.verify_stream_offset(self.static_rotations_offset, "Static Rotations", HEX32_formatter, self.static_rotations_marker)
        self.static_rotations = rw.rw_smallest3quats(self.static_rotations, self.static_rotations_count)
        rw.align(rw.tell(), 0x10)

    def rw_static_locations(self, rw):
        #if rw.section_exists(self.static_locations_offset, self.static_locations_count):
        rw.verify_stream_offset(self.static_locations_offset, "Static Locations", HEX32_formatter, self.static_locations_marker)
        self.static_locations = rw.rw_float32s(self.static_locations, (self.static_locations_count, 3))
        rw.align(rw.tell(), 0x10)

    def rw_static_scales(self, rw):
        #if rw.section_exists(self.static_scales_offset, self.static_scales_count):
        rw.verify_stream_offset(self.static_scales_offset, "Static Scales", HEX32_formatter, self.static_scales_marker)
        self.static_scales = rw.rw_float32s(self.static_scales, (self.static_scales_count, 3))

    def rw_static_float_channels(self, rw):
        #if rw.section_exists(self.static_float_channels_offset, self.static_float_channel_count):
        rw.verify_stream_offset(self.static_float_channels_offset, "Static Float Channels", HEX32_formatter, self.static_float_channels_marker)
        self.static_float_channels = rw.rw_float32s(self.static_float_channels, self.static_float_channel_count)
        rw.align(rw.tell(), 0x10)

    def rw_keyframe_chunk_offsets(self, rw):
        if rw.section_exists(self.keyframe_chunks_offsets_offset, self.keyframe_chunk_count):
            rw.verify_stream_offset(self.keyframe_chunks_offsets_offset, "Keyframe Chunk Offsets", HEX32_formatter, self.keyframe_chunks_offsets_marker)
            for kf in rw.array_iterator(self.keyframe_chunks, KeyframeChunk, self.keyframe_chunk_count):
                kf.rw_block_info(rw)

    def rw_keyframe_chunk_counts(self, rw):
        if rw.section_exists(self.keyframe_chunks_counts_offset, self.keyframe_chunk_count):
            rw.verify_stream_offset(self.keyframe_chunks_counts_offset, "Keyframe Chunk Counts", HEX32_formatter, self.keyframe_chunks_counts_marker)
            for kf in self.keyframe_chunks:
                kf.rw_count_info(rw)
        rw.align(rw.tell(), 0x10)

    def rw_animation_masks(self, rw):
        rw.verify_stream_offset(self.animation_masks_offset, "Animation Blend Factors", HEX32_formatter, self.animation_masks_marker)
        if rw.section_exists(self.bone_mask_offset, len(self.bone_masks) + len(self.float_channel_masks)):
            rw.verify_stream_offset(self.bone_mask_offset, "Animation Bone Masks", HEX32_formatter, self.bone_mask_marker)
            self.bone_masks = rw.rw_uint8s(self.bone_masks, self.bone_count)
            rw.align(rw.tell(), 4)
            
            # This might contain some extra padding at the end - can be stripped
            # off with reference to a skeleton binary.
            if self.float_channel_count == 0:
                self.float_channel_count = max(self.animation_masks_size - (rw.tell() - self.animation_masks_offset), 0)
            
            self.float_channel_masks = rw.rw_uint8s(self.float_channel_masks, self.float_channel_count)
            rw.align(rw.tell(), 0x10)
        
        rw.verify_stream_offset(self.animation_masks_offset + self.animation_masks_size, "End of Animation Masks", HEX32_formatter, self.animation_masks_size_marker)

    def rw_keyframe_chunk_data(self, rw):
        for kf in self.keyframe_chunks:
            kf.rw_data(rw)


class KeyframeChunk:
    def __init__(self):
        self.padding_0x00 = 0
        self.size   = 0
        self.offset = 0

        self.keyframe_start = 0
        self.keyframe_count = 0

        self.frame_0_rotations_bytecount        = 0
        self.frame_0_locations_bytecount        = 0
        self.frame_0_scales_bytecount           = 0
        self.frame_0_float_channels_bytecount   = 0
        self.keyframed_rotations_bytecount      = 0
        self.keyframed_locations_bytecount      = 0
        self.keyframed_scales_bytecount         = 0
        self.keyframed_float_channels_bytecount = 0

        self.frame_0_rotations        = None
        self.frame_0_locations        = None
        self.frame_0_scales           = None
        self.frame_0_float_channels   = None
        self.keyframes_in_use         = None
        self.keyframed_rotations      = None
        self.keyframed_locations      = None
        self.keyframed_scales         = None
        self.keyframed_float_channels = None
        
        self.marker = OffsetMarker().subscribe(self, "offset")
        
    def rw_block_info(self, rw):
        self.padding_0x00 = rw.rw_uint16(self.padding_0x00)
        self.size         = rw.rw_uint16(self.size)
        self.offset       = rw.rw_uint32(self.offset)

    def rw_count_info(self, rw):
        self.keyframe_start = rw.rw_uint16(self.keyframe_start)
        self.keyframe_count = rw.rw_uint16(self.keyframe_count)

    def rw_data(self, rw):
        rw.verify_stream_offset(self.offset, "Keyframe Chunk Data", HEX32_formatter, self.marker)
        self.frame_0_rotations_bytecount        = rw.rw_uint16(self.frame_0_rotations_bytecount)
        self.frame_0_locations_bytecount        = rw.rw_uint16(self.frame_0_locations_bytecount)
        self.frame_0_scales_bytecount           = rw.rw_uint16(self.frame_0_scales_bytecount)
        self.frame_0_float_channels_bytecount   = rw.rw_uint16(self.frame_0_float_channels_bytecount)
        self.keyframed_rotations_bytecount      = rw.rw_uint16(self.keyframed_rotations_bytecount)
        self.keyframed_locations_bytecount      = rw.rw_uint16(self.keyframed_locations_bytecount)
        self.keyframed_scales_bytecount         = rw.rw_uint16(self.keyframed_scales_bytecount)
        self.keyframed_float_channels_bytecount = rw.rw_uint16(self.keyframed_float_channels_bytecount)


        num_rotations = self.frame_0_rotations_bytecount      // 6
        num_locations = self.frame_0_locations_bytecount      // 12
        num_scales    = self.frame_0_scales_bytecount         // 12
        num_fcs       = self.frame_0_float_channels_bytecount // 4
        frame_bytesize = self.calc_framevector_size()
        
        self.frame_0_rotations        = rw.rw_smallest3quats(self.frame_0_rotations, num_rotations)
        self.frame_0_locations        = rw.rw_float32s(self.frame_0_locations, (num_locations, 3))
        self.frame_0_scales           = rw.rw_float32s(self.frame_0_scales, (num_scales, 3))
        rw.align(rw.tell(), 0x04)
        self.frame_0_float_channels   = rw.rw_float32s(self.frame_0_float_channels, num_fcs)
        self.keyframes_in_use         = rw.rw_bytestring(self.keyframes_in_use, frame_bytesize)
        self.keyframed_rotations      = rw.rw_smallest3quats (self.keyframed_rotations, self.keyframed_rotations_bytecount // 6)
        self.keyframed_locations      = rw.rw_float32s(self.keyframed_locations, (self.keyframed_locations_bytecount // 12, 3))
        self.keyframed_scales         = rw.rw_float32s(self.keyframed_scales, (self.keyframed_scales_bytecount // 12, 3))
        rw.align(rw.tell(), 0x04)
        self.keyframed_float_channels = rw.rw_float32s(self.keyframed_float_channels, self.keyframed_float_channels_bytecount // 4)
        rw.align(rw.tell(), 0x10)
    
    def calc_framevector_size(self):
        num_rotations = self.frame_0_rotations_bytecount      // 6
        num_locations = self.frame_0_locations_bytecount      // 12
        num_scales    = self.frame_0_scales_bytecount         // 12
        num_fcs       = self.frame_0_float_channels_bytecount // 4
        frame_size = (num_rotations + num_locations + num_scales + num_fcs)
        return ((frame_size * self.keyframe_count) + 7) // 8  # Round up to next 8
    
    def calc_size(self):
        sz = 16 + self.frame_0_rotations_bytecount + self.frame_0_locations_bytecount + self.frame_0_scales_bytecount
        sz = roundup(sz, 0x04)
        sz += self.frame_0_float_channels_bytecount
        sz += self.calc_framevector_size()
        sz += self.keyframed_rotations_bytecount
        sz += self.keyframed_locations_bytecount
        sz += self.keyframed_scales_bytecount
        sz = roundup(sz, 0x04)
        sz += self.keyframed_float_channels_bytecount
        return roundup(sz, 0x10)

    def dump_debug(self):
        return (self.frame_0_rotations_bytecount, 
                self.frame_0_locations_bytecount, 
                self.frame_0_scales_bytecount,
                self.frame_0_float_channels_bytecount,
                self.calc_framevector_size(),
                self.keyframed_rotations_bytecount,
                self.keyframed_locations_bytecount,
                self.keyframed_scales_bytecount,
                self.keyframed_float_channels_bytecount,
                self.calc_size())
