import os

class ValidationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class ValidatorStream:

    def __init__(self):
        self._primary_stream   = None
        self._reference_stream = None
    
    def set_primary_stream(self, stream):
        self._primary_stream = stream
    
    def set_reference_stream(self, stream):
        self._reference_stream = stream
    
    def close(self):
        if self._primary_stream is not None:
            self._primary_stream.close()
            self._primary_stream = None
        if self._reference_stream is not None:
            self._reference_stream.close()
            self._reference_stream = None
    
    def seek(self, offset, whence=os.SEEK_SET):
        self._primary_stream  .seek(offset, whence)
        self._reference_stream.seek(offset, whence)

    def tell(self):
        return self._primary_stream.tell()
    
    def read(self, count):
        data    = self._primary_stream.read(count)
        refdata = self._reference_stream.read(count)
        if data != refdata:
            raise ValidationError(f"Read {data} from primary stream, reference data is {refdata}")
        return data
    
    def write(self, data):
        raise NotImplementedError
