# 智護聲盾 (Smart Care Shield)

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-blue?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Prisma](https://img.shields.io/badge/Prisma-6.19-2D3748?logo=prisma)](https://www.prisma.io/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange?logo=amazon-aws)](https://aws.amazon.com/bedrock/)

> 企業級多租戶智慧長照管理系統 v2.0

AI 驅動的智慧照護平台，整合 AWS Bedrock Claude 4.5 Sonnet，提供照護人員管理、家屬遠端監控、系統管理等功能，具備完整的安全防護機制。

## ✨ 核心特色

- 🏥 **照護人員介面** - 住民管理、每日摘要、警示追蹤
- 👨‍👩‍👧 **家屬遠端監控** - 儀表板、通知、授權管理
- 🔧 **系統管理功能** - 使用者管理、角色權限、稽核日誌
- 🤖 **AI 功能** - 語音互動、長期記憶、智慧提醒
- 🔒 **15 層安全防護** - 從輸入到輸出的完整防護鏈
- 🏢 **多租戶架構** - Organization-based 完整隔離
- 📊 **混合資料庫** - RDS MySQL + DynamoDB

## 🚀 快速開始

### 前置要求

- Node.js >= 20.0.0
- NPM >= 10.0.0
- MySQL 8.0+ (或使用 AWS RDS)
- Python 3.10+ (用於工具腳本)

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/Edwin-Tu/Hackathon-For-Race.git
cd Hackathon-For-Race

# 2. 安裝依賴
npm install

# 3. 配置環境變數
cp .env.example .env
# 編輯 .env 填入實際配置

# 4. 生成 Prisma Client
npm run prisma:generate

# 5. 執行資料庫遷移（如需要）
npm run prisma:migrate

# 6. 啟動開發伺服器
npm run dev
```

開啟 [http://localhost:3000](http://localhost:3000) 查看應用程式。

### 使用 Docker

```bash
# 開發環境（包含 MySQL, Redis, Prisma Studio）
docker-compose up -d

# 或建置生產映像
docker build -t smart-care-app .
docker run -p 3000:3000 smart-care-app
```

### 使用 Makefile

```bash
# 查看所有可用命令
make help

# 一鍵設定專案
make setup

# 啟動開發
make dev

# 執行 CI 檢查
make ci
```

## 📁 專案結構

```
Hackathon-For-Race/
├── .github/              # GitHub Actions CI/CD
├── config/               # 配置文件（JSON）
├── docs/                 # 完整文檔
│   ├── WorkRecord/       # 工作記錄
│   └── superpowers/      # 設計規格
├── prisma/               # Prisma ORM Schema
├── src/                  # 前端原始碼
│   ├── components/       # React 元件
│   ├── pages/            # Next.js 頁面（27個）
│   ├── hooks/            # 自定義 Hooks
│   ├── store/            # Redux 狀態管理
│   ├── types/            # TypeScript 型別
│   └── utils/            # 工具函數
├── backend/              # 後端中介軟體
├── database/             # SQL 腳本
├── scripts/              # Python 部署腳本
├── tools/                # 開發工具
│   ├── python/           # Python 工具
│   └── scripts/          # Shell 腳本
├── tests/                # 測試檔案
├── e2e/                  # E2E 測試
├── infra/                # AWS SAM 基礎設施
├── k8s/                  # Kubernetes 配置
├── lambda/               # AWS Lambda 函數
└── public/               # 靜態資源
```

## 🛠️ 技術棧

### 前端

- **框架**: Next.js 16.2 (React 19.2)
- **語言**: TypeScript 5.9
- **狀態管理**: Redux Toolkit + RTK Query
- **UI 框架**: Material-UI 9.2
- **樣式**: Emotion (CSS-in-JS)
- **測試**: Jest + React Testing Library + Playwright

### 後端

- **語言**: Python 3.14, TypeScript
- **ORM**: Prisma 6.19
- **資料庫**: 
  - Amazon RDS MySQL 8.0.46
  - Amazon DynamoDB
- **認證**: JWT (HttpOnly Cookie)

### 雲端與 AI

- **平台**: AWS (us-west-2)
- **AI 模型**: Amazon Bedrock Claude Sonnet 4.5
- **語音**: Whisper (faster-whisper)
- **儲存**: Amazon S3 (計畫中)

### DevOps

- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **編排**: Kubernetes
- **基礎設施**: AWS SAM

## 📚 文檔

| 文檔 | 說明 |
|------|------|
| [安裝指南](INSTALLATION.md) | 詳細的安裝步驟與故障排除 |
| [專案狀態](docs/PROJECT_STATUS.md) | 目前進度與待辦事項 |
| [技術文檔](docs/TECHNICAL_DOCUMENTATION.md) | 完整技術架構（1,702行） |
| [任務總結](docs/TASK_COMPLETION_SUMMARY.md) | 已完成功能清單 |
| [資料庫參考](docs/DATABASE_CONNECTION_QUICK_REFERENCE.md) | 快速連線指南 |
| [工作記錄](docs/WorkRecord/) | 開發過程記錄 |

### 功能模組文檔（15個）

完整的安全防護模組文檔：

- [F01: 隱私防護閘道](docs/01-隱私防護閘道.md)
- [F02: 語音輸入與轉錄](docs/02-語音輸入與轉錄.md)
- [F03: 對話控制與工具呼叫](docs/03-對話控制與工具呼叫.md)
- ... 共 15 個模組

## 🗄️ 資料庫架構

### RDS MySQL (17 張表)

- **租戶管理**: organizations, organization_members
- **身分認證**: app_users, auth_sessions
- **核心業務**: personas, sessions, interactions, care_events
- **權限稽核**: user_persona_access, audit_logs

### DynamoDB (4 張表)

- smart_care_residents
- smart_care_events
- smart_care_users
- smart_care_audit_log

詳見 [Prisma Schema](prisma/schema.prisma)

## 🧪 測試

```bash
# 執行測試
npm test

# 監看模式
npm run test:watch

# 覆蓋率報告
npm run test:ci

# 型別檢查
npm run type-check

# Lint 檢查
npm run lint
```

## 🔧 開發命令

```bash
# 開發
npm run dev                    # 啟動開發伺服器
npm run build                  # 建置生產版本
npm run start                  # 啟動生產伺服器

# 程式碼品質
npm run lint                   # ESLint 檢查
npm run lint:fix               # 自動修正錯誤
npm run format                 # Prettier 格式化
npm run type-check             # TypeScript 檢查

# 資料庫
npm run prisma:generate        # 生成 Prisma Client
npm run prisma:migrate         # 執行遷移
npm run prisma:studio          # 開啟 Prisma Studio
npm run db:push                # 推送 Schema

# Docker
make docker-up                 # 啟動容器
make docker-down               # 停止容器
make docker-logs               # 查看日誌
```

## 🏗️ 資料庫遷移

```bash
# 開發環境
npm run prisma:migrate

# 生產環境
npm run prisma:migrate:deploy

# 重置資料庫（危險！）
npm run prisma:reset
```

## 🚢 部署

### Vercel（推薦）

```bash
npm install -g vercel
vercel
```

### Docker

```bash
docker build -t smart-care-app .
docker run -p 3000:3000 smart-care-app
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

### AWS SAM

```bash
sam build
sam deploy --guided
```

## 🔒 環境變數

複製 `.env.example` 為 `.env` 並填入以下配置：

```bash
# 應用程式
NODE_ENV=development
PORT=3000

# 資料庫
DATABASE_URL="mysql://user:pass@host:3306/db"

# AWS
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Bedrock AI
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-...

# JWT
JWT_SECRET=your-secret-key
```

詳見 [.env.example](.env.example)

## 🤝 貢獻指南

我們歡迎貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 程式碼規範

- 遵循 ESLint 和 Prettier 規則
- TypeScript 嚴格模式
- 測試覆蓋率 >= 50%
- Commit 訊息使用 Conventional Commits

## 📊 專案狀態

- **整體完成度**: 75%
- **前端架構**: 80%
- **後端 API**: 60%
- **資料庫**: 100%
- **測試覆蓋**: 20%
- **文檔**: 90%

詳見 [PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

## 🐛 問題回報

發現 Bug？請到 [Issues](https://github.com/Edwin-Tu/Hackathon-For-Race/issues) 回報。

## 📄 授權

ISC License

## 👥 團隊

- Edwin Tu - [@Edwin-Tu](https://github.com/Edwin-Tu)
- Bryan
- Hao

## 🙏 致謝

- AWS Bedrock Team
- Prisma Team
- Next.js Team
- Material-UI Team

## 📞 聯絡方式

- GitHub: https://github.com/Edwin-Tu/Hackathon-For-Race
- Issues: https://github.com/Edwin-Tu/Hackathon-For-Race/issues

---

**版本**: 2.0.0  
**最後更新**: 2026-08-01  
**狀態**: 🟢 積極開發中
