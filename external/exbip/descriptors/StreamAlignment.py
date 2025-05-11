class AlignmentDescriptor:
    FUNCTION_NAME = "align"

    class UnexpectedPaddingError(Exception):
        def __init__(self, expected, received):
            super().__init__(f"Expected padding with a value of '{expected}', received '{received}'")

    def deserialize(binary_parser, position, alignment, pad_value=b'\x00'):
        size = binary_parser.bytes_to_alignment(position, alignment)
        align_data = binary_parser._bytestream.read(size)
        expected_pad = pad_value*(size//len(pad_value))
        if align_data != expected_pad:
            raise AlignmentDescriptor.UnexpectedPaddingError(expected_pad, align_data)

    def serialize(binary_parser, position, alignment, pad_value=b'\x00'):
        size = binary_parser.bytes_to_alignment(position, alignment)
        if not (size/len(pad_value)).is_integer():
            raise ValueError(f"Alignment requires an offset increment of {size} bytes, "
                             f"but the padding value '{pad_value}' is {len(pad_value)} bytes in size, "
                             f"which would require a non-integer number of pad values")
        binary_parser._bytestream.write(pad_value * (size // len(pad_value)))

    def count(binary_parser, position, alignment, pad_value=b'\x00'):
        size = binary_parser.bytes_to_alignment(position, alignment)
        if not (size/len(pad_value)).is_integer():
            raise ValueError(f"Alignment requires an offset increment of {size} bytes, "
                             f"but the padding value '{pad_value}' is {len(pad_value)} bytes in size, "
                             f"which would require a non-integer number of pad values")
        binary_parser.advance_offset(size)

class FillDescriptor:
    FUNCTION_NAME = "fill"
    
    def deserialize(binary_parser, position, alignment, fill_value=b'\x00'):
        size = binary_parser.bytes_to_alignment(position, alignment)
        binary_parser._bytestream.read(size)
        
    def serialize(binary_parser, position, alignment, fill_value=b'\x00'):
        fv_size = len(fill_value)
        size = binary_parser.bytes_to_alignment(position, alignment)
        fv_count = (size//fv_size)
        if not fv_count*fv_size == size:
            raise ValueError(f"Alignment requires an offset increment of {size} bytes, "
                             f"but the fill value '{fill_value}' is {fv_size} bytes in size, "
                             f"which would require a non-integer number of fill values")
        binary_parser._bytestream.write(fill_value * fv_count)

    def count(binary_parser, position, alignment, fill_value=b'\x00'):
        fv_size = len(fill_value)
        size = binary_parser.bytes_to_alignment(position, alignment)
        fv_count = (size//fv_size)
        if not fv_count*fv_size == size:
            raise ValueError(f"Alignment requires an offset increment of {size} bytes, "
                             f"but the fill value '{fill_value}' is {fv_size} bytes in size, "
                             f"which would require a non-integer number of fill values")
        binary_parser.advance_offset(size)
