import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode

class StabilityImageCore(StabilityBaseNode):
    """Stability Core Image Generationノード"""

    @classmethod
    def INPUT_TYPES(s):
        # 親クラスのINPUT_TYPESを取得
        types = super().INPUT_TYPES()
        # 必要な入力を追加
        if "required" not in types:
            types["required"] = {}

        # required入力を追加
        types["required"].update({
            "prompt": ("STRING", {"default": "", "multiline": True}),
            "aspect_ratio": (["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"], {"default": "1:1"}),
            "negative_prompt": ("STRING", {"default": "", "multiline": True}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            "style_preset": (["none", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art",
                            "enhance", "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound",
                            "neon-punk", "origami", "photographic", "pixel-art", "tile-texture"], {"default": "none"}),
            "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"

    def generate(self,
                prompt: str,
                aspect_ratio: str,
                negative_prompt: str = "",
                seed: int = 0,
                style_preset: str = "none",
                output_format: str = "png",
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像を生成"""
        client = self.get_client(api_key)
        # リクエストデータの準備
        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "seed": seed,
            "output_format": output_format
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if style_preset != "none":
            data["style_preset"] = style_preset

        # APIリクエストを実行（画像データを直接受け取る）
        headers = {
            "Accept": "image/*"  # 画像データを直接受け取る
        }

        # multipart/form-dataとしてデータを送信
        files = {}
        for key, value in data.items():
            files[key] = (None, str(value))

        response = client._make_request(
            "POST",
            "/v2beta/stable-image/generate/core",
            files=files,
            headers=headers
        )
        
        # レスポンスの処理とエラーチェック
        self.handle_response(response, "image/*")

        # Content-Typeに基づいて処理を分岐
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            # JSONレスポンスの場合
            response_data = response.json()

            if 'artifacts' in response_data and response_data['artifacts']:
                image_data = response_data['artifacts'][0].get('base64')
                if image_data:
                    import base64
                    image_bytes = base64.b64decode(image_data)
                else:
                    raise Exception("No base64 image data in response")
            else:
                raise Exception("No artifacts in response")
        elif 'image/' in content_type:
            # 画像データの場合
            image_bytes = response.content
        else:
            raise Exception(f"Unexpected content type: {content_type}")

        # バイト列を画像テンソルに変換
        image_tensor = client.bytes_to_tensor(image_bytes)
        return (image_tensor,)