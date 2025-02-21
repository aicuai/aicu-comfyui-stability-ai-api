import torch
from typing import Tuple, Optional
from .stability_base_node import StabilityBaseNode

class StabilityImageUltra(StabilityBaseNode):
    """Stability Ultra Image Generationノード"""

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
            "aspect_ratio": (["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"], {"default": "1:1"}),
        })

        # optional入力を追加
        types["optional"].update({
            "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step":1}),
            "style_preset": (["none", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art",
                            "enhance", "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound",
                            "neon-punk", "origami", "photographic", "pixel-art", "tile-texture"], {"default": "none"}),
            "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
            "image": ("IMAGE",),  # 入力画像（オプション）
            "strength": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01}),  # 画像の影響度
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
                image: Optional[torch.Tensor] = None,
                strength: float = 0.7,
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像を生成"""

        # APIクライアントを取得（APIキーが指定されている場合はそれを使用）
        client = self.get_client(api_key)

        # 入力画像のバリデーション
        if image is not None:
            # 画像サイズの取得
            height, width = image.shape[1:3]

            # サイズ制限のチェック
            if width < 64 or width > 16384:
                raise ValueError(f"画像の幅は64px以上16,384px以下である必要があります。現在の幅: {width}px")
            if height < 64 or height > 16384:
                raise ValueError(f"画像の高さは64px以上16,384px以下である必要があります。現在の高さ: {height}px")
            if width * height < 4096:
                raise ValueError(f"総ピクセル数は4,096px以上である必要があります。現在のピクセル数: {width * height}px")

            # strengthパラメータのチェック
            if strength is None:
                raise ValueError("strengthパラメータは画像が指定されている場合は必須です")

        # リクエストデータの準備
        data = {
            "prompt": prompt,
            "seed": seed,
            "output_format": output_format
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if style_preset != "none":
            data["style_preset"] = style_preset

        # 入力画像がある場合（image-to-image）
        files = {}
        if image is not None:
            data["strength"] = strength
            files["image"] = ("image.png", client.image_to_bytes(image))
        else:
            # text-to-imageの場合はアスペクト比を指定
            data["aspect_ratio"] = aspect_ratio

        # APIリクエストを実行（画像データを直接受け取る）
        headers = {
            "Accept": "image/*"  # 画像データを直接受け取る
        }

        # multipart/form-dataとしてデータを送信
        for key, value in data.items():
            files[key] = (None, str(value))


        response = client._make_request(
            "POST",
            "/v2beta/stable-image/generate/ultra",
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