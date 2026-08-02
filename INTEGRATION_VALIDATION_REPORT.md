# 整合與除錯驗證報告

## 整合基底

- 後端、安全層、Agent、Tool Gateway、RDS：`Hackathon-For-Race-Bryan-backend-hardening-v4`
- UI：`Hackathon-For-Race-Edwin-Tu-2`
- 台語 ASR 模型選擇：`Hackathon-For-Race-feature-breeze-asr-v2/test_breeze_asr.py`

沒有合併 Breeze／Edwin 分支中的 Prisma schema、migration、資料庫連線檔、舊 Bedrock client 或未接線的授權 middleware。

## 已完成

- 中文 `zh-TW` → faster-whisper
- 台語 `nan-TW` → Breeze-ASR-26
- 指定 ASR 不可用／空結果時安全 fallback
- Agent 原始回覆完整保留
- 台語輸入時，將完整 Agent 回覆另行翻成台語
- 產生台語漢字顯示文字及 TTS 羅馬字
- MMS Min Nan TTS 產生 WAV，透過 API base64 回傳並由 UI 播放
- 工具確認後仍依原語言翻譯／發音
- Next.js server-side proxy 隱藏 FastAPI Bearer Token
- 修正 Edwin UI 原本 `microphone=()` 導致瀏覽器拒絕錄音的錯誤
- 保留 Edwin UI 其他頁面、主題、色彩、導覽與元件

## 自動驗證

```text
Backend pytest: 147 passed
Python compileall: passed
Modified TS/TSX syntax transpilation: passed
Cloud deployment shell syntax: passed
CloudFormation / Compose YAML syntax: passed
Secret scan: passed
```

新增測試涵蓋：

- Breeze 模型只常駐載入並回傳台語 trace
- 中文／台語 ASR 路由
- ASR fallback
- Agent 回覆完整台語翻譯與必要值保留
- WAV 編碼
- `/api/voice/turn` 台語翻譯＋TTS 音訊回傳

## UI 變更範圍

與 Edwin-Tu-2 比對後，只有：

- `src/pages/resident/voice.tsx`：接入錄音、API、播放、確認與語言選擇
- `src/pages/api/smart-care/*`：新增 server-side proxy
- `src/server/smartCareProxy.ts`：新增 proxy helper
- `next.config.ts`：將 `microphone=()` 修成 `microphone=(self)`

沒有修改其他 UI 頁面、theme、layout 或共用元件的設計。

## 尚需在使用者電腦實測

本執行環境無法從外部下載大型 Hugging Face 模型，因此沒有假稱實際跑過 Breeze-ASR-26 或 MMS TTS。兩者採 lazy loading，需在 Mac 執行：

```bash
uv sync --extra bilingual-voice
```

此外，內部 npm registry 缺少 `zod-validation-error` 與 `yaml` 套件，因此無法在此環境完成 `npm ci`／`next build`。已對所有新增或修改的 TypeScript/TSX 檔做語法轉譯檢查；請在正常 npm registry 的 Mac 上補跑：

```bash
cd frontend
npm install
npm run type-check
npm run build
```
