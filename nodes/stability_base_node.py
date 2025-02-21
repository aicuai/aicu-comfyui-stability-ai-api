import torch
from typing import List, Tuple, Dict, Any, Optional
from ..api_client import StabilityAPIClient

class StabilityBaseNode:
    """StabilityAI APIノードの基底クラス"""
    CATEGORY = "Stability AI"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "api_key": ("STRING", {"multiline": False, "default": ""})
            }
        }

    def __init__(self):
        self.client = None

    def get_client(self, api_key: str = "") -> StabilityAPIClient:
        """APIクライアントを取得
        
        Parameters
        ----------
        api_key : str, optional
            APIキー。指定された場合、このキーを優先的に使用
            
        Returns
        -------
        StabilityAPIClient
            APIクライアントインスタンス
        """
        # APIキーが変更された場合、または初回の場合は新しいクライアントを作成
        if self.client is None or (api_key and api_key != self.client.api_key):
            self.client = StabilityAPIClient(api_key if api_key else None)
        return self.client
    
    def handle_response(self, response, content_type: str = None) -> bytes:
        """APIレスポンスを処理し、エラーがあれば適切な例外を発生させる
        
        Parameters
        ----------
        response : requests.Response
            APIレスポンス
        content_type : str, optional
            期待するコンテンツタイプ (例: "image/*", "application/json")
            
        Returns
        -------
        bytes
            処理されたレスポンスコンテンツ
            
        Raises
        ------
        Exception
            様々なAPIエラーに対応する例外
        """
        # ステータスコードに基づくエラーチェック
        if response.status_code == 400:
            error_msg = "無効なパラメータです"
            if response.json().get("errors"):
                error_msg += f": {response.json()['errors']}"
            raise ValueError(error_msg)
            
        elif response.status_code == 401:
            raise ValueError("APIキーが無効です。有効なAPIキーを指定してください。")
            
        elif response.status_code == 403:
            raise ValueError("このリクエストは許可されていません。コンテンツモデレーションに違反している可能性があります。")
            
        elif response.status_code == 404:
            raise ValueError("指定されたリソースが見つかりませんでした。")
            
        elif response.status_code == 413:
            raise ValueError("リクエストのサイズが大きすぎます（最大10MB）。")
            
        elif response.status_code == 422:
            error_msg = "リクエストは正しい形式でしたが、処理できませんでした"
            if response.json().get("errors"):
                error_msg += f": {response.json()['errors']}"
            raise ValueError(error_msg)
            
        elif response.status_code == 429:
            raise ValueError("APIリクエストの制限を超えました。しばらく待ってから再試行してください。")
            
        elif response.status_code == 500:
            raise ValueError("サーバー内部エラーが発生しました。問題が解決しない場合はサポートにお問い合わせください。")
            
        elif response.status_code != 200 and response.status_code != 202:
            raise ValueError(f"予期しないエラーが発生しました（ステータスコード: {response.status_code}）")

        # コンテンツタイプのチェック（指定がある場合）
        if content_type:
            resp_content_type = response.headers.get('content-type', '')
            if not resp_content_type.startswith(content_type.replace('*', '')):
                raise ValueError(f"予期しないコンテンツタイプです: {resp_content_type}")

        return response.content