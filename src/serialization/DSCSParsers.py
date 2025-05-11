from ...external.exbip import Reader
from ...external.exbip import Writer
# from ...external.exbip import Counter
from ...external.exbip import Validator
from ...external.exbip import OffsetCalculator

from . import DSCSDescriptors


class DSCSReader(Reader.extended_with(DSCSDescriptors.DSCS_DESCRIPTORS, DSCSDescriptors.DSCS_ENDIAN_DESCRIPTORS)):
    pass


class DSCSWriter(Writer.extended_with(DSCSDescriptors.DSCS_DESCRIPTORS, DSCSDescriptors.DSCS_ENDIAN_DESCRIPTORS)):
    pass


# class DSCSCounter(Counter.extended_with()):
#     pass


class DSCSValidator(Validator.extended_with(DSCSDescriptors.DSCS_DESCRIPTORS, DSCSDescriptors.DSCS_ENDIAN_DESCRIPTORS)):
    pass


class DSCSOffsetCalculator(OffsetCalculator.extended_with(DSCSDescriptors.DSCS_DESCRIPTORS, DSCSDescriptors.DSCS_ENDIAN_DESCRIPTORS)):
    pass

