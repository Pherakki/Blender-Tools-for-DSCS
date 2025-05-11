from ..framework.parsers.OffsetCalculatorBase import OffsetCalculatorBase
from ..descriptors import STANDARD_DESCRIPTORS
from ..descriptors import STANDARD_ENDIAN_DESCRIPTORS


class OffsetMarker:
    def __init__(self):
        self.subscribers = []

    def clear(self):
        self.subscribers.clear()

    def subscribe(self, obj, attr):
        def fn(binary_parser):
            setattr(obj, attr, binary_parser.tell())
        self.subscribers.append(fn)
        return self
    
    def subscribe_callback(self, callback):
        self.subscribers.append(callback)
        return self
    
    def notify(self, binary_parser):
        for callback in self.subscribers:
            callback(binary_parser)


class OffsetCalculator(OffsetCalculatorBase.extended_with(STANDARD_DESCRIPTORS, STANDARD_ENDIAN_DESCRIPTORS)):
    pass
