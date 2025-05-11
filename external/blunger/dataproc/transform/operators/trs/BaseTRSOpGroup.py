class TRSOpGroup:
    __slots__ = ("t", "r", "s")
    
    def __init__(self, translation_operator, rotation_operator, scale_operator):
        self.t = translation_operator
        self.r = rotation_operator
        self.s = scale_operator
