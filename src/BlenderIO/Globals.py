from ...external.blunger.dataproc import ModelTransforms


NAMESPACE = "mvgltools"

MODEL_TRANSFORMS = ModelTransforms(world_axis=['X', 'Z', '-Y'], 
                                   bone_axis=['X', 'Y', 'Z'])
