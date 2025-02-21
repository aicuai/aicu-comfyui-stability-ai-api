# __init__.py
from .nodes.stability_image_ultra import StabilityImageUltra
from .nodes.stability_image_core import StabilityImageCore
from .nodes.stability_image_sd3 import StabilityImageSD3
from .nodes.stability_upscale_fast import StabilityUpscaleFast
from .nodes.stability_upscale_conservative import StabilityUpscaleConservative
from .nodes.stability_upscale_creative import StabilityUpscaleCreative
from .nodes.stability_edit import StabilityEdit
from .nodes.stability_image_to_video import StabilityImageToVideo
from .nodes.stability_control_sketch import StabilityControlSketch
from .nodes.stability_control_structure import StabilityControlStructure
from .nodes.stability_control_style import StabilityControlStyle
from .nodes.stability_fast_3d import StableFast3D
from .nodes.stability_point_aware_3d import StablePointAware3D
from .nodes.save_3d_model import Save3DModel
from .nodes.preview_3d_model import Preview3DModel


NODE_CLASS_MAPPINGS = {
    "StabilityImageUltra": StabilityImageUltra,
    "StabilityImageCore": StabilityImageCore,
    "StabilityImageSD3": StabilityImageSD3,
    "StabilityUpscaleFast": StabilityUpscaleFast,
    "StabilityUpscaleConservative": StabilityUpscaleConservative,
    "StabilityUpscaleCreative": StabilityUpscaleCreative,
    "StabilityEdit": StabilityEdit,
    "StabilityImageToVideo": StabilityImageToVideo,
    "StabilityControlSketch": StabilityControlSketch,
    "StabilityControlStructure": StabilityControlStructure,
    "StabilityControlStyle": StabilityControlStyle,
    # "StableFast3D": StableFast3D,
    # "StablePointAware3D": StablePointAware3D,
    # "Save3DModel": Save3DModel,
    # "Preview3DModel": Preview3DModel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StabilityImageUltra": "Stability Ultra Image Generation",
    "StabilityImageCore": "Stability Core Image Generation",
    "StabilityImageSD3": "Stability SD3 Image Generation",
    "StabilityUpscaleFast": "Stability Fast Upscaler",
    "StabilityUpscaleConservative": "Stability Conservative Upscaler",
    "StabilityUpscaleCreative": "Stability Creative Upscaler",
    "StabilityEdit": "Stability Image Editor",
    "StabilityImageToVideo": "Stability Image to Video",
    "StabilityControlSketch": "Stability Sketch Control",
    "StabilityControlStructure": "Stability Structure Control",
    "StabilityControlStyle": "Stability Style Control",
    # "StableFast3D": "Stability Fast 3D Generation",
    # "StablePointAware3D": "Stability Point Aware 3D",
    # "Save3DModel": "Save 3D Model",
    # "Preview3DModel": "Preview 3D Model", 
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']