# 中文＋台語語音整合

此版本以 Bryan 的 FastAPI／Input Guard／Agent／Tool Gateway／RDS 後端為主，套用 Edwin-Tu-2 的長者 UI，並只抽取 `feature-breeze-asr-v2` 的 Breeze-ASR-26 模型選擇邏輯。沒有合併 Breeze 分支的 Prisma schema、資料庫 migration、假登入或舊 UI。

## 完整流程

```text
Edwin-Tu-2 長者 UI
  → Next.js server-side proxy（Bearer Token 不進入瀏覽器）
  → POST /api/voice/turn
  → 中文：faster-whisper
     台語：Breeze-ASR-26
  → Input Guard
  → Claude Agent／Tool Gateway／RDS
  → 中文輸入：Agent 原回覆
     台語輸入：Agent 原回覆完整翻成台語
  → 中文：瀏覽器或既有本機 TTS
     台語：facebook/mms-tts-nan WAV
  → UI 播放
```

Agent 的原始 `reply` 不會被覆寫。台語翻譯放在 `translated_reply`，因此工具結果、原始回覆和翻譯可以分開稽核。

## 後端本機啟動

```bash
cp .env.example .env
uv sync --extra bilingual-voice
```

在 `.env` 開啟：

```env
ASR_MODE=hybrid
ASR_AUTO_PRIMARY=whisper
ASR_FALLBACK_ENABLED=true
BREEZE_ASR_ENABLED=true
BREEZE_ASR_DEVICE=auto
TAIWANESE_REPLY_TRANSLATION_ENABLED=true
TAIWANESE_TTS_ENABLED=true
TAIWANESE_TTS_DEVICE=auto
```

Mac 會優先使用 MPS；沒有 MPS／CUDA 時回退 CPU。第一次台語辨識與台語 TTS 會下載模型。

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Edwin UI 啟動

```bash
cd frontend
cp .env.example .env.local
```

`.env.local`：

```env
SMART_CARE_API_URL=http://127.0.0.1:8000
SMART_CARE_API_TOKEN=
```

若後端開啟 `API_AUTH_ENABLED=true`，將相同 Bearer Token 放在 `SMART_CARE_API_TOKEN`。這是 Next.js 伺服器端變數，不可改成 `NEXT_PUBLIC_...`。

```bash
npm install
npm run dev
```

開啟 `http://localhost:3000/resident/voice`。在既有「帳號設置」中選中文或台語，按下原頁面新增的語音互動按鈕錄音。

## API 回傳

台語回合保留兩份文字：

```json
{
  "agent": {
    "reply": "好的，我已經幫你記錄。"
  },
  "translated_reply": "好，我已經共你記錄矣。",
  "reply_language": "nan-TW",
  "speech_delivery": {
    "backend": "mms_tts:facebook/mms-tts-nan",
    "content_type": "audio/wav",
    "audio_base64": "..."
  }
}
```

翻譯層要求完整翻譯，不使用固定回覆模板；數字、時間、UUID、URL 與英文字詞遺失時會拒絕該翻譯並回退中文回覆。

## 驗證

```bash
python -m pytest -q
python -m compileall -q app tests scripts
```

使用真實中文音檔：

```bash
python scripts/bilingual_voice_smoke.py sample-zh.wav \
  --language zh-TW
```

使用真實台語音檔：

```bash
python scripts/bilingual_voice_smoke.py sample-nan.wav \
  --language nan-TW
```

## 雲端注意事項

目前既有 ECS Task 是 2 vCPU／4 GB。此版本保留雲端預設：

```env
BREEZE_ASR_ENABLED=false
TAIWANESE_TTS_ENABLED=false
```

因此原本 Whisper 雲端鏈路不會因缺少大型模型而中斷。要在同一映像啟用台語模型，部署時至少必須：

```bash
export INSTALL_BILINGUAL_VOICE=true
export BREEZE_ASR_ENABLED=true
export TAIWANESE_TTS_ENABLED=true
export PRELOAD_BREEZE=true
export PRELOAD_TAIWANESE_TTS=true
```

Breeze-ASR-26 較大，不建議直接放進目前 2 vCPU／4 GB Task。比賽版本優先在 Mac MPS 執行 Breeze／台語 TTS，Agent、Tool Gateway 與 RDS 繼續使用雲端；或將 Breeze 拆成獨立高記憶體服務。
