# 專案結構說明

此文件提供 Hackathon-For-Race 專案的完整結構說明。

## 📁 根目錄結構

```
Hackathon-For-Race/
├── .github/                    # GitHub 配置
│   └── workflows/              # GitHub Actions CI/CD
├── .husky/                     # Git Hooks (Husky)
├── .next/                      # Next.js 建置輸出（gitignored）
├── node_modules/               # NPM 依賴（gitignored）
├── public/                     # 靜態資源
│   ├── images/                 # 圖片資源
│   └── fonts/                  # 字體檔案
├── src/                        # 前端原始碼 ⭐
├── backend/                    # 後端程式碼
├── database/                   # 資料庫腳本
├── prisma/                     # Prisma ORM
├── scripts/                    # Python 部署腳本
├── tools/                      # 開發工具 ⭐
│   ├── python/                 # Python 工具
│   └── scripts/                # Shell 腳本
├── tests/                      # Python 測試
├── e2e/                        # E2E 測試 (Playwright)
├── infra/                      # AWS SAM 基礎設施
├── k8s/                        # Kubernetes 部署配置
├── lambda/                     # AWS Lambda 函數
├── docs/                       # 文檔 ⭐
│   ├── WorkRecord/             # 工作記錄
│   ├── superpowers/            # 設計規格
│   └── temp/                   # 臨時文件
├── config/                     # 配置文件 ⭐
├── recovery/                   # 備份檔案
└── [配置檔案]                  # 各種配置檔案

⭐ = 最近優化/新增的目錄
```

## 📂 詳細目錄說明

### 1. 前端目錄 (`src/`)

```
src/
├── components/          # React 元件
│   ├── common/          # 通用元件
│   ├── layout/          # 版面元件
│   └── [功能元件]
├── pages/               # Next.js 頁面路由
│   ├── admin/           # 管理員頁面
│   ├── caregiver/       # 照護人員頁面
│   ├── family/          # 家屬頁面
│   ├── api/             # API 路由
│   └── [...].tsx        # 其他頁面
├── hooks/               # 自定義 React Hooks
├── store/               # Redux 狀態管理
│   ├── slices/          # Redux Slices
│   └── store.ts         # Store 配置
├── types/               # TypeScript 型別定義
├── utils/               # 工具函數
├── theme/               # MUI 主題配置
├── context/             # React Context
├── layout/              # 版面組件
├── middleware.ts        # Next.js Middleware
└── __tests__/           # 測試檔案
```

### 2. 後端目錄 (`backend/`)

```
backend/
└── middleware/
    └── authorization.ts    # 授權中介軟體（680行）
```

### 3. 資料庫目錄 (`prisma/`)

```
prisma/
├── schema.prisma           # 資料庫 Schema（930行）
├── schema.prisma.backup_*  # Schema 備份
└── migrations/             # 資料庫遷移歷史
    └── [timestamp]_[name]/
        └── migration.sql
```

### 4. 工具目錄 (`tools/`)

```
tools/
├── python/                         # Python 工具
│   ├── bedrock_client.py           # AWS Bedrock 客戶端
│   ├── prisma_client.py            # Prisma Python 客戶端
│   ├── main.py                     # Bedrock 測試
│   ├── test_mysql_connection.py    # MySQL 連線測試
│   ├── test_mysql_detailed.py      # MySQL 詳細測試
│   ├── check_and_update_permissions.py  # 權限工具
│   ├── describe_tables.py          # 資料表描述
│   ├── requirements.txt            # Python 依賴
│   └── README.md
├── scripts/                        # Shell/PowerShell 腳本
│   ├── sync_prisma_mysql.ps1       # Prisma 同步工具
│   └── README.md
└── README.md
```

### 5. Python 腳本目錄 (`scripts/`)

```
scripts/
├── deploy_rds_mysql.py        # RDS MySQL 部署
├── deploy_dynamodb.py         # DynamoDB 部署
├── deploy_rds_and_sync.py     # RDS 部署與同步
├── test_rds_connection.py     # RDS 連線測試
└── dynamodb_example.py        # DynamoDB 使用範例
```

### 6. 配置目錄 (`config/`)

```
config/
├── dynamodb_connection_info.json    # DynamoDB 連線資訊
├── rds_connection_info.json         # RDS 連線資訊
├── rds_verification_report.json     # RDS 驗證報告
├── opencode.json                    # OpenCode AI 配置
└── README.md
```

### 7. 文檔目錄 (`docs/`)

```
docs/
├── WorkRecord/                              # 工作記錄
│   ├── 2026-08-01-database-remote-deployment.md
│   ├── 2026-08-01-214034-project-integration-report.md
│   ├── 2026-08-01-215646-directory-integration.md
│   ├── 2026-08-01-220600-project-optimization.md
│   └── 2026-08-01-222038-installation-fixes.md
├── superpowers/                             # 設計規格
│   ├── [設計文檔].md
│   └── [實作計畫].md
├── temp/                                    # 臨時文件
│   ├── aws-inventory-20260801-202155.txt
│   ├── table_descriptions.txt
│   └── [備份檔案]
├── 01-15 功能模組文檔/                      # 15 個安全模組
├── PROJECT_STATUS.md                        # 專案狀態
├── TECHNICAL_DOCUMENTATION.md               # 技術文檔
├── TASK_COMPLETION_SUMMARY.md               # 任務總結
├── DATABASE_CONNECTION_QUICK_REFERENCE.md   # 資料庫參考
└── [其他文檔]
```

### 8. DevOps 目錄

#### `.github/`
```
.github/
└── workflows/
    └── ci-cd.yml              # CI/CD Pipeline（5 階段）
```

#### `infra/`
```
infra/
└── [AWS SAM 模板]             # Serverless 基礎設施
```

#### `k8s/`
```
k8s/
└── [Kubernetes YAML]           # K8s 部署配置
```

#### `lambda/`
```
lambda/
└── [Lambda 函數]               # AWS Lambda 程式碼
```

### 9. 測試目錄

#### `tests/` (Python)
```
tests/
└── test_prisma_setup.py        # Prisma 設定測試
```

#### `e2e/` (Playwright)
```
e2e/
└── [E2E 測試腳本]              # 端到端測試
```

#### `src/__tests__/` (Jest)
```
src/__tests__/
└── [單元測試]                  # Jest 單元測試
```

## 📄 根目錄配置檔案

### 開發配置

| 檔案 | 說明 |
|------|------|
| `package.json` | NPM 專案配置 |
| `package-lock.json` | NPM 鎖定版本 |
| `tsconfig.json` | TypeScript 配置 |
| `next.config.ts` | Next.js 配置 |
| `eslint.config.mjs` | ESLint 9 配置 |
| `.prettierrc` | Prettier 配置 |
| `jest.config.js` | Jest 測試配置 |
| `jest.setup.js` | Jest 設定檔 |

### 環境配置

| 檔案 | 說明 |
|------|------|
| `.env` | 環境變數（gitignored） |
| `.env.example` | 環境變數範本 |

### Docker 配置

| 檔案 | 說明 |
|------|------|
| `Dockerfile` | Docker 映像定義 |
| `.dockerignore` | Docker 忽略規則 |
| `docker-compose.yml` | Docker Compose 配置 |

### Git 配置

| 檔案 | 說明 |
|------|------|
| `.gitignore` | Git 忽略規則 |
| `.editorconfig` | 編輯器配置 |

### 其他配置

| 檔案 | 說明 |
|------|------|
| `Makefile` | Make 命令集合 |
| `README.md` | 專案說明 |
| `INSTALLATION.md` | 安裝指南 |

## 🗂️ 檔案組織原則

### 已移動的檔案

| 原位置 | 新位置 | 原因 |
|--------|--------|------|
| `/*.py` | `tools/python/` | 整合 Python 工具 |
| `/*.ps1` | `tools/scripts/` | 整合 Shell 腳本 |
| `/*.json` (配置) | `config/` | 集中配置管理 |
| `/*.md` (文檔) | `docs/` | 整合文檔 |
| 臨時檔案 | `docs/temp/` | 歷史存檔 |

### 目錄用途

| 目錄 | 用途 | 內容類型 |
|------|------|---------|
| `src/` | 前端程式碼 | TypeScript, React, Next.js |
| `backend/` | 後端程式碼 | TypeScript, Middleware |
| `prisma/` | 資料庫 ORM | Schema, Migrations |
| `scripts/` | 部署腳本 | Python 部署自動化 |
| `tools/` | 開發工具 | Python, Shell 工具 |
| `tests/` | 測試 | Python, Jest, Playwright |
| `docs/` | 文檔 | Markdown 文檔 |
| `config/` | 配置 | JSON 配置檔 |
| `public/` | 靜態資源 | 圖片, 字體 |

## 🎯 最佳實踐

### 1. 命名規範

- **檔案**: kebab-case (例: `user-profile.tsx`)
- **元件**: PascalCase (例: `UserProfile.tsx`)
- **工具**: snake_case (例: `deploy_rds.py`)
- **目錄**: kebab-case 或 camelCase

### 2. 檔案位置

- ✅ 前端程式碼 → `src/`
- ✅ 工具腳本 → `tools/`
- ✅ 文檔 → `docs/`
- ✅ 配置 → `config/` 或根目錄
- ✅ 測試 → 對應的 `__tests__/` 或 `tests/`

### 3. 模組引用

```typescript
// 使用 Path Alias
import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';
import { UserType } from '@/types/user';
```

### 4. 文檔組織

- 技術文檔 → `docs/`
- 工作記錄 → `docs/WorkRecord/`
- 設計規格 → `docs/superpowers/`
- 臨時文件 → `docs/temp/`

## 🔗 相關資源

- [專案 README](../README.md)
- [安裝指南](../INSTALLATION.md)
- [技術文檔](TECHNICAL_DOCUMENTATION.md)
- [專案狀態](PROJECT_STATUS.md)

---

**最後更新**: 2026-08-01  
**版本**: 2.0  
**狀態**: ✅ 已優化
