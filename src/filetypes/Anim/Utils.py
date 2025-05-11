from .Binary import roundup
import math
import numpy as np


def interpolate_keyframe(interp_frame_time, frames, values, interpolator):
    next_frame_pos  = -1
    next_frame_time = max(frames)
    for i, k in enumerate(frames):
        if k > interp_frame_time:
            next_frame_pos  = i
            next_frame_time = k
            break

    if next_frame_pos == -1:
        return values[-1]
    elif next_frame_pos == 0:
        return values[0]
    elif next_frame_time == interp_frame_time:
        return values[next_frame_pos]
    
    prev_frame_time  = frames[next_frame_pos-1]
    prev_frame_value = values[next_frame_pos-1]
    next_frame_value = values[next_frame_pos]
    t = (interp_frame_time - prev_frame_time) / (next_frame_time - prev_frame_time)

    return interpolator(prev_frame_value, next_frame_value, t)

def interpolate_anim_tracks(interp_frame_time, anim_list, interpolator):
    out = [None for _ in range(len(anim_list))]
    for idx, (frames, values) in enumerate(anim_list):
        out[idx] = interpolate_keyframe(interp_frame_time, frames, values, interpolator)
    return out


def lerp(x, y, t):
    return x + t*(y-x)


def slerp(x, y, t):
    omega = math.acos(min(1, max(-1, np.dot(x, y))))
    if omega == 0 or np.isnan(omega):
        return x
    
    term_1 = x * math.sin((1-t)*omega)
    term_2 = y * math.sin(t*omega)
    return (term_1 + term_2) / math.sin(omega)


def categorise_channels(channel_dict):
    # unused = []
    static = []
    animated = []
    
    for idx, vals in channel_dict.items():
        if len(vals) == 0:
            pass
        elif len(vals) == 1:
            static.append(idx)
        else:
            animated.append(idx)
    
    return static, animated



def create_keyframe_chunks(KeyframeChunk, binary, interface, animated_positions, animated_rotations, animated_scales, animated_fcs, max_kf, max_chunk_size):
    # Now break the animation up into keyframe chunks.
    animated_position_kfs = [(list(interface.positions     [id_].keys()), [np.array(p) for p in interface.positions[id_].values()]) for id_ in animated_positions]
    animated_rotation_kfs = [(list(interface.rotations     [id_].keys()), [np.array(p) for p in interface.rotations[id_].values()]) for id_ in animated_rotations]
    animated_scales_kfs   = [(list(interface.scales        [id_].keys()), [np.array(p) for p in interface.scales   [id_].values()]) for id_ in animated_scales]
    animated_fcs_kfs      = [(list(interface.float_channels[id_].keys()), list(interface.float_channels[id_].values())) for id_ in animated_fcs]
    
    frame_idx = 0
    max_intermediate_kf_chunk_size = max_chunk_size - binary.keyframe_chunks_offsets_offset - 0x7F
    
    final_chunk = ChunkBuilder(KeyframeChunk, max_intermediate_kf_chunk_size, max_kf,
                         interpolate_anim_tracks(max_kf, animated_position_kfs, lerp),
                         interpolate_anim_tracks(max_kf, animated_rotation_kfs, slerp),
                         interpolate_anim_tracks(max_kf, animated_scales_kfs,   lerp),
                         interpolate_anim_tracks(max_kf, animated_fcs_kfs,      lerp))
    final_chunk.concretize()
    
    final_chunk_size                    = final_chunk.kf_chunk.calc_size()
    final_chunk.kf_chunk.size           = 0
    final_chunk.kf_chunk.keyframe_count = 0
    
    max_intermediate_kf_chunk_size -= final_chunk_size
    
    chunk_idx = 0
    while frame_idx < max_kf:
        # Init the chunk with the interpolated frame 0 data.
        chunk = ChunkBuilder(KeyframeChunk, max_intermediate_kf_chunk_size, frame_idx,
                             interpolate_anim_tracks(frame_idx, animated_position_kfs, lerp),
                             interpolate_anim_tracks(frame_idx, animated_rotation_kfs, slerp),
                             interpolate_anim_tracks(frame_idx, animated_scales_kfs,   lerp),
                             interpolate_anim_tracks(frame_idx, animated_fcs_kfs,      lerp))
        
        frame_idx += 1
        local_max = min(max_kf, frame_idx+128)
        while frame_idx < local_max:
            # This can definitely be optimised if it's a problem.
            if not chunk.try_expand_by_frame({cidx: interface.positions[bidx][frame_idx]      for cidx, bidx in enumerate(animated_positions) if frame_idx in interface.positions[bidx]}, 
                                             {cidx: interface.rotations[bidx][frame_idx]      for cidx, bidx in enumerate(animated_rotations) if frame_idx in interface.rotations[bidx]}, 
                                             {cidx: interface.scales[bidx][frame_idx]         for cidx, bidx in enumerate(animated_scales   ) if frame_idx in interface.scales[bidx]},
                                             {cidx: interface.float_channels[bidx][frame_idx] for cidx, bidx in enumerate(animated_fcs      ) if frame_idx in interface.float_channels[bidx]}):

                break
            frame_idx += 1
    
        chunk.concretize()
        chunk.kf_chunk.size = chunk.kf_chunk.calc_size() + final_chunk_size
        binary.keyframe_chunks.append(chunk.kf_chunk)
        chunk_idx += 1
    
    binary.keyframe_chunks.append(final_chunk.kf_chunk)
    binary.keyframe_chunk_count = len(binary.keyframe_chunks)
    

class ChunkBuilder:
    def __init__(self, KeyframeChunk, maximum_size, start_idx, frame_0_positions, frame_0_rotations, frame_0_scales, frame_0_float_channels):
        self.maximum_size = maximum_size
        self.rejected_size = 0
        self.kf_chunk = KeyframeChunk()
        self.kf_chunk.keyframe_start = start_idx
        
        rotation_count      = len(frame_0_rotations)
        position_count      = len(frame_0_positions)
        scale_count         = len(frame_0_scales)
        float_channel_count = len(frame_0_float_channels)
        
        self.kf_chunk.frame_0_rotations      = frame_0_rotations
        self.kf_chunk.frame_0_locations      = frame_0_positions
        self.kf_chunk.frame_0_scales         = frame_0_scales
        self.kf_chunk.frame_0_float_channels = frame_0_float_channels
        
        # Need to instead init using the frame 0 variables and store them
        # on the kf_chunk.
        self.kf_chunk.frame_0_rotations_bytecount      = 6 * rotation_count
        self.kf_chunk.frame_0_locations_bytecount      = 12 * position_count
        self.kf_chunk.frame_0_scales_bytecount         = 12 * scale_count
        self.kf_chunk.frame_0_float_channels_bytecount = 4 * float_channel_count
        
        # Would be nicer to replace with an array since we know how many
        # animated bones and float channels exist.
        self.rotations            = [[] for k in range(rotation_count)]
        self.rotation_frames      = [[] for k in range(rotation_count)]
        self.positions            = [[] for k in range(position_count)]
        self.position_frames      = [[] for k in range(position_count)]
        self.scales               = [[] for k in range(scale_count)]
        self.scale_frames         = [[] for k in range(scale_count)]
        self.float_channels       = [[] for k in range(float_channel_count)]
        self.float_channel_frames = [[] for k in range(float_channel_count)]
    
    def try_expand_by_frame(self, positions, rotations, scales, fcs):
        n_rotations = len(rotations)
        n_positions = len(positions)
        n_scales    = len(scales)
        n_fcs       = len(fcs)
        cur_frame   = self.kf_chunk.keyframe_count
        
        # Increment keyframe size to see if it exceeds the maximum.
        # We'll revert this change in the if-statement if the resize cannot be 
        # accomodated.
        rdelta = n_rotations * 6
        pdelta = n_positions * 12
        sdelta = n_scales    * 12
        fdelta = n_fcs       * 4
        
        self.kf_chunk.keyframed_rotations_bytecount      += rdelta
        self.kf_chunk.keyframed_locations_bytecount      += pdelta
        self.kf_chunk.keyframed_scales_bytecount         += sdelta
        self.kf_chunk.keyframed_float_channels_bytecount += fdelta
        self.kf_chunk.keyframe_count += 1
        
        if self.kf_chunk.calc_size() < self.maximum_size:
            for cidx, data in (rotations.items()):
                self.rotations[cidx].append(data)
                self.rotation_frames[cidx].append(cur_frame)
            for cidx, data in (positions.items()):
                self.positions[cidx].append(data)
                self.position_frames[cidx].append(cur_frame)
            for cidx, data in (scales.items()):
                self.scales[cidx].append(data)
                self.scale_frames[cidx].append(cur_frame)
            for cidx, data in (fcs.items()):
                self.float_channels[cidx].append(data)
                self.float_channel_frames[cidx].append(cur_frame)
            
            return True
        else:
            self.rejected_size = self.kf_chunk.calc_size()
            self.kf_chunk.keyframed_rotations_bytecount      -= rdelta
            self.kf_chunk.keyframed_locations_bytecount      -= pdelta
            self.kf_chunk.keyframed_scales_bytecount         -= sdelta
            self.kf_chunk.keyframed_float_channels_bytecount -= fdelta
            
            self.kf_chunk.keyframe_count -= 1
            return False
        
    def concretize(self):
        # Sort out the quirks of the bytesizes:
        # The scale and float channel sizes are 'incorrect' in that they
        # actually contain padding bytes in their size counts.
        sz = self.kf_chunk.frame_0_locations_bytecount + self.kf_chunk.frame_0_rotations_bytecount + self.kf_chunk.frame_0_scales_bytecount
        tmp_sz = roundup(sz, 4)
        self.kf_chunk.frame_0_scales_bytecount += tmp_sz - sz
        sz = tmp_sz
        
        sz += self.kf_chunk.frame_0_float_channels_bytecount
        sz += self.kf_chunk.calc_framevector_size()
        sz += self.kf_chunk.keyframed_rotations_bytecount
        sz += self.kf_chunk.keyframed_locations_bytecount
        sz += self.kf_chunk.keyframed_scales_bytecount
        
        tmp_sz = roundup(sz, 0x04)
        self.kf_chunk.keyframed_scales_bytecount += tmp_sz - sz
        sz = tmp_sz
        
        sz += self.kf_chunk.keyframed_float_channels_bytecount
        
        tmp_sz = roundup(sz, 0x10)
        self.kf_chunk.keyframed_float_channels_bytecount += tmp_sz - sz
        sz = tmp_sz
        
        # Construct the animation data.
        self.kf_chunk.keyframed_rotations = []
        for r in self.rotations:
            self.kf_chunk.keyframed_rotations.extend(r)
        self.kf_chunk.keyframed_locations = []
        for p in self.positions:
            self.kf_chunk.keyframed_locations.extend(p)
        self.kf_chunk.keyframed_scales = []
        for s in self.scales:
            self.kf_chunk.keyframed_scales.extend(s)
        self.kf_chunk.keyframed_float_channels = []
        for f in self.float_channels:
            self.kf_chunk.keyframed_float_channels.extend(f)
        
        # Construct the keyframe vector.
        buffer = bytearray(self.kf_chunk.calc_framevector_size())
        buffer_idx = 0
        buffer_subidx = -1
        frame_total = self.kf_chunk.keyframe_count - 1
        
        for framebufs in [self.rotation_frames, self.position_frames, self.scale_frames, self.float_channel_frames]:
            for frames in framebufs:
                prev_frame = -1
                
                for f in frames:
                    buffer_subidx += f - prev_frame
                    shift = buffer_subidx // 8
                    buffer_subidx -= 8*shift
                    buffer_idx += shift
                    buffer[buffer_idx] |= 1 << (7-buffer_subidx)
                    
                    prev_frame = f
                
                buffer_subidx += frame_total - prev_frame
                
        self.kf_chunk.keyframes_in_use = bytes(buffer)
        self.kf_chunk.keyframe_start &= 0xFFFF        
