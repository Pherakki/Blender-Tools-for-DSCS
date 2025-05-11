from ...external.exbip.serializables import traits
from . import DSCSParsers

DSCSReadable         = traits.ReadableTrait(DSCSParsers.DSCSReader)
DSCSWritable         = traits.WriteableTrait(DSCSParsers.DSCSWriter)
DSCSOffsetCalculable = traits.OffsetsCalculableTrait(DSCSParsers.DSCSOffsetCalculator)
DSCSValidatable      = traits.ValidatableTrait(DSCSParsers.DSCSValidator)
