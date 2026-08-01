# Hackathon For Race - 智慧長照系統

> 企業級多租戶智慧照護 Agent 系統 v2.0  
> 整合 AWS Bedrock Claude 4.5 Sonnet、多層次安全防護、AI Workspace 隔離

---

## 📋 目錄

- [專案概述](#專案概述)
- [核心特色](#核心特色)
- [系統架構](#系統架構)
- [快速開始](#快速開始)
- [資料庫設定](#資料庫設定)
- [文件索引](#文件索引)
- [開發指南](#開發指南)
- [測試與驗證](#測試與驗證)

---

## 專案概述

**智慧長照系統**是一個為長者照護設計的 AI Agent 系統，結合語音互動、照護事件追蹤、家屬通知、多層次安全防護等功能。

### 技術棧

- **後端**: Python 3.14, Prisma ORM
- **資料庫**: MySQL 8.0
- **AI 模型**: AWS Bedrock Claude Sonnet 4.5
- **語音**: Whisper (faster-whisper)
- **前端**: TypeScript, Node.js

### 專案統計

- **資料表**: 25 個（核心 17 + 新增 8）
- **功能模組**: 15 個（完整文檔）
- **Enum 型別**: 18 個（型別安全）
- **外鍵約束**: 36 個（資料完整性）
- **程式碼**: 3,160+ 行（含文檔）

---

## 核心特色

### ✅ v2.0 架構升級

- **多租戶隔離** - 基於 Organization 的完整租戶模型
- **細粒度權限** - 4 種帳號類型 + 6 種機構角色 + 12 個家屬權限
- **AI Workspace 分離** - 候選資料與正式資料完全隔離
- **型別安全** - 18 個 Enum 型別取代字串
- **完整稽核** - 所有操作可追溯

### 🔐 安全防護（15 層）

1. 隱私防護閘道 - PII 偵測與遮蔽
2. 輸入正規化 - 防 Prompt Injection
3. 工具閘道 - 角色權限白名單
4. 攻擊分類 - 20 種攻擊偵測
5. 風險評分 - 動態政策引擎
6. 輸出守衛 - 資料洩漏驗證
7. Token 守衛 - 敏感資料保護
8. 稽核日誌 - 完整追蹤

### 🤖 AI 功能

- **語音互動** - Whisper 語音轉文字 + TTS 回覆
- **長期記憶** - 版本控制的偏好管理
- **照護事件** - 自動辨識與記錄
- **每日摘要** - AI 生成照護報告
- **智慧提醒** - 循環提醒與風險評估

---

## 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                 智慧長照系統架構 v2.0                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐      │
│  │   長者     │   │   家屬     │   │ 機構人員   │      │
│  │  (ELDER)   │   │ (GUARDIAN) │   │  (MEMBER)  │      │
│  └─────┬──────┘   └─────┬──────┘   └─────┬──────┘      │
│        │                 │                 │             │
│        └─────────────────┼─────────────────┘             │
│                          │                               │
│                ┌─────────▼──────────┐                    │
│                │  授權 Middleware   │                    │
│                │  • Session 驗證    │                    │
│                │  • 組織範圍        │                    │
│                │  • 長者權限        │                    │
│                │  • 操作權限        │                    │
│                └─────────┬──────────┘                    │
│                          │                               │
│        ┌─────────────────┼─────────────────┐             │
│        │                 │                 │             │
│  ┌─────▼──────┐   ┌──────▼──────┐   ┌────▼─────┐       │
│  │ Core       │   │ AI          │   │ Tool     │       │
│  │ Database   │   │ Workspace   │   │ Gateway  │       │
│  │            │   │             │   │          │       │
│  │ • 正式資料 │◄──┤ • 候選記憶 │──►│ • 權限   │       │
│  │ • 照護事件 │   │ • 摘要草稿 │   │ • 風險   │       │
│  │ • 提醒     │   │ • 工具執行 │   │ • 確認   │       │
│  │ • 警示     │   │ • 確認請求 │   │ • 稽核   │       │
│  └────────────┘   └─────────────┘   └──────────┘       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 資料隔離架構

```
Core Database (正式資料)         AI Workspace (草稿)
├── organizations                ├── ai_memory_candidates
├── organization_members         ├── ai_summary_drafts
├── organization_personas        ├── tool_executions (橋接)
├── guardian_relationships       └── confirmation_requests (橋接)
├── app_users
├── personas                     AI 只能:
├── persona_preferences          ✅ 建立候選記憶
├── care_events                  ✅ 生成摘要草稿
├── reminders                    ✅ 提出工具操作
├── care_alerts                  ❌ 不可直接修改正式資料
├── daily_summaries              ❌ 不可自行核准
├── audit_logs                   ❌ 不可讀取密碼/Token
└── auth_sessions
```

---

## 快速開始

### 前置需求

- **Node.js** 16.x 或以上
- **Python** 3.10 或以上
- **MySQL** 8.0 或以上
- **npm** / **pip**

### 1. Clone 專案

```bash
git clone https://github.com/Edwin-Tu/Hackathon-For-Race.git
cd Hackathon-For-Race
```

### 2. 安裝依賴

```bash
# Node.js 依賴
npm install

# Python 依賴
pip install -r requirements.txt
```

### 3. 設定環境變數

複製 `.env.example` 並修改為 `.env`：

```bash
# 資料庫連線
DATABASE_URL="mysql://smart_care_app:YOUR_PASSWORD@localhost:3306/smart_care_agent"

# AWS Bedrock
AWS_DEFAULT_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_SESSION_TOKEN=your_session_token
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### 4. 資料庫設定（重要！）

#### 方式 A: 使用互動式腳本（推薦）

```powershell
# 執行互動式同步腳本
.\sync_prisma_mysql.ps1

# 腳本會引導你：
# 1. 選擇同步模式（Migration / Push）
# 2. 自動備份資料庫
# 3. 執行同步
# 4. 驗證結果
```

#### 方式 B: 手動執行（開發環境）

```bash
# 快速同步（Push 模式）
npx prisma db push

# 生成 Prisma Client
npx prisma generate
```

#### 方式 C: 手動執行（生產環境）

```bash
# 1. 備份資料庫
mysqldump -u root -p smart_care_agent > backup.sql

# 2. 執行 Migration
npx prisma migrate dev --name multi_tenant_v2

# 3. 生成 Prisma Client
npx prisma generate

# 4. 驗證結果
python check_and_update_permissions.py
```

### 5. 驗證安裝

```bash
# 檢查資料庫結構
python describe_tables.py

# 檢查資料庫連線
python test_mysql_detailed.py

# 開啟 Prisma Studio（視覺化管理）
npx prisma studio
```

### 6. 測試 AWS Bedrock 連線

```bash
# 測試 Bedrock 基本推論
python main.py
```

---

## 資料庫設定

### 資料庫架構 v2.0

**25 個資料表**，分為 4 大類：

#### 1. Core Database（正式業務資料）- 17 個表

- **租戶管理** (4 個)
  - `organizations` - 長照機構
  - `organization_members` - 機構成員
  - `organization_personas` - 機構-長者關係
  - `guardian_relationships` - 家屬監護關係

- **身分認證** (2 個)
  - `app_users` - 使用者帳號
  - `auth_sessions` - 登入會話

- **核心業務** (8 個)
  - `personas` - 長者主體
  - `sessions` - 工作階段
  - `interactions` - 互動記錄
  - `persona_preferences` - 偏好記憶
  - `care_events` - 照護事件
  - `reminders` - 提醒排程
  - `care_alerts` - 照護警示
  - `daily_summaries` - 每日摘要

- **權限與稽核** (3 個)
  - `user_persona_access` - 細粒度權限
  - `audit_logs` - 稽核日誌
  - `event_revisions` - 事件修訂

#### 2. AI Workspace（AI 可管理）- 4 個表

- `service_principals` - 系統服務身分
- `service_permissions` - 服務權限
- `ai_memory_candidates` - AI 候選記憶
- `ai_summary_drafts` - AI 摘要草稿

#### 3. 橋接表（AI 與正式系統）- 2 個表

- `tool_executions` - 工具執行記錄
- `confirmation_requests` - 確認請求

#### 4. 系統表 - 2 個表

- `_prisma_migrations` - Migration 歷史
- `daily_summary_events` - 摘要事件關聯

### 資料庫帳號

系統使用 3 種資料庫帳號：

| 帳號 | 用途 | 權限 |
|------|------|------|
| `smart_care_migration` | 部署與 Migration | DDL + DML |
| `smart_care_app` | 後端應用程式 | DML (CRUD) |
| `smart_care_ai` | AI Agent（不建議直連）| 受限 DML |

### 建立資料庫帳號（首次設定）

```bash
# 執行帳號建立腳本
mysql -u root -p < database/setup_users.sql

# 或更新現有帳號權限
mysql -u root -p < database/update_existing_user_grants.sql
```

---

## 文件索引

### 📚 核心文檔

| 文件 | 說明 | 路徑 |
|------|------|------|
| **快速開始指南** ⭐ | 5 分鐘上手教學 | `docs/快速開始指南_v2.0.md` |
| **Prisma 同步指南** ⭐ | 資料庫連線與同步 | `PRISMA_MYSQL_SYNC_GUIDE.md` |
| **Migration 指南** | 資料庫升級步驟 | `MIGRATION_GUIDE.md` |
| **權限矩陣** | 完整權限規則 | `docs/權限矩陣與資料存取控制.md` |
| **架構總結** | v2.0 變更報告 | `docs/架構重構總結報告_v2.0.md` |
| **資料表說明** | 詳細欄位說明 | `docs/資料表欄位詳細討論.md` |
| **WorkRecord** | 專案工作記錄 | `WorkRecord_20260801.md` |

### 📖 功能模組文檔（15 個）

| 模組 | 文件 | 權重 |
|------|------|------|
| F01 - 隱私防護閘道 | `docs/01-隱私防護閘道.md` | 100 |
| F02 - 語音輸入與轉錄 | `docs/02-語音輸入與轉錄.md` | 80 |
| F03 - 對話控制與工具呼叫 | `docs/03-對話控制與工具呼叫.md` | 90 |
| F04 - 本地工具閘道 | `docs/04-本地工具閘道.md` | 95 |
| F05 - 照護資料持久化與長期記憶 | `docs/05-照護資料持久化與長期記憶.md` | 90 |
| F06 - 提醒排程與輸出事件 | `docs/06-提醒排程與輸出事件.md` | 70 |
| F07 - 身份驗證與角色授權 | `docs/07-身份驗證與角色授權.md` | 80 |
| F08 - 照護者儀表板 | `docs/08-照護者儀表板.md` | 75 |
| F09 - 攻擊分類與防禦技能 | `docs/09-攻擊分類與防禦技能.md` | 90 |
| F10 - 風險評分與政策引擎 | `docs/10-風險評分與政策引擎.md` | 85 |
| F11 - 輸入正規化與保護提示詞 | `docs/11-輸入正規化與保護提示詞.md` | 70 |
| F12 - 輸出守衛與洩漏驗證 | `docs/12-輸出守衛與洩漏驗證.md` | 75 |
| F13 - 資產註冊與Token守衛 | `docs/13-資產註冊與Token守衛.md` | 75 |
| F14 - LLM閘道與事件稽核 | `docs/14-LLM閘道與事件稽核.md` | 80 |
| F15 - 基準測試與驗證 | `docs/15-基準測試與驗證.md` | 65 |

---

## 開發指南

### 專案結構

```
Hackathon-For-Race/
├── backend/
│   └── middleware/
│       └── authorization.ts      # 授權 Middleware
├── database/
│   ├── setup_users.sql           # 資料庫帳號設置
│   └── update_existing_user_grants.sql
├── docs/                         # 完整文檔
│   ├── 快速開始指南_v2.0.md
│   ├── 權限矩陣與資料存取控制.md
│   ├── 架構重構總結報告_v2.0.md
│   ├── 資料表欄位詳細討論.md
│   └── 01-15 功能模組.md
├── prisma/
│   ├── schema.prisma             # Prisma Schema (930 行)
│   └── migrations/               # Migration 歷史
├── tests/
│   └── test_prisma_setup.py
├── bedrock_client.py             # AWS Bedrock 客戶端
├── main.py                       # Bedrock 測試
├── prisma_client.py              # Prisma 客戶端
├── check_and_update_permissions.py  # 權限檢查工具
├── describe_tables.py            # 資料表說明工具
├── sync_prisma_mysql.ps1         # 互動式同步腳本
├── .env                          # 環境變數（不進版控）
├── .env.example                  # 環境變數範例
├── package.json                  # Node.js 配置
├── requirements.txt              # Python 依賴
└── README.md                     # 本文件
```

### 開發工作流

#### 1. 建立新功能

```bash
# 1. 建立分支
git checkout -b feature/your-feature

# 2. 修改 Schema（如需要）
code prisma/schema.prisma

# 3. 同步資料庫
npx prisma db push

# 4. 開發功能
# ...

# 5. 測試
python tests/test_your_feature.py

# 6. 提交
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

#### 2. 修改資料表結構

```bash
# 1. 修改 Schema
code prisma/schema.prisma

# 2. 建立 Migration
npx prisma migrate dev --name your_migration_name

# 3. 生成 Client
npx prisma generate

# 4. 更新程式碼
# ...
```

#### 3. 使用 Prisma Client

```typescript
// TypeScript / JavaScript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// 查詢長者
const personas = await prisma.persona.findMany({
  where: {
    status: 'ACTIVE',
    primaryOrganizationId: organizationId,
  },
  include: {
    organizationRelations: true,
    guardianRelationships: true,
  },
});
```

```python
# Python
from prisma import Prisma

prisma = Prisma()
await prisma.connect()

# 查詢長者
personas = await prisma.persona.find_many(
    where={
        'status': 'ACTIVE',
        'primaryOrganizationId': organization_id,
    },
    include={
        'organizationRelations': True,
        'guardianRelationships': True,
    },
)

await prisma.disconnect()
```

---

## 測試與驗證

### 執行測試

```bash
# MySQL 連線測試
python test_mysql_connection.py
python test_mysql_detailed.py

# Prisma 設置測試
python tests/test_prisma_setup.py

# 資料庫狀態檢查
python check_and_update_permissions.py

# 資料表說明
python describe_tables.py

# Bedrock 連線測試
python main.py
```

### 視覺化管理

```bash
# 啟動 Prisma Studio
npx prisma studio

# 瀏覽器自動開啟 http://localhost:5555
# 可視覺化管理所有資料表
```

### 檢查清單

- [ ] 資料庫連線成功
- [ ] 25 個資料表已建立
- [ ] Prisma Client 已生成
- [ ] 權限檢查通過
- [ ] Bedrock 連線成功
- [ ] 測試資料可建立

---

## 常見問題

### Q1: 如何重置資料庫？

```bash
# ⚠️ 警告：會刪除所有資料！
npx prisma migrate reset

# 或手動
mysql -u root -p -e "DROP DATABASE smart_care_agent; CREATE DATABASE smart_care_agent;"
npx prisma migrate deploy
```

### Q2: Migration 失敗怎麼辦？

```bash
# 1. 查看狀態
npx prisma migrate status

# 2. 使用備份還原
mysql -u root -p smart_care_agent < backup.sql

# 3. 標記為已解決
npx prisma migrate resolve --rolled-back [migration_name]
```

### Q3: Prisma Client 型別不正確？

```bash
# 重新生成 Client
npx prisma generate

# 重啟 TypeScript Server (VSCode)
# Ctrl+Shift+P → "TypeScript: Restart TS Server"
```

### Q4: 如何查看所有 Migration 歷史？

```bash
# 查看 Migration 狀態
npx prisma migrate status

# 查看 Migration 資料夾
ls prisma/migrations/

# 查看特定 Migration SQL
cat prisma/migrations/[migration_folder]/migration.sql
```

---

## 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

---

## 授權

本專案使用 MIT 授權 - 詳見 LICENSE 檔案

---

## 聯絡資訊

- **GitHub**: https://github.com/Edwin-Tu/Hackathon-For-Race
- **專案路徑**: `C:\Users\hc105\Hackathon-For-Race`

---

## 版本歷史

### v2.0 (2026-08-01)
- ✅ 多租戶架構重構
- ✅ 新增 8 個資料表
- ✅ 18 個 Enum 型別
- ✅ AI Workspace 分離
- ✅ 細粒度權限控制
- ✅ 完整文檔（3,160+ 行）

### v1.0 (2026-08-01)
- ✅ 基礎架構建立
- ✅ AWS Bedrock 整合
- ✅ 15 個功能模組
- ✅ MySQL + Prisma ORM

---

**專案版本**: v2.0  
**最後更新**: 2026-08-01  
**狀態**: ✅ 可部署
