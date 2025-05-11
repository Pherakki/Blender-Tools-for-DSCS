from .Interface import AnimFile
from .BinaryHundredLine import AnimFileBinary as AnimFileBinaryHundredLine, KeyframeChunk
from .Utils import categorise_channels
from .Utils import create_keyframe_chunks


class AnimFileHundredLine(AnimFile):
    def __init__(self):
        super().__init__()
        self.unknown_section = [0.,0.,0.,0.,1.,0.,0.,0.]
    
    @classmethod
    def from_binary(cls, binary):
        instance = super().from_binary(binary)
        instance.unknown_section = binary.unknown_section
        return instance
        
    def to_file(self, path):
        binary = self.to_binary()
        binary.write(path)

    def to_binary(self):
        max_chunk_size = 0xFFFFFFFF
        
        binary = AnimFileBinaryHundredLine()
        binary.unknown_section = self.unknown_section
        static_positions, animated_positions = categorise_channels(self.positions)
        static_rotations, animated_rotations = categorise_channels(self.rotations)
        static_scales,    animated_scales    = categorise_channels(self.scales)
        static_fcs,       animated_fcs       = categorise_channels(self.float_channels)
        
        unused_bones = set(range(self.bone_count))
        unused_bones -= set(static_positions)
        unused_bones -= set(static_rotations)
        unused_bones -= set(static_scales)
        unused_bones -= set(animated_positions)
        unused_bones -= set(animated_rotations)
        unused_bones -= set(animated_scales)
        unused_bones = sorted(unused_bones)
        
        unused_float_channels = set(range(self.float_channel_count))
        unused_float_channels -= set(static_fcs)
        unused_float_channels -= set(animated_fcs)
        unused_float_channels = sorted(unused_float_channels)   
        
  
        # Sort out header variables    
        binary.static_locations_count     = len(static_positions)
        binary.static_rotations_count     = len(static_rotations)
        binary.static_scales_count        = len(static_scales)
        binary.static_float_channel_count = len(static_fcs)
        binary.static_location_idxs       = static_positions
        binary.static_rotation_idxs       = static_rotations
        binary.static_scale_idxs          = static_scales
        binary.static_float_channel_idxs  = static_fcs
        
        binary.animated_locations_count      = len(animated_positions)
        binary.animated_rotations_count      = len(animated_rotations)
        binary.animated_scales_count         = len(animated_scales)
        binary.animated_float_channel_count  = len(animated_fcs)
        binary.animated_location_idxs        = animated_positions
        binary.animated_rotation_idxs        = animated_rotations
        binary.animated_scale_idxs           = animated_scales
        binary.animated_float_channel_idxs   = animated_fcs
                
        # Dump static animations
        binary.static_locations      = [list(self.positions[k].values())[0]      for k in static_positions]
        binary.static_rotations      = [list(self.rotations[k].values())[0]      for k in static_rotations]
        binary.static_scales         = [list(self.scales   [k].values())[0]      for k in static_scales]
        binary.static_float_channels = [list(self.float_channels[k].values())[0] for k in static_fcs]
        
        # Identify max keyframe
        max_pos_kf = max((max(self.positions     [idx]) for idx in animated_positions), default=0)
        max_rot_kf = max((max(self.rotations     [idx]) for idx in animated_rotations), default=0)
        max_scl_kf = max((max(self.scales        [idx]) for idx in animated_scales),    default=0)
        max_fcs_kf = max((max(self.float_channels[idx]) for idx in animated_fcs),       default=0)
        max_kf = max((max_pos_kf, max_rot_kf, max_scl_kf, max_fcs_kf))
        
        # Finish filling out the header
        binary.playback_rate           = self.playback_rate
        binary.animation_duration      = max_kf / binary.playback_rate
        binary.frame_count             = (max_kf + 1) & 0xFFFF
        binary.keyframe_chunk_count    = 1
        binary.max_keyframe_chunk_size = max_chunk_size
        binary.padding_0x26            = 0
        binary.bone_count              = self.bone_count
        binary.float_channel_count     = self.float_channel_count

        
        binary.bone_masks          = self.bone_blend_factors
        binary.float_channel_masks = self.float_channel_blend_factors
        
        # Calculate the offsets in order to figure out how much the max chunk
        # size gets reduced by the header.
        binary.calculate_offsets()
        
        # Now break the animation up into keyframe chunks.
        create_keyframe_chunks(KeyframeChunk, binary, self, animated_positions, animated_rotations, animated_scales, animated_fcs, max_kf, max_chunk_size)
        
        # Finally, calculate all remaining offsets.
        binary.calculate_offsets()
        
        return binary

