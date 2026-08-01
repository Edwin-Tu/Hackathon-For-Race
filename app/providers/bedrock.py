"""Amazon Bedrock provider using the Converse API."""

import asyncio
import logging
import time
from typing import Any

import boto3
from botocore.exceptions import (
    ClientError,
    ConnectionError as BotoConnectionError,
    ConnectTimeoutError,
    NoCredentialsError,
    ParamValidationError,
    ReadTimeoutError,
)

from app.config import settings
from app.models import ProviderResponse, ToolUseBlock, UsageInfo
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class BedrockProvider(BaseLLMProvider):
    """Provider that calls Amazon Bedrock Runtime Converse API."""

    def __init__(self) -> None:
        session_kwargs: dict = {"region_name": settings.AWS_REGION}
        if settings.AWS_PROFILE:
            session_kwargs["profile_name"] = settings.AWS_PROFILE

        session = boto3.Session(**session_kwargs)
        self._client = session.client("bedrock-runtime")
        self._model_id = settings.BEDROCK_MODEL_ID

    def _build_converse_params(
        self,
        messages: list[dict],
        system_prompt: str,
        tool_config: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> dict:
        """Build parameters for the Converse API call."""
        converse_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content")

            # Handle different content formats
            if isinstance(content, str):
                converse_messages.append({
                    "role": role,
                    "content": [{"text": content}],
                })
            elif isinstance(content, list):
                # Already formatted content blocks (for tool results)
                converse_messages.append({
                    "role": role,
                    "content": content,
                })
            else:
                # Fallback
                converse_messages.append({
                    "role": role,
                    "content": [{"text": str(content)}],
                })

        params = {
            "modelId": self._model_id,
            "messages": converse_messages,
            "system": [{"text": system_prompt}],
        }

        if tool_config:
            # Backward compatible: callers may provide either the tools list or
            # a complete Bedrock toolConfig object containing toolChoice.
            if isinstance(tool_config, dict):
                params["toolConfig"] = tool_config
            else:
                params["toolConfig"] = {"tools": tool_config}

        return params

    def _sync_converse(self, params: dict) -> tuple[dict, int]:
        """Synchronous call to Bedrock Converse API with timing."""
        start_ms = time.perf_counter_ns() // 1_000_000
        response = self._client.converse(**params)
        end_ms = time.perf_counter_ns() // 1_000_000
        latency_ms = end_ms - start_ms
        return response, latency_ms

    def _log_converse_response(
        self,
        response: dict,
        latency_ms: int,
        tool_names: list[str],
    ) -> None:
        """
        Log Bedrock converse response without sensitive data.
        
        DOES NOT log:
        - AWS credentials
        - Full prompt/messages
        - Tool argument values
        - Confirmation tokens
        """
        metadata = response.get("ResponseMetadata", {})
        usage = response.get("usage", {})
        
        logger.info(
            "Bedrock converse completed: "
            "request_id=%s http_status=%s model=%s stop_reason=%s "
            "input_tokens=%s output_tokens=%s latency_ms=%s tool_names=%s",
            metadata.get("RequestId", "unknown"),
            metadata.get("HTTPStatusCode", 0),
            self._model_id,
            response.get("stopReason", ""),
            usage.get("inputTokens", 0),
            usage.get("outputTokens", 0),
            latency_ms,
            tool_names if tool_names else [],
        )

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tool_config: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> ProviderResponse:
        """Call Bedrock Converse API via asyncio.to_thread to avoid blocking."""
        params = self._build_converse_params(messages, system_prompt, tool_config)

        try:
            response, latency_ms = await asyncio.to_thread(self._sync_converse, params)

            # Extract content from response
            output = response.get("output", {})
            message = output.get("message", {})
            content_blocks = message.get("content", [])

            # Parse text and toolUse blocks
            text = ""
            tool_use_blocks: list[ToolUseBlock] = []
            tool_names: list[str] = []

            for block in content_blocks:
                if "text" in block:
                    text += block["text"]
                elif "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_names.append(tool_use["name"])
                    tool_use_blocks.append(ToolUseBlock(
                        tool_use_id=tool_use["toolUseId"],
                        name=tool_use["name"],
                        input=tool_use.get("input", {}),
                    ))

            # Log response (no sensitive data)
            self._log_converse_response(response, latency_ms, tool_names)

            # Extract usage
            usage_data = response.get("usage", {})
            input_tokens = usage_data.get("inputTokens", 0)
            output_tokens = usage_data.get("outputTokens", 0)

            return ProviderResponse(
                success=True,
                text=text,
                model=self._model_id,
                stop_reason=response.get("stopReason", ""),
                usage=UsageInfo(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                ),
                tool_use_blocks=tool_use_blocks,
                raw_content=content_blocks,
            )

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return ProviderResponse(
                success=False,
                error_type="NoCredentialsError",
                error_message="找不到 AWS 憑證。請設定環境變數或 AWS Profile。",
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Bedrock ClientError: %s - %s", error_code, error_msg)

            error_map = {
                "ExpiredTokenException": (
                    "ExpiredToken",
                    "AWS 憑證已過期，請重新取得。",
                ),
                "AccessDeniedException": (
                    "AccessDeniedException",
                    f"存取被拒絕：{error_msg}",
                ),
                "ValidationException": (
                    "ValidationException",
                    f"請求驗證失敗：{error_msg}",
                ),
                "ThrottlingException": (
                    "ThrottlingException",
                    "請求過於頻繁，請稍後重試。",
                ),
            }

            if error_code in error_map:
                err_type, err_message = error_map[error_code]
                return ProviderResponse(
                    success=False,
                    error_type=err_type,
                    error_message=err_message,
                )

            return ProviderResponse(
                success=False,
                error_type=error_code,
                error_message=error_msg,
            )

        except ParamValidationError as e:
            logger.error("Parameter validation error: %s", e)
            return ProviderResponse(
                success=False,
                error_type="ValidationException",
                error_message=f"參數驗證錯誤：{e}",
            )

        except (ConnectTimeoutError, ReadTimeoutError) as e:
            logger.error("Bedrock timeout: %s", e)
            return ProviderResponse(
                success=False,
                error_type="TimeoutError",
                error_message="連線逾時，請稍後重試。",
            )

        except BotoConnectionError as e:
            logger.error("Bedrock connection error: %s", e)
            return ProviderResponse(
                success=False,
                error_type="ConnectionError",
                error_message="無法連線到 AWS Bedrock 服務，請檢查網路連線。",
            )

        except Exception as e:
            logger.exception("Unexpected error calling Bedrock")
            return ProviderResponse(
                success=False,
                error_type="UnexpectedError",
                error_message=f"未預期的錯誤：{type(e).__name__}: {e}",
            )
