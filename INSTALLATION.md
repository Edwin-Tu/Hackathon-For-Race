# 安裝指南

## 問題說明

由於 ESLint 9 的重大變更，需要使用新的配置格式。

## 已修正的問題

1. ✅ ESLint 升級到 9.17.0
2. ✅ 移除不相容的 TypeScript ESLint 外掛
3. ✅ 使用 Next.js 內建的 ESLint 配置
4. ✅ 創建新的 ESLint 9 配置檔 (eslint.config.mjs)

## 安裝步驟

### 1. 清理舊的依賴

```powershell
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue
```

### 2. 安裝依賴

```powershell
npm install
```

如果遇到 peer dependency 警告，使用：

```powershell
npm install --legacy-peer-deps
```

### 3. 生成 Prisma Client

```powershell
npm run prisma:generate
```

### 4. 複製環境變數

```powershell
Copy-Item .env.example .env
```

然後編輯 `.env` 填入實際的配置值。

### 5. 驗證安裝

```powershell
# 檢查 TypeScript
npm run type-check

# 檢查 Lint（可能會有錯誤需要修正）
npm run lint

# 啟動開發伺服器
npm run dev
```

## 可選：設定 Git Hooks

如果需要 Git Hooks（提交前自動檢查），執行：

```powershell
# 手動安裝 husky（npm prepare 在 Windows 可能失敗）
npx husky install
```

## 常見問題

### Q: Husky 安裝失敗？

在 Windows PowerShell，`||` 運算符不被支援。你可以：

1. 跳過 husky（不影響開發）
2. 使用 Git Bash 執行
3. 手動執行 `npx husky install`

### Q: TypeScript 找不到？

執行 `npm install` 後會自動安裝。確認 `node_modules/.bin/tsc` 存在。

### Q: Prettier 找不到？

執行 `npm install` 後會自動安裝。確認 `node_modules/.bin/prettier` 存在。

### Q: 仍有版本衝突？

使用強制安裝：

```powershell
npm install --force
```

或使用舊版 peer deps 解析：

```powershell
npm install --legacy-peer-deps
```

## 簡化的開發流程

如果你不需要所有的開發工具，可以簡化配置：

### 最小化安裝

```powershell
# 只安裝生產依賴
npm install --production

# 然後安裝必要的開發工具
npm install --save-dev typescript @types/node @types/react @types/react-dom
npm install --save-dev eslint eslint-config-next
npm install --save-dev prisma
```

### 啟動開發

```powershell
npm run dev
```

## 下一步

安裝完成後，請參考主要的 README.md 繼續開發。

---

**更新日期**: 2026-08-01  
**狀態**: ✅ 已修正 ESLint 9 相容性問題
