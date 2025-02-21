# nodes/save_3d_model.py
import os
from typing import Tuple

class Save3DModel:
    """3Dモデルを保存するノード"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_3d": ("MODEL_3D",),
                "filename": ("STRING", {"default": "model"}),
                "model_type": (["GLB", "OBJ", "PLY"], {"default": "GLB"}),
            },
             "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("MODEL_3D",) 
    RETURN_NAMES = ("model_3d",) 
    FUNCTION = "save_model"
    OUTPUT_NODE = True
    CATEGORY = "Stability AI"

    def save_model(self, model_3d, filename: str, model_type:str, prompt=None, extra_pnginfo=None) -> Tuple:
        """3Dモデルを保存"""

        model_bytes = model_3d["string"] # バイトデータを取得

        # 出力ディレクトリの作成
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 拡張子を付ける
        filename += "." + model_type.lower()
        # ファイルパスの作成
        filepath = os.path.join(output_dir, filename)

        # GLBファイルとして保存
        with open(filepath, 'wb') as f:
            f.write(model_bytes)

        print(f"[comfyui-stability-ai-api] Saved: {filepath}")

        return ({"string": model_bytes, "mimetype": "model/gltf-binary"},)