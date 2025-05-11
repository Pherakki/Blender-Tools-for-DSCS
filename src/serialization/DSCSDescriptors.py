import struct
from ...external.exbip.framework.descriptors.EndianPair import EndianPairDescriptor

UINT32_LE_STRUCT = struct.Struct("<I")
UINT32_LE_UNPACK = UINT32_LE_STRUCT.unpack
UINT32_LE_PACK   = UINT32_LE_STRUCT.pack
UINT32_BE_STRUCT = struct.Struct(">I")
UINT32_BE_UNPACK = UINT32_BE_STRUCT.unpack
UINT32_BE_PACK   = UINT32_BE_STRUCT.pack


class Smallest3QuatDescriptor:
    FUNCTION_NAME = "rw_smallest3quat"
    
    def deserialize(binary_target, value):
        input_data = binary_target.rw_uint8s(None, 6)
        if (input_data[0] & 0x80) >> 7 == 1:
            print("WARNING: Quaternion with a leading bit of 1 found.")
        c1 = (input_data[0] & 0x7F) << 8 | input_data[1]
        c2 = (input_data[2] & 0xFF) << 7 | (input_data[3] & 0xFE) >> 1
        c3 = (input_data[3] & 0x01) << 14 | (input_data[4] & 0xFF) << 6 | (input_data[5] & 0xFC) >> 2
        largest_index = input_data[5] & 0x03

        components = [c1, c2, c3]
        components = [c - 16383 for c in components]
        components = [c / 16384 for c in components]
        components = [c / (2**.5) for c in components]

        square_vector_length = sum([c ** 2 for c in components])
        if square_vector_length <= 1: # Should be smaller than 0.5...
            largest_component = (1 - square_vector_length)**.5
        else:
            print("WARNING: Quaternion with an invalid largest component found.")
            largest_component = 0

        components.insert(largest_index, largest_component)

        return components
    
    def serialize(binary_target, value):
        components = [v for v in value]
        abs_components = [abs(c) for c in components]
        abs_largest_component = max(abs_components)
        largest_index = abs_components.index(abs_largest_component)
        largest_component = components[largest_index]
        largest_component_sign = largest_component // (abs(largest_component))
        # Get rid of the largest component
        # No need to store the sign of the largest component, because
        # (X, Y, Z, W) = (-X, -Y, -Z, -W)
        # So just multiply through by the sign of the removed component to create an equivalent quaternion
        # In this way, the largest component is always +ve
        del components[largest_index]
        components = [largest_component_sign * c for c in components]

        # No other component can be larger than 1/sqrt(2) due to normalisation
        # So map the remaining components from the interval [-1/sqrt(2), 1/sqrt(2)] to [0, 32767] to gain ~1.4x precision
        components = [int(round(c * (2**.5) * 16384)) + 16383 for c in components]

        for i, elem in enumerate(components):
            if elem < 0:
                components[i] = 0
            elif elem > 32767:
                components[i] = 32767

        # Now convert to big-endian uint15s
        packed_rep = [0, 0, 0, 0, 0, 0]
        packed_rep[0] = ((components[0] & 0x7F00) >> 8)
        packed_rep[1] = ((components[0] & 0x00FF) >> 0)
        packed_rep[2] = ((components[1] & 0x7F80) >> 7)
        packed_rep[3] = ((components[1] & 0x007F) << 1) | ((components[2] & 0xC000) >> 14)
        packed_rep[4] = ((components[2] & 0x3FC0) >> 6)
        packed_rep[5] = ((components[2] & 0x003F) << 2) | largest_index

        binary_target.rw_uint8s(packed_rep, 6)

        return value
    
    def count(binary_target, value):
        binary_target.advance_offset(6)
        return value


class Smallest3QuatsDescriptor:
    FUNCTION_NAME = "rw_smallest3quats"
    
    def deserialize(binary_target, value, length):
        return [binary_target.rw_smallest3quat(None) for _ in range(length)]
    
    def serialize(binary_target, value, length):
        for v in value:
            binary_target.rw_smallest3quat(v)
        return value
    
    def count(binary_target, value, length):
        binary_target.advance_offset(6*length)
        return value


class ShiftedUInt32DescriptorLE:
    FUNCTION_NAME = "rw_shifted_uint32_le"
    
    def deserialize(binary_parser, value, shift):
        return UINT32_LE_UNPACK(binary_parser._bytestream.read(4))[0] + shift
    
    def serialize(binary_parser, value, shift):
        binary_parser._bytestream.write(UINT32_LE_PACK(value - shift))
        return value
    
    def count(binary_parser, value, shift):
        binary_parser.advance_offset(4)
        return value

class ShiftedUInt32DescriptorBE:
    FUNCTION_NAME = "rw_shifted_uint32_be"
    
    def deserialize(binary_parser, value, shift):
        return UINT32_BE_UNPACK(binary_parser._bytestream.read(4))[0] - shift
    
    def serialize(binary_parser, value, shift):
        binary_parser._bytestream.write(UINT32_BE_PACK(value + shift))
        return value
    
    def count(binary_parser, value, shift):
        binary_parser.advance_offset(4)
        return value

DSCS_DESCRIPTORS        = [ShiftedUInt32DescriptorLE, ShiftedUInt32DescriptorBE, Smallest3QuatDescriptor, Smallest3QuatsDescriptor]
DSCS_ENDIAN_DESCRIPTORS = [EndianPairDescriptor("rw_shifted_uint32", "rw_shifted_uint32_le", "rw_shifted_uint32_be")]
