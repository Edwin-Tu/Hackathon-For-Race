import argparse
from pathlib import Path

import torch
from transformers import pipeline


MODEL_ID = "MediaTek-Research/Breeze-ASR-26"


def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"

    if torch.cuda.is_available():
        return "cuda"

    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="使用 Breeze-ASR-26 將台語音訊轉成文字"
    )

    parser.add_argument(
        "audio_file",
        help="音訊檔案路徑，例如 taigi_test.mp3",
    )

    args = parser.parse_args()
    audio_path = Path(args.audio_file)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"找不到音訊檔案：{audio_path}"
        )

    if not audio_path.is_file():
        raise ValueError(
            f"指定的路徑不是檔案：{audio_path}"
        )

    device = get_device()

    print(f"使用裝置：{device}")
    print("開始載入 Breeze-ASR-26 模型，第一次執行會下載模型。")

    transcriber = pipeline(
        task="automatic-speech-recognition",
        model=MODEL_ID,
        device=device,
    )

    result = transcriber(
        str(audio_path),
        return_timestamps=True,
    )

    text = result.get("text", "").strip()

    print("辨識結果：")

    if text:
        print(text)
    else:
        print("沒有辨識到文字。")


if __name__ == "__main__":
    main()