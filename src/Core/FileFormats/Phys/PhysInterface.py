class PhysInterface:
    def __init__(self):
        self.ragdolls  = [] # Contains positions + collider references...
        self.colliders = [] # A collider
        
    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        
        for collider in binary.colliders:
            pass # Convert colliders
            
        for ragdoll in binary.ragdolls:
            pass # Convert ragdolls
            

class BoxColliderInterface:
    pass
   
class ComplexColliderInterface:
    pass

class RagdollInterface:
    def __init__(self):
        self.name_bytes = None
        self.position   = None
        self.rotation   = None
        self.scale      = None
        self.unknown_vec3 = (0.20000000298023224, 0.20000000298023224, 0.6000000238418579)
        self.unknown_float = 0
        self.collider_id = 0
        self.unknown_flag = 0
        
    @property
    def name(self):
        return self.name_bytes.decode('utf8')
    @name.setter
    def name(self, value):
        self.name_bytes = value.encode('utf8')

    @classmethod
    def from_binary(cls, binary):
        instance = cls()
        instance.name_bytes = binary.name.rstrip('\x00')
        instance.position = binary.position
        
