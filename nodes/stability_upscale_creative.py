import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode
import time

class StabilityUpscaleCreative(StabilityBaseNode):
    """クリエイティブな画像アップスケールを行うノード。"""

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
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step":1}),
            "creativity": ("FLOAT", {"default": 0.3, "min": 0.1, "max": 0.5, "step": 0.01}),
            "style_preset": (["none", "3d-model", "analog-film", "anime", "cinematic",
                           "comic-book", "digital-art", "enhance", "fantasy-art",
                           "isometric", "line-art", "low-poly", "modeling-compound",
                           "neon-punk", "origami", "photographic", "pixel-art",
                           "tile-texture"], {"default": "none"}),
            "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    def upscale(self,
                image: torch.Tensor,
                prompt: str,
                negative_prompt: str = "",
                seed: int = 0,
                creativity: float = 0.3,
                style_preset: str = "none",
                output_format: str = "png",
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像をクリエイティブにアップスケール"""
        client = self.get_client(api_key)

        # 画像サイズのバリデーション
        height, width = image.shape[1:3]
        if width < 64 or height < 64:
            raise ValueError(f"画像の辺は64px以上である必要があります。現在のサイズ: {width}x{height}px")
        if width * height < 4096 or width * height > 1048576:
            raise ValueError(f"総ピクセル数は4096px以上1048576px以下である必要があります。現在のピクセル数: {width * height}px")

        # リクエストデータの準備
        data = {
            "prompt": prompt,
            "seed": seed,
            "creativity": creativity,
            "output_format": output_format
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if style_preset != "none":
            data["style_preset"] = style_preset

        files = {
            "image": ("image.png", client.image_to_bytes(image))
        }

        # 生成開始リクエスト
        init_response = client._make_request(
            "POST",
            "/v2beta/stable-image/upscale/creative",
            data=data,
            files=files,
            headers={"Accept": "*/*"}
        )

        init_data = init_response.json()

        if "id" not in init_data:
            raise Exception("No generation ID in response")

        generation_id = init_data["id"]

        # 生成完了を待機（最大5分）
        retry_count = 0
        max_retries = 30  # 10秒 × 30回 = 5分

        while retry_count < max_retries:
            try:
                # 結果取得リクエスト - application/jsonを使用
                poll_response = client._make_request(
                    "GET",
                    f"/v2beta/results/{generation_id}",
                    headers={"Accept": "*/*"}  # ヘッダーを*/*に変更
                )
                if poll_response.status_code == 200:
                    # アップスケール完了

                    # Content-Typeに基づいて処理を分岐
                    content_type = poll_response.headers.get('content-type', '')

                    if 'application/json' in content_type:
                        # JSONレスポンスの場合
                        response_data = poll_response.json()
                        if 'artifacts' in response_data and response_data['artifacts']:
                            if 'base64' in response_data['artifacts'][0]:
                                import base64
                                image_data = base64.b64decode(response_data['artifacts'][0]['base64'])
                            else:
                                raise Exception("No base64 data in artifact")
                        else:
                            raise Exception("No valid artifacts in response")

                    elif 'image/' in content_type:
                        # 直接画像データが返される場合
                        image_data = poll_response.content
                    else:
                        raise Exception(f"Unexpected content type: {content_type}")

                    # 画像データをテンソルに変換
                    image_tensor = client.bytes_to_tensor(image_data)
                    return (image_tensor,)

                elif poll_response.status_code == 202:
                    # まだ生成中
                    time.sleep(10)  # 10秒待機
                    retry_count += 1
                    continue
                else:
                    raise Exception(f"Unexpected status code: {poll_response.status_code}")

            except Exception as e:
                raise Exception(f"Error while waiting for upscale completion: {str(e)}")

        raise Exception("Upscale timed out after 5 minutes")