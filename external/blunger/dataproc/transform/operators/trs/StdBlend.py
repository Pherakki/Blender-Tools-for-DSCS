from .BaseTRSOpGroup import TRSOpGroup
from ..translation import parentspace_to_bindspace_translation_additiveblend
from ..rotation import parentspace_to_bindspace_rotation_multblend
from ..scale import parentspace_to_bindspace_scale_multblend
from ..translation import bindspace_to_parentspace_translation_additiveblend
from ..rotation import bindspace_to_parentspace_rotation_multblend
from ..scale import bindspace_to_parentspace_scale_multblend


parentspace_to_bindspace_stdblend = TRSOpGroup(
    parentspace_to_bindspace_translation_additiveblend, 
    parentspace_to_bindspace_rotation_multblend, 
    parentspace_to_bindspace_scale_multblend
)

bindspace_to_parentspace_stdblend = TRSOpGroup(
    bindspace_to_parentspace_translation_additiveblend, 
    bindspace_to_parentspace_rotation_multblend, 
    bindspace_to_parentspace_scale_multblend
)
