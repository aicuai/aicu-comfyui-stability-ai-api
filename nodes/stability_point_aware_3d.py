# nodes/stability_point_aware_3d.py
import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode

class StablePointAware3D(StabilityBaseNode):
    """Stable Point Aware 3D (SPAR3D)を使用して3Dアセットを生成するノード。

    このノードは、ポイントクラウド拡散と高度な背面処理を組み合わせて、
    より詳細な3Dモデルを生成します。
    """

    @classmethod
    def INPUT_TYPES(s):
        # 親クラスのINPUT_TYPESを取得
        types = super().INPUT_TYPES()
        # 必要な入力を追加
        if "required" not in types:
            types["required"] = {}
        if "optional" not in types:
            types["optional"] = {}

        # required入力を追加
        types["required"].update({
            "image": ("IMAGE",),
        })

        # optional入力を追加
        types["optional"].update({
            "texture_resolution": (["512", "1024", "2048"], {"default": "1024"}),
            "foreground_ratio": ("FLOAT", {"default": 1.3, "min": 1.0, "max": 2.0, "step": 0.01}),
            "remesh": (["none", "quad", "triangle"], {"default": "none"}),
            "target_type": (["none", "vertex", "face"], {"default": "none"}),
            "target_count": ("INT", {"default": 5000, "min": 100, "max": 20000, "step": 100}),
            "guidance_scale": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 10.0, "step": 0.1}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step": 1}),
        })

        return types

    RETURN_TYPES = ("MODEL_3D",)  # GLBファイルをバイト列として返す
    RETURN_NAMES = ("model_3d",)
    FUNCTION = "generate"

    def generate(self,
                image: torch.Tensor,
                texture_resolution: str = "1024",
                foreground_ratio: float = 1.3,
                remesh: str = "none",
                target_type: str = "none",
                target_count: int = 5000,
                guidance_scale: float = 3.0,
                seed: int = 0,
                api_key: str = "") -> Tuple[bytes]:
        """3Dモデルを生成
        """
        client = self.get_client(api_key)

        # 画像サイズのバリデーション
        height, width = image.shape[1:3]
        if width < 64 or height < 64:
            raise ValueError(f"画像の辺は64px以上である必要があります。現在のサイズ: {width}x{height}px")
        if width * height < 4096 or width * height > 4194304:
            raise ValueError(f"総ピクセル数は4,096px以上4,194,304px以下である必要があります。現在のピクセル数: {width * height}px")

        # リクエストデータの準備
        data = {
            "texture_resolution": texture_resolution,
            "foreground_ratio": foreground_ratio,
            "guidance_scale": guidance_scale,
            "seed": seed
        }

        if remesh != "none":
            data["remesh"] = remesh

        if target_type != "none":
            data["target_type"] = target_type
            data["target_count"] = target_count

        # ファイルの準備
        files = {
            "image": ("image.png", client.image_to_bytes(image))
        }

        # APIリクエストを実行
        response = client._make_request(
            "POST",
            "/v2beta/3d/stable-point-aware-3d",
            data=data,
            files=files
        )

        return ({"string": response.content, "mimetype": "model/gltf-binary"},)