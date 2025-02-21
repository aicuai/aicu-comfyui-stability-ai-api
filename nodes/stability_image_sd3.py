import torch
from typing import Tuple, Optional
from .stability_base_node import StabilityBaseNode

class StabilityImageSD3(StabilityBaseNode):
    """Stability SD3 Image Generationノード"""

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
            "prompt": ("STRING", {"multiline": True}),
            "model": (["sd3.5-large", "sd3.5-large-turbo", "sd3.5-medium", "sd3-large", "sd3-large-turbo", "sd3-medium"],),
            "mode": (["text-to-image", "image-to-image"],),
        })

        # optional入力を追加
        types["optional"].update({
            "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step": 1}),
            "cfg_scale": ("FLOAT", {"default": 7.0, "min": 1.0, "max": 10.0, "step": 0.1}),
            "image": ("IMAGE",),
            "strength": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01}),
            "aspect_ratio": (["1:1", "3:2", "4:3", "16:9", "2:3", "3:4", "9:16"], {"default": "1:1"}),
            "style_preset": (["none", "enhance", "anime", "photographic", "digital-art", "comic-book", "pixel-art", "cinematic", "3d-model", "origami"], {"default": "none"}),
            "output_format": (["png", "webp"], {"default": "png"}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"

    def generate(self,
                prompt: str,
                model: str,
                mode: str,
                negative_prompt: str = "",
                seed: int = 0,
                cfg_scale: float = 7.0,
                image: Optional[torch.Tensor] = None,
                strength: float = 0.7,
                aspect_ratio: str = "1:1",
                style_preset: str = "none",
                output_format: str = "png",
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像を生成"""

        client = self.get_client(api_key)

        # リクエストデータの準備
        data = {
            "prompt": prompt,
            "model": model,
            "mode": mode,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "output_format": output_format
        }

        # パラメータのバリデーション
        if mode == "image-to-image":
            if image is None:
                raise ValueError("image-to-imageモードでは入力画像が必須です")
            if strength is None:
                raise ValueError("image-to-imageモードではstrengthパラメータが必須です")
        else:
            # text-to-imageの場合はアスペクト比を指定
            data["aspect_ratio"] = aspect_ratio

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if style_preset != "none":
            data["style_preset"] = style_preset

        if mode == "image-to-image":
            data["strength"] = strength

        # APIリクエストを実行
        headers = {"Accept": "image/*"}
        
        files = {}
        if mode == "image-to-image":
            files["image"] = ("image.png", client.image_to_bytes(image))
        
        response = client._make_request(
                "POST",
                "/v2beta/stable-image/generate/sd3",
                data=data,
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
                    raise Exception("No base64 data in artifact")
            else:
                raise Exception("No valid artifacts in response")
        elif 'image/' in content_type:
            # 直接画像データが返される場合
            image_bytes = response.content
        else:
            raise Exception(f"Unexpected content type: {content_type}")

        # 画像データをテンソルに変換
        image_tensor = client.bytes_to_tensor(image_bytes)
        return (image_tensor,)