import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode

class StabilityControlSketch(StabilityBaseNode):
    """スケッチや輪郭線から画像を生成するノード。"""

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
            "prompt": ("STRING", {"multiline": True}),
        })

        # optional入力を追加
        types["optional"].update({
            "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            "control_strength": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step":1}),
            "style_preset": (["none", "3d-model", "analog-film", "anime", "cinematic",
                           "comic-book", "digital-art", "enhance", "fantasy-art",
                           "isometric", "line-art", "low-poly", "modeling-compound",
                           "neon-punk", "origami", "photographic", "pixel-art",
                           "tile-texture"], {"default": "none"}),
            "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"

    def generate(self,
                image: torch.Tensor,
                prompt: str,
                negative_prompt: str = "",
                control_strength: float = 0.7,
                seed: int = 0,
                style_preset: str = "none",
                output_format: str = "png",
                api_key: str = "") -> Tuple[torch.Tensor]:
        """スケッチから画像を生成"""

        client = self.get_client(api_key)

        # 画像サイズのバリデーション
        height, width = image.shape[1:3]
        if width < 64 or height < 64:
            raise ValueError(f"画像の辺は64px以上である必要があります。現在のサイズ: {width}x{height}px")
        if width * height < 4096 or width * height > 9437184:
            raise ValueError(f"総ピクセル数は4096px以上9437184px以下である必要があります。現在のピクセル数: {width * height}px")
        aspect_ratio = width / height
        if aspect_ratio < 0.4 or aspect_ratio > 2.5:
            raise ValueError(f"アスペクト比は1:2.5から2.5:1の間である必要があります。現在のアスペクト比: {aspect_ratio:.2f}")

        # リクエストデータの準備
        data = {
            "prompt": prompt,
            "control_strength": control_strength,
            "seed": seed,
            "output_format": output_format
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if style_preset != "none":
            data["style_preset"] = style_preset

        # ファイルの準備
        files = {
            "image": ("image.png", client.image_to_bytes(image))
        }

        # APIリクエストを実行
        headers = {"Accept": "image/*"}
        response = client._make_request(
            "POST",
            "/v2beta/stable-image/control/sketch",
            data=data,
            files=files,
            headers=headers
        )
        
        # レスポンスの処理とエラーチェック
        self.handle_response(response, "image/*")

        # レスポンスを画像テンソルに変換
        image_tensor = client.bytes_to_tensor(response.content)
        return (image_tensor,)