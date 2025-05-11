from .Translation import TranslationTransforms
from .Rotation    import RotationTransforms


class TRTransforms:
    __slots__ = ("translation", "rotation")
    
    def __init__(self, translation, rotation):
        self.translation = TranslationTransforms.from_dynamic(translation)
        self.rotation    = RotationTransforms.from_dynamic(rotation)
