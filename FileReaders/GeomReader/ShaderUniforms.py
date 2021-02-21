class BaseUniform:
    num_floats = None

    def __init__(self, data):
        self.data = data


class DiffuseTextureID(BaseUniform): num_floats = 0
class DiffuseColour(BaseUniform): num_floats = 4  # FP uniform, half-floats?
class NormalMapTextureID(BaseUniform): num_floats = 0
class Bumpiness(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class SpecularStrength(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class SpecularPower(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class CubeMapTextureID(BaseUniform): num_floats = 0
class ReflectionStrength(BaseUniform): num_floats = 1  # FP Uniform, half-float? Works with cube map
class FresnelExp(BaseUniform): num_floats = 1  # FP Uniform, half-float?  ### COULD BE MIXED UP WTH BELOW ####
class FresnelMin(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class FuzzySpecColor(BaseUniform): num_floats = 3  # Only appears in chr435, chr912  ### COULD BE MIXED UP WTH TWO BELOW ####
class SubColor(BaseUniform): num_floats = 3  # Only appears in chr435, chr912
class SurfaceColor(BaseUniform): num_floats = 3  # Only appears in chr435, chr912
class Rolloff(BaseUniform): num_floats = 1  # Only appears in chr435, chr912   ### COULD BE MIXED UP WTH BELOW ####
class VelvetStrength(BaseUniform): num_floats = 1  # Only appears in chr435, chr912
class UnknownTextureSlot1(BaseUniform): num_floats = 0  # Some kind of texture - seems to be sometimes assigned to UV2, sometimes to UV3?
class OverlayTextureID(BaseUniform): num_floats = 0  # UV2 texture? Always appears with OverlayStrength.
class UnknownTextureSlot2(BaseUniform): num_floats = 0  # Overlay normal texture ID? # only appears in d13001f.geom, d13002f.geom, d13003f.geom, d13051b.geom, d13090f.geom, d15008f.geom, d15115f.geom
class OverlayBumpiness(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class OverlayStrength(BaseUniform): num_floats = 1  # FP Uniform, half-float? Blend ratio of 1st and 2nd texture
class ToonTextureID(BaseUniform): num_floats = 0  # idx 0 is texture id, rest are...?
class Curvature(BaseUniform): num_floats = 1  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom  ### COULD BE MIXED UP WTH TWO BELOW ####
class GlassStrength(BaseUniform): num_floats = 1  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
class UpsideDown(BaseUniform): num_floats = 1  # d12301f.geom, d12302f.geom, d12303f.geom, d12351b.geom, d15105f.geom, d15125f.geom, t2405f.geom
class ParallaxBiasX(BaseUniform): num_floats = 1  # d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom  ### COULD BE MIXED UP WTH BELOW ####
class ParallaxBiasY(BaseUniform): num_floats = 1  # d13001f.geom, d13002f.geom, d13003f.geom, d15008f.geom, d15115f.geom
class Time(BaseUniform): num_floats = 1  # VP uniform
class ScrollSpeedSet1(BaseUniform): num_floats = 2  # VP uniform
class ScrollSpeedSet2(BaseUniform): num_floats = 2  # VP uniform
class ScrollSpeedSet3(BaseUniform): num_floats = 2  # VP uniform
class OffsetSet1(BaseUniform): num_floats = 2  # VP uniform
class OffsetSet2(BaseUniform): num_floats = 2  # VP uniform # c.f. Meramon
class DistortionStrength(BaseUniform): num_floats = 1  # FP uniform, half-float?
class LightMapStrength(BaseUniform): num_floats = 1  # FP Uniform, half-float?  ### COULD BE MIXED UP WTH BELOW ####
class LightMapPower(BaseUniform): num_floats = 1  # FP Uniform, half-float?
class OffsetSet3(BaseUniform): num_floats = 2  # VP uniform
class Fat(BaseUniform): num_floats = 1  # VP uniform
class RotationSet1(BaseUniform): num_floats = 1  # VP uniform # eff_bts_chr429_swarhead.geom, eff_bts_chr590_hdr.geom
class RotationSet2(BaseUniform): num_floats = 1  # VP uniform # chr803.geom, chr805.geom, eff_bts_chr803_s02.geom
class ScaleSet1(BaseUniform): num_floats = 2  # VP uniform # eff_bts_chr802_s01.geom
class ZBias(BaseUniform): num_floats = 1  # VP uniform, half-float?
class UnknownTextureSlot3(BaseUniform): num_floats = 0


texture_nodes = [DiffuseTextureID, NormalMapTextureID, CubeMapTextureID, UnknownTextureSlot1,
                 OverlayTextureID, UnknownTextureSlot2, ToonTextureID, UnknownTextureSlot3]
# VP_uniforms = [Time, ScrollSpeedSet1, ScrollSpeedSet2, ScrollSpeedSet3, OffsetSet1, OffsetSet2, OffsetSet3,
#                Fat, RotationSet1, RotationSet2, ScaleSet1, ZBias]
# FP_uniforms = [DiffuseColour, Bumpiness, SpecularStrength, SpecularPower, ReflectionStrength, FresnelExp, FresnelMin,
#                FuzzySpecColor, SubColor, SurfaceColor, Rolloff, VelvetStrength, OverlayBumpiness, OverlayStrength,
#                Curvature, GlassStrength, UpsideDown, ParallaxBiasX, ParallaxBiasY, DistortionStrength,
#                LightMapStrength, LightMapPower]

shader_uniforms_vp_fp = [DiffuseColour, Bumpiness, SpecularStrength, SpecularPower, ReflectionStrength,
                       FresnelExp, FresnelMin, FuzzySpecColor, SubColor, SurfaceColor, Rolloff, VelvetStrength,
                       OverlayBumpiness, OverlayStrength, Curvature, GlassStrength, UpsideDown,
                       ParallaxBiasX, ParallaxBiasY, Time, ScrollSpeedSet1, ScrollSpeedSet2, ScrollSpeedSet3,
                       OffsetSet1, OffsetSet2, DistortionStrength, LightMapStrength, LightMapPower, OffsetSet3,
                       Fat, RotationSet1, RotationSet2, ScaleSet1, ZBias]

all_shader_uniforms = [*texture_nodes, *shader_uniforms_vp_fp]


# These dictionaries are how the shader uniforms are accessed from other files via factory methods
shader_uniforms_from_names = {cls.__name__: cls for cls in all_shader_uniforms}
shader_uniforms_from_defn = {(cls.__name__, cls.num_floats): cls for cls in all_shader_uniforms}
shader_textures = {cls.__name__: cls for cls in texture_nodes}
shader_uniforms_vp_fp_from_names = {cls.__name__: cls for cls in shader_uniforms_vp_fp}