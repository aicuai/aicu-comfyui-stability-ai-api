import torch
from typing import Tuple, Optional
from .stability_base_node import StabilityBaseNode

class StabilityEdit(StabilityBaseNode):
    """Stability AIの画像編集機能を提供するノード。"""

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
            "edit_type": (["erase", "inpaint", "outpaint", "search-and-replace",
                         "search-and-recolor", "remove-background"],),
        })

        # optional入力を追加
        types["optional"].update({
            # すべてのedit_type共通のオプション
            "output_format": (["png", "webp"], {"default": "png"}),
            
            # remove-background以外のedit_type用のオプション
            "prompt": ("STRING", {"multiline": True, "default": ""}),
            "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            "mask": ("MASK",),
            "grow_mask": ("INT", {"default": 5, "min": 0, "max": 100, "step":1}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step": 1}),
            "style_preset": (["none", "3d-model", "analog-film", "anime", "cinematic",
                           "comic-book", "digital-art", "enhance", "fantasy-art",
                           "isometric", "line-art", "low-poly", "modeling-compound",
                           "neon-punk", "origami", "photographic", "pixel-art",
                           "tile-texture"], {"default": "none"}),
            # search-and-replace, search-and-recolor用
            "search_or_select_prompt": ("STRING", {"multiline": True, "default": ""}),
            # outpaint用
            "left": ("INT", {"default": 0, "min": 0, "max": 2000, "step":1}),
            "right": ("INT", {"default": 0, "min": 0, "max": 2000, "step":1}),
            "up": ("INT", {"default": 0, "min": 0, "max": 2000, "step":1}),
            "down": ("INT", {"default": 0, "min": 0, "max": 2000, "step":1}),
            "creativity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit"

    def edit(self,
            image: torch.Tensor,
            edit_type: str,
            prompt: str = "",
            negative_prompt: str = "",
            mask: Optional[torch.Tensor] = None,
            grow_mask: int = 5,
            seed: int = 0,
            style_preset: str = "none",
            output_format: str = "png",
            search_or_select_prompt: str = "",
            left: int = 0,
            right: int = 0,
            up: int = 0,
            down: int = 0,
            creativity: float = 0.5,
            api_key: str = "") -> Tuple[torch.Tensor]:
        """画像を編集"""

        client = self.get_client(api_key)

        # マスクの前処理
        if mask is not None and edit_type in ["erase", "inpaint"]:
            # マスクの形状を確認
            if len(mask.shape) == 4:  # [B,C,H,W]形式
                mask = mask.squeeze(0).squeeze(0)  # [H,W]形式に変換
            elif len(mask.shape) == 3:  # [B,H,W]形式
                mask = mask.squeeze(0)  # [H,W]形式に変換

            # マスクの値を0-1の範囲に正規化
            if mask.dtype != torch.float32:
                mask = mask.float()
            if mask.max() > 1.0:
                mask = mask / 255.0

        # 画像サイズのバリデーション
        height, width = image.shape[1:3]
        if edit_type == "remove-background":
            if width * height < 4096 or width * height > 4194304:
                raise ValueError(f"総ピクセル数は4,096から4,194,304ピクセルの間である必要があります。現在のピクセル数: {width * height}px")
            if output_format not in ["png", "webp"]:
                raise ValueError(f"remove-backgroundでは'png'または'webp'のみがサポートされています。指定された形式: {output_format}")
        else:
            if width < 64 or height < 64:
                raise ValueError(f"画像の辺は64px以上である必要があります。現在のサイズ: {width}x{height}px")
            if width * height < 4096 or width * height > 9437184:
                raise ValueError(f"総ピクセル数は4096px以上9437184px以下である必要があります。現在のピクセル数: {width * height}px")
            aspect_ratio = width / height
            if aspect_ratio < 0.4 or aspect_ratio > 2.5:
                raise ValueError(f"アスペクト比は1:2.5から2.5:1の間である必要があります。現在のアスペクト比: {aspect_ratio:.2f}")

        # 編集タイプごとのバリデーション
        if edit_type in ["erase", "inpaint"]:
            if mask is None:
                raise ValueError(f"{edit_type}にはマスクが必要です")
        elif edit_type in ["search-and-replace", "search-and-recolor"]:
            if not search_or_select_prompt:
                raise ValueError(f"{edit_type}には search_or_select_prompt が必要です")
        elif edit_type == "outpaint":
            if not any([left, right, up, down]):
                raise ValueError("outpaintには少なくとも1つの方向の拡張サイズが必要です")
            if not 0 <= creativity <= 1:
                raise ValueError("creativityは0から1の間である必要があります")

        # remove-backgroundの場合は最小限のパラメータのみ使用
        if edit_type == "remove-background":
            data = {
                "output_format": output_format
            }
            files = {
                "image": ("image.png", client.image_to_bytes(image))
            }
        else:
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

            if grow_mask != 5 and edit_type in ["erase", "inpaint"]:
                data["grow_mask"] = grow_mask

            # 編集タイプごとの追加パラメータ
            if edit_type =="search-and-replace":
                data["search_prompt"] = search_or_select_prompt
            elif edit_type == "search-and-recolor":
                data["select_prompt"] = search_or_select_prompt
            elif edit_type == "outpaint":
                data["creativity"] = creativity
                if left: data["left"] = left
                if right: data["right"] = right
                if up: data["up"] = up
                if down: data["down"] = down

            # ファイルの準備
            files = {
                "image": ("image.png", client.image_to_bytes(image))
            }

            if edit_type in ["erase", "inpaint"] and mask is not None:
                # マスクをPNG形式のバイト列に変換
                mask_bytes = client.image_to_bytes(mask)
                files["mask"] = ("mask.png", mask_bytes)

        # APIリクエストを実行
        headers = {"Accept": "image/*"}
        response = client._make_request(
            "POST",
            f"/v2beta/stable-image/edit/{edit_type}",
            data=data,
            files=files,
            headers=headers
        )
        
        # レスポンスの処理とエラーチェック
        self.handle_response(response, "image/*")

        # レスポンスを画像テンソルに変換
        image_tensor = client.bytes_to_tensor(response.content)
        return (image_tensor,)