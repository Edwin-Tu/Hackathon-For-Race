# 驗證 UI 實作摘要

## 目的

提供一個不依賴 React、Vue 或外部 CDN 的單頁驗證台，方便在黑客松開發階段觀察：

```text
瀏覽器音訊／文字
→ Whisper
→ Input Guard
→ Skill / Claude
→ Tool Gateway
→ MySQL
→ 本機 TTS / Reminder Output
```

## 路由

- `GET /demo`：驗證頁面
- `GET /demo-assets/app.css`：本機樣式
- `GET /demo-assets/app.js`：本機互動程式

既有 API 沒有改名：

- `POST /api/voice/transcribe`
- `POST /api/voice/turn`
- `POST /api/agent/chat`
- `POST /api/security/input-guard/check`
- `GET /api/reminders/status`
- `POST /api/reminders/run-once`
- `GET /api/output/events`

## 驗證功能

1. 瀏覽器 `MediaRecorder` 錄音，支援 Safari 常見的 `audio/mp4` 與 Chromium 的 `audio/webm`。
2. 音訊檔拖曳與 15 MB 前端預檢。
3. 顯示 Whisper 逐字稿、語言、信心與音訊秒數。
4. 顯示 Input Guard 的 ALLOW/BLOCK、風險分數與分類。
5. 顯示 Agent 回覆、模型、Token、操作狀態與錯誤。
6. 顯示 Tool Gateway 最小化事件，不顯示完整工具參數。
7. 高風險操作可在 UI 送出一次性 confirmation token，但不把 token 顯示在頁面。
8. 顯示 Scheduler 狀態與最近輸出事件。
9. 原始 JSON 可展開查看。

## 安全處理

- 不在 HTML 中嵌入 `.env`、AWS、MySQL 或 Demo Persona 資訊。
- API 動態文字使用 DOM `textContent`，不使用伺服器資料拼接 `innerHTML`。
- 前端不提供 role、persona_id、user_id、authorized_persona_ids 欄位。
- Confirmation token 只保存在頁面記憶體，完成或清除後移除。
- 所有 API 都使用同源相對路徑，不需要 CORS 放寬。

## 使用

```bash
uv sync --extra voice
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

瀏覽器開啟：

```text
http://127.0.0.1:8000/demo
```
