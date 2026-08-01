# Backend Voice + Reminder Implementation

## 已實作範圍

本版本在既有 Input Guard、Agent、Skill、Tool Gateway 與 MySQL 上加入：

1. 本機 faster-whisper 轉錄服務
2. `/api/voice/transcribe`
3. `/api/voice/turn`
4. 背景 Reminder Scheduler
5. MySQL 原子 claim：`scheduled → triggering`
6. 成功、失敗與錯過狀態：`triggered / failed / missed`
7. 啟動時回收 stale `triggering` reminder
8. 傳輸中立 `OutputEnvelope`
9. 有界 Output Event Store 與輪詢 API
10. Console、macOS/Windows/Linux 本機鈴聲
11. macOS `say`、Windows SAPI、Linux `spd-say`/`espeak` TTS
12. UI 未接時的 CLI 驗證腳本

## 安全與可靠性

- 上傳音訊限制 MIME、副檔名與最大位元組數。
- 音訊只寫入臨時檔，轉錄後立即刪除。
- Whisper 模型延遲載入，載入與推論以鎖序列化。
- `/api/voice/turn` 仍進入原本的 Input Guard 與 Agent 管線。
- Scheduler 使用資料庫交易與 `FOR UPDATE SKIP LOCKED`，避免多 worker 重複播報。
- 本機音訊失敗不會讓 Console 與 Output Event Store 的提醒失效。
- TTS 命令使用參數陣列執行，不使用 shell interpolation。
- 未新增或修改資料表；直接對接現有 `reminders` 欄位。

## 測試結果

```text
111 passed in 6.17s
```

新增測試包含：

- 到期 reminder 只觸發一次
- 未到期 reminder 不觸發
- 過期 reminder 標為 missed
- 全部輸出失敗時標為 failed
- Output Event Store 單調 ID 與 after_id
- 音訊後端失敗但事件儲存成功
- Whisper trace 與空逐字稿
- 語音轉錄 API
- 語音到 Agent API
- 不支援音訊格式拒絕

## 本機啟動

```bash
uv sync --extra voice
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 快速驗證提醒

```bash
uv run python -m scripts.reminder_trigger_demo --title "喝水" --delay-seconds 10
```

## 快速驗證 Whisper

```bash
uv run python -m scripts.whisper_check --load-model
uv run python -m scripts.whisper_check sample.wav --language zh
```

## 尚未實作

- 瀏覽器 MediaRecorder UI
- WebSocket 即時推送
- 瀏覽器 TTS 佇列
- JWT/Cognito 正式身分驗證
- Output Event 持久化資料表

## 驗證邊界

此建置環境沒有使用者的 MySQL、AWS 臨時憑證、faster-whisper 模型與 macOS 音訊裝置，因此未在沙盒內執行真實的 Bedrock、MySQL、Whisper 模型下載或 `say`/`afplay` 播放。上述項目需在 Mac 依照 README 指令完成一次實機驗證。
