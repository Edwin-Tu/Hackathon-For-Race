# Tools Directory

此目錄包含專案開發與維護相關的工具和腳本。

## 📁 目錄結構

```
tools/
├── python/          # Python 工具與腳本
└── scripts/         # Shell/PowerShell 腳本
```

## 🐍 Python Tools

位於 `tools/python/` 目錄：

| 檔案 | 說明 |
|------|------|
| `bedrock_client.py` | AWS Bedrock AI 客戶端 |
| `prisma_client.py` | Prisma Python 客戶端 |
| `main.py` | Bedrock 測試主程式 |
| `test_mysql_connection.py` | MySQL 連線測試 |
| `test_mysql_detailed.py` | MySQL 詳細測試 |
| `check_and_update_permissions.py` | 資料庫權限檢查工具 |
| `describe_tables.py` | 資料表結構描述工具 |
| `requirements.txt` | Python 依賴清單 |

### 使用方式

```bash
# 安裝 Python 依賴
cd tools/python
pip install -r requirements.txt

# 執行測試
python test_mysql_connection.py
python main.py
```

## 📜 Scripts

位於 `tools/scripts/` 目錄：

| 檔案 | 說明 |
|------|------|
| `sync_prisma_mysql.ps1` | Prisma Schema 同步工具（互動式） |

### 使用方式

```powershell
# PowerShell 腳本
.\tools\scripts\sync_prisma_mysql.ps1
```

## 📝 注意事項

- Python 工具需要 Python 3.10+ 環境
- PowerShell 腳本需要 PowerShell 5.1+ 或 PowerShell Core 7+
- 執行前請確保已配置 `.env` 環境變數
- 部分工具需要 AWS 憑證和資料庫連線資訊

## 🔗 相關文檔

- [資料庫部署指南](../docs/AWS_DATABASE_DEPLOYMENT_GUIDE.md)
- [技術文檔](../docs/TECHNICAL_DOCUMENTATION.md)
- [安裝指南](../INSTALLATION.md)
