# 智護聲盾 UI 設計規格 (React + TypeScript)

## 1. 架構概覽
- **框架**：Next.js (React 18) + TypeScript
- **樣式**：Material‑UI (MUI) + Emotion（支援主題切換）
- **狀態管理**：Redux Toolkit，使用 RTK Query 處理 API 呼叫
- **路由**：Next.js 基於檔案系統的路由，配合 `_middleware.ts` 進行角色路由守衛
- **認證**：OAuth2 / OpenID Connect + JWT（HttpOnly Cookie）
- **API 客戶端**：OpenAPI 產生的 TypeScript 客戶端 (`@openapi-generator-cli`)

## 2. 主要 UI 模組與對應角色
| 角色 | 功能頁面 | 主要元件 |
|------|----------|----------|
| 照護人員 | 住民列表、每日摘要、事件時間軸、提醒清單、高風險警示、記憶修正 | `ResidentList`, `DailySummary`, `EventTimeline`, `ReminderList`, `RiskAlert`, `MemoryEditor` |
| 家屬 | 授權住民概覽、近期摘要、提醒狀態、事件通知、授權管理 | `FamilyDashboard`, `RecentSummary`, `ReminderStatus`, `NotificationCenter`, `ConsentManagement` |
| 系統管理者 | 使用者與角色管理、資產設定、稽核日誌、風險政策編輯、基準測試報告 | `AdminUserManagement`, `RoleEditor`, `AssetRegistry`, `AuditLogViewer`, `PolicyEditor`, `BenchmarkReport` |

## 3. 路由與權限（Next.js）
```
/pages
 ├─ /caregiver            // 照護人員入口
 │    ├─ index.tsx        // 住民列表
 │    ├─ summary.tsx
 │    └─ alerts.tsx
 ├─ /family               // 家屬入口
 │    ├─ index.tsx
 │    └─ notifications.tsx
 ├─ /admin                // 系統管理者入口
 │    ├─ users.tsx
 │    ├─ assets.tsx
 │    └─ policies.tsx
 └─ _middleware.ts        // 依 JWT 判斷 role，阻止未授權存取
```

## 4. UI 版面設計
- **全局 Layout**：`AppBar`（顯示使用者名稱、角色切換、登出） + `Drawer`（左側導航） + `Content`（主要區域）
- **響應式**：MUI Grid + CSS Flexbox，手機端抽屜收合，桌面端固定側邊欄。
- **資料卡**：使用 MUI Card，顯示事件摘要、時間、來源、信心分數。卡片右上角顯示 `source_event_ids` 供追溯。
- **高風險警示**：紅底白字樣式，點擊展開 GuardEvent 詳情。

## 5. 安全與隱私考量
1. 前端不持有機密資產，所有機密操作透過後端工具閘道完成。
2. 角色與住民 ID 均由 JWT 驗證，避免跨住民資料洩漏。
3. 表單前端驗證（Yup + Formik）配合後端 `F11` 正規化。
4. 從後端返回文字已經過 `F12` 輸出守衛，前端僅顯示 `redacted`／`blocked` 標記。

## 6. 測試策略
- **單元測試**：Jest + React Testing Library，覆蓋元件渲染與互動。
- **端到端測試**：Playwright（`webapp-testing` skill），模擬不同角色登入、資料檢視、警示觸發。
- **安全測試**：CI 中執行 `F15` 基準測試腳本，驗證攻擊分類、風險評分與防禦不回退。

## 7. 部署與 CI/CD
- **容器化**：Dockerfile 基於 `node:20-alpine`，支援 `next export`（靜態）與 SSR（Node）兩種模式。
- **CI**：GitHub Actions
  ```yaml
  steps:
    - name: Install
      run: npm ci
    - name: Lint
      run: npm run lint
    - name: Test
      run: npm run test
    - name: Build & Docker
      run: |
        docker build -t smart-care-ui .
        docker push <registry>/smart-care-ui
    - name: Deploy
      run: kubectl rollout restart deployment/smart-care-ui
  ```
- **環境變數**：`.env.production`、`.env.development`，機密透過 GitHub Secrets 注入容器。

## 8. 交付物
- 完整的 React 前端程式碼（src/、pages/、components/）
- Dockerfile、docker-compose.yml
- CI 工作流程檔案
- 測試報告（Jest、Playwright、F15 基準測試 JSON）

---

**此規格文件已完成，請審閱。如需調整，請告訴我具體修改項目。若無異議，請批准以進入實作階段。**