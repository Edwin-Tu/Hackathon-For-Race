"""
AWS Bedrock 雲端模型串接模組
支援 Claude 3.5 Sonnet 及其他 Bedrock 模型
"""

import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()


class BedrockClient:
    """AWS Bedrock 模型客戶端"""

    def __init__(self, model_id: str = None, region: str = None):
        """
        初始化 Bedrock 客戶端

        Args:
            model_id: Bedrock 模型 ID，預設從環境變數讀取
            region:   AWS 區域，預設從環境變數讀取
        """
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-west-2")
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )

    # ------------------------------------------------------------------
    # 核心推論方法
    # ------------------------------------------------------------------

    def invoke(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        呼叫 Bedrock 模型進行單次推論

        Args:
            prompt:      使用者輸入的提示詞
            max_tokens:  最大回應 token 數
            temperature: 溫度（0.0 ~ 1.0）

        Returns:
            模型回應文字
        """
        body = self._build_request_body(prompt, max_tokens, temperature)

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            return self._parse_response(response)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg  = e.response["Error"]["Message"]
            raise RuntimeError(f"Bedrock API 錯誤 [{error_code}]: {error_msg}") from e

        except NoCredentialsError:
            raise RuntimeError("找不到 AWS 憑證，請確認 .env 或環境變數設定是否正確。")

    def invoke_stream(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7):
        """
        串流呼叫 Bedrock 模型（逐字輸出）

        Args:
            prompt:      使用者輸入的提示詞
            max_tokens:  最大回應 token 數
            temperature: 溫度

        Yields:
            每個串流片段的文字
        """
        body = self._build_request_body(prompt, max_tokens, temperature)

        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                # Claude 3 串流格式
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg  = e.response["Error"]["Message"]
            raise RuntimeError(f"Bedrock 串流 API 錯誤 [{error_code}]: {error_msg}") from e

    def chat(self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        多輪對話介面

        Args:
            messages: 對話歷史，格式為 [{"role": "user"|"assistant", "content": "..."}]
            max_tokens:  最大回應 token 數
            temperature: 溫度

        Returns:
            模型回應文字
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            return self._parse_response(response)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg  = e.response["Error"]["Message"]
            raise RuntimeError(f"Bedrock Chat API 錯誤 [{error_code}]: {error_msg}") from e

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def list_available_models(self) -> list[dict]:
        """列出帳號可用的 Bedrock 基礎模型"""
        mgmt_client = boto3.client(
            service_name="bedrock",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
        response = mgmt_client.list_foundation_models()
        return response.get("modelSummaries", [])

    # ------------------------------------------------------------------
    # 私有輔助方法
    # ------------------------------------------------------------------

    def _build_request_body(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        """建構符合 Claude 3 Messages API 的請求 body"""
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

    def _parse_response(self, response) -> str:
        """解析 Bedrock 回應，取出文字內容"""
        body = json.loads(response["body"].read())
        # Claude 3 格式
        if "content" in body:
            return body["content"][0]["text"]
        # 舊版 Claude 2 格式（備援）
        if "completion" in body:
            return body["completion"]
        return str(body)
