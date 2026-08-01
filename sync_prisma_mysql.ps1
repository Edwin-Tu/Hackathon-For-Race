# Prisma 與 MySQL 同步腳本
# 互動式引導執行

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       Prisma Schema 與 MySQL 資料庫同步工具" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 檢查當前目錄
$currentDir = Get-Location
Write-Host "`n當前目錄: $currentDir" -ForegroundColor Yellow

if (-not (Test-Path "prisma\schema.prisma")) {
    Write-Host "❌ 錯誤: 找不到 prisma\schema.prisma" -ForegroundColor Red
    Write-Host "請確認在專案根目錄執行此腳本" -ForegroundColor Yellow
    exit 1
}

# 檢查 .env 檔案
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  警告: 找不到 .env 檔案" -ForegroundColor Yellow
    Write-Host "請確認 DATABASE_URL 環境變數已設定" -ForegroundColor Yellow
} else {
    Write-Host "✓ 找到 .env 檔案" -ForegroundColor Green
}

# 選擇同步方式
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "請選擇同步方式:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1] Migration 模式 (推薦 - 有版本控制)" -ForegroundColor Green
Write-Host "    • 適用: 生產環境、有現有資料"
Write-Host "    • 優點: 可回滾、有歷史記錄"
Write-Host "    • 缺點: 需要審查 SQL"
Write-Host ""
Write-Host "[2] Push 模式 (快速 - 直接同步)" -ForegroundColor Yellow
Write-Host "    • 適用: 開發環境、測試環境"
Write-Host "    • 優點: 快速簡單"
Write-Host "    • 缺點: 無法回滾"
Write-Host ""
Write-Host "[3] 檢查狀態 (查看當前資料庫狀態)" -ForegroundColor Cyan
Write-Host ""
Write-Host "[0] 取消" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "請輸入選項 (0-3)"

switch ($choice) {
    "1" {
        # Migration 模式
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "Migration 模式 - 步驟執行" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        
        # 步驟 1: 備份
        Write-Host "`n【步驟 1/5】備份資料庫" -ForegroundColor Yellow
        $backup = Read-Host "是否要備份現有資料庫? (y/n)"
        
        if ($backup -eq "y") {
            $backupFile = "backup_before_migration_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
            Write-Host "正在備份到: $backupFile" -ForegroundColor Cyan
            
            $dbName = "smart_care_agent"
            $username = "root"
            
            Write-Host "請輸入 MySQL root 密碼:" -ForegroundColor Yellow
            mysqldump -u $username -p $dbName > $backupFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ 備份完成: $backupFile" -ForegroundColor Green
            } else {
                Write-Host "✗ 備份失敗" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "⚠️  跳過備份（不建議）" -ForegroundColor Yellow
        }
        
        # 步驟 2: 驗證 Schema
        Write-Host "`n【步驟 2/5】驗證 Prisma Schema" -ForegroundColor Yellow
        npx prisma validate
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Schema 驗證失敗" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Schema 驗證通過" -ForegroundColor Green
        
        # 步驟 3: 建立 Migration
        Write-Host "`n【步驟 3/5】建立 Migration" -ForegroundColor Yellow
        $migrationName = Read-Host "請輸入 Migration 名稱 (預設: multi_tenant_v2)"
        
        if ([string]::IsNullOrWhiteSpace($migrationName)) {
            $migrationName = "multi_tenant_v2"
        }
        
        Write-Host "建立 Migration: $migrationName" -ForegroundColor Cyan
        npx prisma migrate dev --name $migrationName --create-only
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Migration 建立失敗" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Migration 已建立" -ForegroundColor Green
        
        # 步驟 4: 審查 SQL
        Write-Host "`n【步驟 4/5】審查 Migration SQL" -ForegroundColor Yellow
        $migrationFolder = Get-ChildItem -Path "prisma\migrations" | Where-Object { $_.Name -like "*$migrationName*" } | Select-Object -Last 1
        
        if ($migrationFolder) {
            $sqlFile = Join-Path $migrationFolder.FullName "migration.sql"
            Write-Host "Migration SQL 位置: $sqlFile" -ForegroundColor Cyan
            
            $viewSql = Read-Host "`n是否要查看 SQL 內容? (y/n)"
            if ($viewSql -eq "y") {
                Write-Host "`n--- Migration SQL ---" -ForegroundColor Cyan
                Get-Content $sqlFile | Write-Host -ForegroundColor Gray
                Write-Host "--- End of SQL ---`n" -ForegroundColor Cyan
            }
        }
        
        $confirm = Read-Host "`n確認要執行此 Migration? (y/n)"
        if ($confirm -ne "y") {
            Write-Host "已取消執行" -ForegroundColor Yellow
            exit 0
        }
        
        # 步驟 5: 執行 Migration
        Write-Host "`n【步驟 5/5】執行 Migration" -ForegroundColor Yellow
        npx prisma migrate deploy
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Migration 執行失敗" -ForegroundColor Red
            if ($backup -eq "y") {
                Write-Host "`n可使用以下命令還原:" -ForegroundColor Yellow
                Write-Host "  mysql -u root -p smart_care_agent < $backupFile" -ForegroundColor Cyan
            }
            exit 1
        }
        Write-Host "✓ Migration 執行成功" -ForegroundColor Green
        
        # 生成 Prisma Client
        Write-Host "`n生成 Prisma Client..." -ForegroundColor Yellow
        npx prisma generate
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Client 生成失敗" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Client 生成完成" -ForegroundColor Green
        
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "✓ Migration 完成！" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
    }
    
    "2" {
        # Push 模式
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "Push 模式 - 快速同步" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        
        Write-Host "`n⚠️  警告: Push 模式會直接修改資料庫，無法回滾！" -ForegroundColor Red
        Write-Host "建議先備份資料庫" -ForegroundColor Yellow
        
        $backup = Read-Host "`n是否要備份? (y/n)"
        if ($backup -eq "y") {
            $backupFile = "backup_before_push_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
            Write-Host "正在備份到: $backupFile" -ForegroundColor Cyan
            mysqldump -u root -p smart_care_agent > $backupFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ 備份完成" -ForegroundColor Green
            }
        }
        
        $confirm = Read-Host "`n確認要執行 Push? (y/n)"
        if ($confirm -ne "y") {
            Write-Host "已取消執行" -ForegroundColor Yellow
            exit 0
        }
        
        Write-Host "`n執行 Push..." -ForegroundColor Yellow
        npx prisma db push
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Push 失敗" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "✓ Push 完成！" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
    }
    
    "3" {
        # 檢查狀態
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "檢查資料庫狀態" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        
        Write-Host "`n【Prisma Migration 狀態】" -ForegroundColor Yellow
        npx prisma migrate status
        
        Write-Host "`n【Python 腳本檢查】" -ForegroundColor Yellow
        if (Test-Path "check_and_update_permissions.py") {
            python check_and_update_permissions.py
        } else {
            Write-Host "找不到 check_and_update_permissions.py" -ForegroundColor Red
        }
        
        Write-Host "`n【資料表清單】" -ForegroundColor Yellow
        if (Test-Path "describe_tables.py") {
            $showTables = Read-Host "是否要查看詳細資料表說明? (y/n)"
            if ($showTables -eq "y") {
                python describe_tables.py
            }
        }
    }
    
    "0" {
        Write-Host "`n已取消" -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "`n無效的選項" -ForegroundColor Red
        exit 1
    }
}

# 驗證結果
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "驗證同步結果" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$verify = Read-Host "`n是否要執行驗證腳本? (y/n)"
if ($verify -eq "y") {
    if (Test-Path "check_and_update_permissions.py") {
        Write-Host "`n執行驗證..." -ForegroundColor Yellow
        python check_and_update_permissions.py
    } else {
        Write-Host "找不到驗證腳本" -ForegroundColor Red
    }
}

# 開啟 Prisma Studio
Write-Host "`n============================================================" -ForegroundColor Cyan
$studio = Read-Host "是否要開啟 Prisma Studio（視覺化管理工具）? (y/n)"
if ($studio -eq "y") {
    Write-Host "啟動 Prisma Studio..." -ForegroundColor Cyan
    Write-Host "將在瀏覽器開啟 http://localhost:5555" -ForegroundColor Yellow
    npx prisma studio
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`n下一步建議:" -ForegroundColor Cyan
Write-Host "  1. 閱讀: docs\快速開始指南_v2.0.md" -ForegroundColor Gray
Write-Host "  2. 執行: python describe_tables.py (查看資料表)" -ForegroundColor Gray
Write-Host "  3. 執行: npx prisma studio (視覺化管理)" -ForegroundColor Gray
