class Preview3DModel:
    """3Dモデルをプレビュー表示するノード"""
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_3d": ("MODEL_3D",),
            },
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "preview"
    OUTPUT_NODE = True
    CATEGORY = "Stability AI/preview"
    
    def preview(self, model_3d):
        """
        3Dモデルをプレビュー表示する
        
        Parameters:
        -----------
        model_3d : dict
            3Dモデルデータ。以下のキーを含む:
            - string: モデルデータのバイト列
            - mimetype: モデルのMIMEタイプ (例: "model/gltf-binary")
        
        Returns:
        --------
        tuple
            空のタプル (このノードは出力を生成しない)
        """
        from server import PromptServer
        
        # モデルタイプを取得 (例: "model/gltf-binary" -> "glb")
        model_type = model_3d["mimetype"].split("/")[-1]
        if model_type == "gltf-binary":
            model_type = "glb"
            
        # プレビューイベントを発火
        PromptServer.instance.send_sync("preview_3d_model", {
            "model_data": model_3d["string"],  # モデルのバイナリデータ
            "model_type": model_type,          # モデルの種類 (glb, obj, ply など)
        })
        
        return ()