"""Standalone script to verify Bedrock connectivity and Claude model access."""

import os
import sys

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def main() -> None:
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        print("❌ 錯誤：BEDROCK_MODEL_ID 環境變數未設定。")
        print("   請設定 BEDROCK_MODEL_ID，例如：")
        print("   export BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0")
        sys.exit(1)

    region = os.environ.get("AWS_REGION", "us-west-2")
    profile = os.environ.get("AWS_PROFILE")

    print(f"🔍 Bedrock 連線測試")
    print(f"   Region:   {region}")
    print(f"   Model ID: {model_id}")
    if profile:
        print(f"   Profile:  {profile}")
    print()

    session_kwargs: dict = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile

    try:
        session = boto3.Session(**session_kwargs)
        client = session.client("bedrock-runtime")

        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "你好，請用一句話介紹自己。"}],
                }
            ],
            system=[{"text": "用繁體中文回答，簡短即可。"}],
        )

        # Extract reply
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        text = ""
        for block in content_blocks:
            if "text" in block:
                text += block["text"]

        # Extract usage
        usage = response.get("usage", {})
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)
        stop_reason = response.get("stopReason", "")

        print("✅ 呼叫成功！")
        print(f"   模型:       {model_id}")
        print(f"   停止原因:   {stop_reason}")
        print(f"   Input:      {input_tokens} tokens")
        print(f"   Output:     {output_tokens} tokens")
        print(f"   Total:      {input_tokens + output_tokens} tokens")
        print()
        print(f"   回覆: {text}")

    except NoCredentialsError:
        print("❌ 錯誤：找不到 AWS 憑證。")
        print("   請確認已設定 AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY")
        print("   或使用 AWS_PROFILE。")
        sys.exit(1)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"❌ AWS 錯誤 [{error_code}]: {error_msg}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 未預期錯誤: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
