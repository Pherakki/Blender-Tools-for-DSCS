from . import CounterBase

class OffsetCalculatorBase(CounterBase.CounterBase):
    @staticmethod
    def _get_rw_method(descriptor):
        return getattr(descriptor, "calculate_offsets", descriptor.count)
