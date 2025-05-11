class StreamMarkerDescriptor:
    FUNCTION_NAME = "dispatch_marker"
    
    def deserialize(binary_target, marker):
        pass
    
    def serialize(binary_target, marker):
        pass
    
    def count(binary_target, marker):
        pass
    
    def calculate_offsets(binary_target, marker):
        marker.notify(binary_target)
