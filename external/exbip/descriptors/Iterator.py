class ForLoopIteratorConstruct:
    def __init__(self, binary_parser, array, constructor, count):
        self._binary_parser = binary_parser
        self._array         = array
        self._constructor   = constructor
        self._count         = count
        
        array.clear()
    
    def __iter__(self):
        for _ in range(self._count):
            obj = self._constructor()
            self._array.append(obj)
            yield obj


class ForLoopIteratorParse:
    def __init__(self, binary_parser, array, constructor, count):
        self._binary_parser = binary_parser
        self._array         = array
        self._constructor   = constructor
        self._count         = count
    
    def __iter__(self):
        for obj in self._array:
            yield obj


class WhileLoopIteratorConstruct:
    def __init__(self, binary_parser, array, constructor, stop_condition):
        self._binary_parser  = binary_parser
        self._array          = array
        self._constructor    = constructor
        self._stop_condition = stop_condition
        
        array.clear()
    
    def __iter__(self):
        while self._stop_condition():
            obj = self._constructor()
            self._array.append(obj)
            yield obj


class DoWhileLoopIteratorConstruct:
    def __init__(self, binary_parser, array, constructor, stop_condition):
        self._binary_parser  = binary_parser
        self._array          = array
        self._constructor    = constructor
        self._stop_condition = stop_condition
        
        array.clear()
    
    def __iter__(self):
        while True:
            obj = self._constructor()
            self._array.append(obj)
            yield obj
            if self._stop_condition(obj):
                break


class ForLoopIteratorDescriptor:
    FUNCTION_NAME = "array_iterator"
    
    def deserialize(binary_parser, array, constructor, count):
        return ForLoopIteratorConstruct(binary_parser, array, constructor, count)
    
    def serialize(binary_parser, array, constructor, count):
        return ForLoopIteratorParse(binary_parser, array, constructor, count)

    def count(binary_parser, array, constructor, count):
        return ForLoopIteratorParse(binary_parser, array, constructor, count)


class WhileLoopIteratorDescriptor:
    FUNCTION_NAME = "array_while_iterator"
    
    def deserialize(binary_parser, array, constructor, stop_condition):
        return WhileLoopIteratorConstruct(binary_parser, array, constructor, stop_condition)
    
    def serialize(binary_parser, array, constructor, stop_condition):
        return ForLoopIteratorParse(binary_parser, array, constructor, len(array))

    def count(binary_parser, array, constructor, stop_condition):
        return ForLoopIteratorParse(binary_parser, array, constructor, len(array))

class DoWhileLoopIteratorDescriptor:
    FUNCTION_NAME = "array_do_while_iterator"
    
    def deserialize(binary_parser, array, constructor, stop_condition):
        return DoWhileLoopIteratorConstruct(binary_parser, array, constructor, stop_condition)
    
    def serialize(binary_parser, array, constructor, stop_condition):
        return ForLoopIteratorParse(binary_parser, array, constructor, len(array))

    def count(binary_parser, array, constructor, stop_condition):
        return ForLoopIteratorParse(binary_parser, array, constructor, len(array))
