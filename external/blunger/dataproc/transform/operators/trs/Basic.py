from .BaseTRSOpGroup import TRSOpGroup
from ..translation import parentspace_to_bindspace_translation
from ..rotation import parentspace_to_bindspace_rotation
from ..scale import parentspace_to_bindspace_scale
from ..translation import bindspace_to_parentspace_translation
from ..rotation import bindspace_to_parentspace_rotation
from ..scale import bindspace_to_parentspace_scale


parentspace_to_bindspace = TRSOpGroup(
    parentspace_to_bindspace_translation, 
    parentspace_to_bindspace_rotation, 
    parentspace_to_bindspace_scale
)

bindspace_to_parentspace = TRSOpGroup(
    bindspace_to_parentspace_translation, 
    bindspace_to_parentspace_rotation, 
    bindspace_to_parentspace_scale
)
