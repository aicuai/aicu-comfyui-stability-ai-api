import torch
from typing import Tuple
from .stability_base_node import StabilityBaseNode
import cv2
import numpy as np
import io

class StabilityImageToVideo(StabilityBaseNode):
    """Stability Image to Videoノード"""

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
            "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "step": 1}),
            "cfg_scale": ("FLOAT", {"default": 1.8, "min": 0.0, "max": 10.0, "step": 0.1}),
            "motion_bucket_id": ("INT", {"default": 127, "min": 1, "max": 255, "step": 1}),
        })

        return types

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"

    def generate(self,
                image: torch.Tensor,
                seed: int = 0,
                cfg_scale: float = 1.8,
                motion_bucket_id: int = 127,
                api_key: str = "") -> Tuple[torch.Tensor]:
        """画像からビデオを生成"""

        client = self.get_client(api_key)

        # リクエストデータの準備
        data = {
            "seed": seed,
            "cfg_scale": cfg_scale,
            "motion_bucket_id": motion_bucket_id
        }

        files = {
            "image": ("image.png", client.image_to_bytes(image))
        }

        # 生成を開始
        response = client._make_request(
            "POST",
            "/v2beta/image-to-video",
            data=data,
            files=files
        )

        generation_id = response.json()["id"]

        if response.status_code == 200:
            # 生成完了まで待機
            while True:
                response = client._make_request(
                    "GET",
                    f"/v2beta/image-to-video/result/{generation_id}",
                    headers={"Accept": "video/*"}
                )
                
                # レスポンスの処理とエラーチェック
                self.handle_response(response, "video/*")

                # ビデオデータをバイトストリームとして読み込む
                video_bytes = io.BytesIO(response.content)

                # 一時ファイルにビデオを保存
                temp_file = "temp_video.mp4"
                with open(temp_file, "wb") as f:
                    f.write(response.content)

                # ビデオを読み込む
                cap = cv2.VideoCapture(temp_file)

                frames = []
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # BGRからRGBに変換
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame)

                cap.release()
                import os
                os.remove(temp_file)

                # フレームをnumpy配列に変換 [B, H, W, C]形式
                frames_array = np.stack(frames)
                # float32に変換し、0-1の範囲にスケーリング
                frames_array = frames_array.astype(np.float32) / 255.0
                # フレームをtorch.Tensorに変換（形状は[B, H, W, C]のまま）
                frames_tensor = torch.from_numpy(frames_array)

                return (frames_tensor,)

        else:
            throw_error = response.json()["error"]
            raise Exception(throw_error)