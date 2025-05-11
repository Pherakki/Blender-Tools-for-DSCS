from .Array           import PRIMITIVE_ARRAY_DESCRIPTORS
from .Array           import PRIMITIVE_ENDIAN_ARRAY_DESCRIPTORS
from .Descriptor      import DescriptorDescriptor
from .Iterator        import ForLoopIteratorDescriptor
from .Iterator        import DoWhileLoopIteratorDescriptor
from .Iterator        import WhileLoopIteratorDescriptor
from .Object          import ObjectDescriptor
from .Object          import DynamicObjectDescriptor
from .Object          import DynamicObjectsDescriptor
from .Object          import DynamicObjectsWhileDescriptor
from .Primitive       import PRIMITIVE_DESCRIPTORS
from .Primitive       import PRIMITIVE_ENDIAN_DESCRIPTORS
from .Section         import SectionExistsDescriptor
from .StreamAlignment import AlignmentDescriptor
from .StreamAlignment import FillDescriptor
from .StreamEOF       import AssertEOFDescriptor
from .StreamOffset    import EnforceOffsetDescriptor
from .StreamOffset    import NavigateOffsetDescriptor
from .StreamOffset    import VerifyOffsetDescriptor
from .StreamOffset    import CheckOffsetAsEnforceDescriptor
from .StreamOffset    import CheckOffsetAsVerifyDescriptor
from .StreamMarker    import StreamMarkerDescriptor
from .StreamPadding   import PaddingDescriptor
from .Strings         import BytestringDescriptor
from .Strings         import BytestringsDescriptor
from .Strings         import CBytestringDescriptor
from .Strings         import CBytestringsDescriptor


STANDARD_DESCRIPTORS = [
    AlignmentDescriptor,
    AssertEOFDescriptor,
    BytestringDescriptor,
    BytestringsDescriptor,
    CBytestringDescriptor,
    CBytestringsDescriptor,
    CheckOffsetAsVerifyDescriptor,
    DescriptorDescriptor,
    DynamicObjectDescriptor,
    DynamicObjectsDescriptor,
    DynamicObjectsWhileDescriptor,
    EnforceOffsetDescriptor,
    FillDescriptor,
    ForLoopIteratorDescriptor,
    NavigateOffsetDescriptor,
    ObjectDescriptor,
    PaddingDescriptor,
    *PRIMITIVE_DESCRIPTORS,
    *PRIMITIVE_ARRAY_DESCRIPTORS,
    SectionExistsDescriptor,
    StreamMarkerDescriptor,
    VerifyOffsetDescriptor,
    DoWhileLoopIteratorDescriptor,
    WhileLoopIteratorDescriptor
]

STANDARD_ENDIAN_DESCRIPTORS = [
    *PRIMITIVE_ENDIAN_DESCRIPTORS,
    *PRIMITIVE_ENDIAN_ARRAY_DESCRIPTORS
]
