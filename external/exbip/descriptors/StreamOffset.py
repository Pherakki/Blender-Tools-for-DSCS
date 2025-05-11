class UnexpectedOffsetError(Exception):
    def __init__(self, prefix, expected, received, formatter):
        msg = f"{prefix}Expected stream to be at {formatter(expected)}, but it is at {formatter(received)}"
        super().__init__(msg)
            
class UnexpectedGlobalOffsetError(Exception):
    def __init__(self, prefix, expected, received, transformer, formatter):
        msg = f"{prefix}Expected stream to be at {formatter(expected)} [Global: {formatter(transformer(expected))}], but it is at {formatter(received)} [Global: {formatter(transformer(received))}]"
        super().__init__(msg)
            

class VerifyOffsetDescriptor:
    FUNCTION_NAME = "verify_stream_offset"
   
    def deserialize(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        if binary_parser.tell() != offset:
            prefix = message + ': ' if message is not None else ''
            if binary_parser.tell() != binary_parser.global_tell():
                raise UnexpectedGlobalOffsetError(prefix, offset, binary_parser.tell(), binary_parser.local_to_global_offset, formatter)
            else:
                raise UnexpectedOffsetError(prefix, offset, binary_parser.tell(), formatter)

    def serialize(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        if binary_parser.tell() != offset:
            prefix = message + ': ' if message is not None else ''
            if binary_parser.tell() != binary_parser.global_tell():
                raise UnexpectedGlobalOffsetError(prefix, offset, binary_parser.tell(), binary_parser.local_to_global_offset, formatter)
            else:
                raise UnexpectedOffsetError(prefix, offset, binary_parser.tell(), formatter)

    def count(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        pass

    def calculate_offsets(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        if notifier is not None:
            notifier.notify(binary_parser)


class EnforceOffsetDescriptor(VerifyOffsetDescriptor):
    FUNCTION_NAME = "enforce_stream_offset"

    def deserialize(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        binary_parser.seek(offset)
    

class NavigateOffsetDescriptor:
    FUNCTION_NAME = "navigate_stream_offset"

    def deserialize(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        binary_parser.seek(offset)

    def serialize(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        pass

    def count(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        pass

    def calculate_offsets(binary_parser, offset, message, formatter=lambda x: x, notifier=None):
        if notifier is not None:
            notifier.notify(binary_parser)


class CheckOffsetAsVerifyDescriptor(VerifyOffsetDescriptor):
    FUNCTION_NAME = "check_stream_offset"


class CheckOffsetAsEnforceDescriptor(EnforceOffsetDescriptor):
    FUNCTION_NAME = "check_stream_offset"
