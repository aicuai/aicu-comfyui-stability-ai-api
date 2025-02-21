import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode

class StabilityUpscaleFast(StabilityBaseNode):
    """高速な画像アップスケールを行うノード"""

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
            "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    def upscale(self,
                image: torch.Tensor,
                output_format: str = "png",
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像を高速にアップスケール"""

        client = self.get_client(api_key)

        # 画像サイズのバリデーション
        height, width = image.shape[1:3]
        if width < 32 or width > 1536:
            raise ValueError(f"画像の幅は32px以上1536px以下である必要があります。現在の幅: {width}px")
        if height < 32 or height > 1536:
            raise ValueError(f"画像の高さは32px以上1536px以下である必要があります。現在の高さ: {height}px")
        if width * height < 1024 or width * height > 1048576:
            raise ValueError(f"総ピクセル数は1024px以上1048576px以下である必要があります。現在のピクセル数: {width * height}px")

        # リクエストデータの準備
        data = {
            "output_format": output_format
        }

        files = {
            "image": ("image.png", client.image_to_bytes(image)),
        }

        # APIリクエストを実行
        headers = {"Accept": "image/*"}
        response = client._make_request(
            "POST",
            "/v2beta/stable-image/upscale/fast",
            data=data,
            files=files,
            headers=headers
        )
        
        # レスポンスの処理とエラーチェック
        self.handle_response(response, "image/*")

        # レスポンスを画像テンソルに変換
        image_tensor = client.bytes_to_tensor(response.content)
        return (image_tensor,)