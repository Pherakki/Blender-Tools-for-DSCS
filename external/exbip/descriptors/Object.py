class ObjectDescriptor:
    FUNCTION_NAME = "rw_obj"

    def deserialize(binary_parser, obj, *args, **kwargs):
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj

    def serialize(binary_parser, obj, *args, **kwargs):
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj
    
    def count(binary_parser, obj, *args, **kwargs):
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj

class DynamicObjectDescriptor:
    FUNCTION_NAME = "rw_dynamic_obj"

    def deserialize(binary_parser, obj, constructor, *args, **kwargs):
        obj = constructor()
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj

    def serialize(binary_parser, obj, constructor, *args, **kwargs):
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj
    
    def count(binary_parser, obj, constructor, *args, **kwargs):
        obj.exbip_rw(binary_parser, *args, **kwargs)
        return obj
    
class DynamicObjectsDescriptor:
    FUNCTION_NAME = "rw_dynamic_objs"

    def deserialize(binary_parser, objs, constructor, count, *args, **kwargs):
        res = []
        for i in range(count):
            obj = constructor()
            res.append(obj)
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return res

    def serialize(binary_parser, objs, constructor, count, *args, **kwargs):
        for obj in objs:
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return objs
    
    def count(binary_parser, objs, constructor, count, *args, **kwargs):
        for obj in objs:
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return objs
    
class DynamicObjectsWhileDescriptor:
    FUNCTION_NAME = "rw_dynamic_objs_while"

    def deserialize(binary_parser, objs, constructor, condition, *args, **kwargs):
        res = []
        while condition(binary_parser):
            obj = constructor()
            res.append(obj)
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return res

    def serialize(binary_parser, objs, constructor, condition, *args, **kwargs):
        for obj in objs:
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return objs
    
    def count(binary_parser, objs, constructor, condition, *args, **kwargs):
        for obj in objs:
            obj.exbip_rw(binary_parser, *args, **kwargs)
        return objs
