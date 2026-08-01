"""
AWS Bedrock 串接測試入口
執行方式：python main.py
"""

from bedrock_client import BedrockClient


def test_basic_invoke():
    """測試基本單次推論"""
    print("=" * 60)
    print("【測試 1】基本推論")
    print("=" * 60)

    client = BedrockClient()
    prompt = "請用繁體中文介紹你自己，並說明你是哪個 AI 模型。"

    print(f"模型：{client.model_id}")
    print(f"區域：{client.region}")
    print(f"提示：{prompt}\n")

    response = client.invoke(prompt)
    print("回應：")
    print(response)
    print()


def test_stream_invoke():
    """測試串流推論（逐字輸出）"""
    print("=" * 60)
    print("【測試 2】串流推論")
    print("=" * 60)

    client = BedrockClient()
    prompt = "請用繁體中文列舉 3 個台灣著名景點，並各寫一句描述。"

    print(f"提示：{prompt}\n")
    print("串流回應：")

    for chunk in client.invoke_stream(prompt):
        print(chunk, end="", flush=True)
    print("\n")


def test_chat():
    """測試多輪對話"""
    print("=" * 60)
    print("【測試 3】多輪對話")
    print("=" * 60)

    client = BedrockClient()
    messages = [
        {"role": "user",      "content": "你好，請記住一個數字：42"},
        {"role": "assistant", "content": "好的，我記住了，那個數字是 42。"},
        {"role": "user",      "content": "我剛才讓你記住的數字是什麼？"},
    ]

    print("對話歷史：")
    for msg in messages:
        print(f"  [{msg['role']}] {msg['content']}")
    print()

    response = client.chat(messages)
    print(f"模型回應：{response}\n")


def main():
    print("\n🚀 AWS Bedrock 雲端模型串接測試開始\n")

    try:
        test_basic_invoke()
        test_stream_invoke()
        test_chat()
        print("✅ 所有測試通過！AWS Bedrock 串接成功。")

    except RuntimeError as e:
        print(f"\n❌ 錯誤：{e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
