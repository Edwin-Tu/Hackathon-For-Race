# 貢獻指南 (Contributing Guide)

感謝你考慮為智護聲盾 (Smart Care Shield) 做出貢獻！

## 📋 目錄

- [行為準則](#行為準則)
- [如何貢獻](#如何貢獻)
- [開發流程](#開發流程)
- [程式碼規範](#程式碼規範)
- [提交規範](#提交規範)
- [Pull Request 流程](#pull-request-流程)
- [測試要求](#測試要求)
- [文檔更新](#文檔更新)

## 🤝 行為準則

### 我們的承諾

為了營造開放且友善的環境，我們承諾：
- 尊重不同的觀點和經驗
- 接受建設性的批評
- 關注對社群最有利的事情
- 對其他社群成員表現同理心

### 不可接受的行為

- 使用性別化語言或圖像
- 人身攻擊或侮辱性評論
- 公開或私下騷擾
- 未經許可發布他人隱私資訊

## 💡 如何貢獻

### 報告 Bug

發現問題？請到 [GitHub Issues](https://github.com/Edwin-Tu/Hackathon-For-Race/issues) 回報：

1. 檢查是否已有類似的 Issue
2. 使用 Bug Report 模板
3. 提供詳細的重現步驟
4. 包含環境資訊（OS、Node 版本等）
5. 如可能，提供螢幕截圖

**Bug Report 範本**:
```markdown
## Bug 描述
簡短描述問題

## 重現步驟
1. 前往 '...'
2. 點擊 '...'
3. 滾動到 '...'
4. 看到錯誤

## 預期行為
描述你預期應該發生什麼

## 實際行為
描述實際發生了什麼

## 環境資訊
- OS: [例如 Windows 11]
- Node: [例如 20.0.0]
- Browser: [例如 Chrome 120]
- Version: [例如 2.0.0]

## 截圖
如果適用，請添加截圖
```

### 建議新功能

有新想法？

1. 檢查 [Roadmap](docs/PROJECT_STATUS.md)
2. 開啟 Feature Request Issue
3. 清楚描述功能與用例
4. 說明為何需要此功能

**Feature Request 範本**:
```markdown
## 功能描述
清晰簡潔的功能描述

## 問題陳述
這個功能解決了什麼問題？

## 建議解決方案
描述你希望如何實現

## 替代方案
是否考慮過其他方案？

## 額外資訊
任何其他相關資訊、截圖等
```

### 改善文檔

文檔改善也是重要的貢獻！

- 修正錯字或語法錯誤
- 補充缺少的說明
- 添加使用範例
- 翻譯文檔

## 🔧 開發流程

### 1. Fork 專案

```bash
# 在 GitHub 上 Fork 專案
# 然後 Clone 到本地
git clone https://github.com/YOUR_USERNAME/Hackathon-For-Race.git
cd Hackathon-For-Race
```

### 2. 設定開發環境

```bash
# 安裝依賴
npm install

# 複製環境變數
cp .env.example .env

# 生成 Prisma Client
npm run prisma:generate

# 啟動開發伺服器
npm run dev
```

### 3. 建立分支

```bash
# 從 main 分支建立新分支
git checkout -b feature/your-feature-name

# 或修復 Bug
git checkout -b fix/bug-description
```

**分支命名規範**:
- `feature/` - 新功能
- `fix/` - Bug 修復
- `docs/` - 文檔更新
- `refactor/` - 程式碼重構
- `test/` - 測試相關
- `chore/` - 雜項更新

### 4. 進行變更

遵循我們的[程式碼規範](#程式碼規範)進行開發。

### 5. 提交變更

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範：

```bash
git add .
git commit -m "feat: add user profile page"
```

### 6. 推送分支

```bash
git push origin feature/your-feature-name
```

### 7. 開啟 Pull Request

在 GitHub 上開啟 PR，使用我們的 PR 模板。

## 📝 程式碼規範

### TypeScript / JavaScript

我們使用 ESLint 和 Prettier 來保持程式碼一致性。

**自動格式化**:
```bash
npm run format          # 格式化所有檔案
npm run lint:fix        # 自動修正 ESLint 錯誤
```

**規範**:
- 使用 TypeScript strict 模式
- 優先使用 `const` 而非 `let`
- 禁止使用 `var`
- 優先使用箭頭函數
- 使用 Path Alias (`@/`)

**範例**:
```typescript
// ✅ Good
const getUserName = (user: User): string => {
  return user.name;
};

// ❌ Bad
var getUserName = function(user) {
  return user.name
}
```

### React / Next.js

**元件結構**:
```tsx
// 1. Imports
import React from 'react';
import { Box } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types/user';

// 2. 型別定義
interface UserProfileProps {
  user: User;
  onUpdate: (user: User) => void;
}

// 3. 元件
export const UserProfile: React.FC<UserProfileProps> = ({ user, onUpdate }) => {
  // Hooks
  const { isAuthenticated } = useAuth();

  // State
  const [isEditing, setIsEditing] = React.useState(false);

  // Effects
  React.useEffect(() => {
    // ...
  }, []);

  // Handlers
  const handleUpdate = () => {
    // ...
  };

  // Render
  return (
    <Box>
      {/* JSX */}
    </Box>
  );
};
```

**命名規範**:
- 元件: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useAuth.ts`)
- 常數: UPPER_SNAKE_CASE (`API_ENDPOINTS`)
- 變數/函數: camelCase (`userName`, `fetchUser`)

### Python

遵循 PEP 8 規範。

**格式化**:
```bash
black tools/python/*.py
```

**規範**:
- 使用 4 空格縮排
- 行長度限制 88 字元（Black 預設）
- 使用 type hints
- Docstrings 使用 Google 風格

**範例**:
```python
def fetch_user(user_id: str) -> dict:
    """
    Fetch user data from database.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A dictionary containing user data.

    Raises:
        ValueError: If user_id is invalid.
    """
    # Implementation
    pass
```

### CSS / Styling

使用 Emotion (CSS-in-JS)。

**規範**:
- 使用 MUI theme 變數
- 響應式設計使用 breakpoints
- 避免 magic numbers

**範例**:
```tsx
const StyledBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1),
  },
}));
```

## 📨 提交規範

我們使用 [Conventional Commits](https://www.conventionalcommits.org/) 規範。

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文檔更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置或輔助工具
- `perf`: 效能改善

### 範例

```bash
# 新功能
git commit -m "feat(auth): add JWT authentication"

# Bug 修復
git commit -m "fix(api): resolve CORS issue"

# 文檔
git commit -m "docs(readme): update installation steps"

# 重構
git commit -m "refactor(components): extract Button component"

# 測試
git commit -m "test(auth): add login flow tests"

# Breaking Change
git commit -m "feat(api)!: change user endpoint structure

BREAKING CHANGE: API endpoint /users now returns different format"
```

## 🔀 Pull Request 流程

### 1. 確保程式碼品質

```bash
# 執行所有檢查
npm run type-check      # TypeScript 檢查
npm run lint            # ESLint 檢查
npm run format:check    # 格式檢查
npm run test            # 執行測試
```

### 2. 更新文檔

- 更新 README（如需要）
- 更新 API 文檔（如需要）
- 添加 CHANGELOG 條目（如需要）

### 3. 填寫 PR 描述

**PR 模板**:
```markdown
## 變更類型
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## 變更描述
清楚描述你做了什麼變更

## 相關 Issue
Closes #123

## 測試
描述你如何測試這些變更

## 截圖（如適用）
添加截圖來展示變更

## Checklist
- [ ] 我的程式碼遵循專案的程式碼規範
- [ ] 我已進行自我審查
- [ ] 我已添加註釋（特別是複雜的部分）
- [ ] 我已更新相關文檔
- [ ] 我的變更不會產生新的警告
- [ ] 我已添加測試證明修復有效或功能正常
- [ ] 新舊測試都通過
```

### 4. 程式碼審查

- 團隊成員會審查你的程式碼
- 根據反饋進行必要的修改
- 保持禮貌和開放的態度

### 5. 合併

- 所有檢查通過後
- 獲得至少 1 個 Approve
- 維護者會合併你的 PR

## 🧪 測試要求

### 單元測試

為新功能添加單元測試：

```tsx
// UserProfile.test.tsx
import { render, screen } from '@testing-library/react';
import { UserProfile } from './UserProfile';

describe('UserProfile', () => {
  it('renders user name', () => {
    const user = { id: '1', name: 'John' };
    render(<UserProfile user={user} />);
    expect(screen.getByText('John')).toBeInTheDocument();
  });
});
```

### 測試覆蓋率

- 目標覆蓋率: >= 50%
- 關鍵功能應達到 >= 80%

```bash
npm run test:ci         # 生成覆蓋率報告
```

### E2E 測試（可選）

對於重要功能，建議添加 E2E 測試：

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'user@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

## 📚 文檔更新

### 何時需要更新文檔

- 添加新功能
- 更改 API
- 修改配置
- 更新依賴

### 文檔位置

| 內容 | 位置 |
|------|------|
| 專案說明 | `README.md` |
| API 文檔 | `docs/API.md` |
| 技術文檔 | `docs/TECHNICAL_DOCUMENTATION.md` |
| 貢獻指南 | `CONTRIBUTING.md` |
| 更新日誌 | `CHANGELOG.md` |

## 💬 溝通渠道

- **GitHub Issues**: 問題回報和功能請求
- **GitHub Discussions**: 一般討論和問答
- **Pull Requests**: 程式碼審查和討論

## 🎓 學習資源

### 專案技術

- [Next.js 教學](https://nextjs.org/learn)
- [React 文檔](https://react.dev/learn)
- [TypeScript 手冊](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Prisma 指南](https://www.prisma.io/docs/getting-started)
- [Material-UI 教學](https://mui.com/material-ui/getting-started/)

### 開發實踐

- [Git 工作流程](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [測試驅動開發](https://www.freecodecamp.org/news/test-driven-development-tutorial-how-to-test-javascript-and-reactjs-app/)

## ❓ 常見問題

### Q: 我是新手，可以貢獻嗎？

A: 當然可以！我們歡迎所有層級的貢獻者。可以從以下開始：
- 修正文檔中的錯字
- 改善 README
- 添加測試
- 標記為 `good first issue` 的 Issues

### Q: 我不熟悉某個技術可以貢獻嗎？

A: 可以！這是學習的好機會。隨時在 Issue 或 PR 中詢問問題。

### Q: 我的 PR 多久會被審查？

A: 通常在 2-3 個工作日內。如果超過一週，可以禮貌地提醒。

### Q: 審查意見太多怎麼辦？

A: 不要氣餒！程式碼審查是學習和改進的機會。逐項處理反饋即可。

## 🙏 致謝

感謝所有貢獻者讓這個專案變得更好！

你的名字會出現在：
- [Contributors](https://github.com/Edwin-Tu/Hackathon-For-Race/graphs/contributors) 頁面
- 專案的 README

## 📄 授權

貢獻到此專案即表示你同意在 ISC License 下授權你的貢獻。

---

**祝你貢獻愉快！** 🎉

如有任何問題，請隨時在 [Issues](https://github.com/Edwin-Tu/Hackathon-For-Race/issues) 中提問。
