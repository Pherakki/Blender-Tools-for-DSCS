from .Traits import DSCSReadable, DSCSWritable, DSCSOffsetCalculable, DSCSValidatable


class DSCSSerializable(DSCSReadable, DSCSWritable, DSCSOffsetCalculable, DSCSValidatable):
    pass
