# Edwin UI 與 Smart Care FastAPI 整合

此目錄保留 Edwin-Tu-2 的頁面、色彩、導覽、提醒卡與設定視覺。整合只新增：

- 麥克風錄音與送出
- 中文／台語選擇
- Agent 回覆顯示與播放
- 工具確認／取消
- Next.js 伺服器端 API Proxy
- `Permissions-Policy` 的 `microphone=(self)` 修正

瀏覽器不會取得 FastAPI Bearer Token。Token 僅由下列 Next.js API routes 在伺服器端加入：

- `/api/smart-care/voice-turn`
- `/api/smart-care/voice-confirm`
- `/api/smart-care/health`
