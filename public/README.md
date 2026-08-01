# Public Assets Directory

此目錄包含公開的靜態資源，可直接通過 URL 訪問。

## 📁 目錄結構

```
public/
├── images/          # 圖片資源
├── fonts/           # 字體檔案
└── README.md        # 本文件
```

## 🖼️ Images

存放專案使用的圖片資源：

- Logo 和品牌圖片
- Icon 和圖標
- 佔位圖片
- 使用者介面圖片

### 建議的檔案命名

```
public/images/
├── logo/
│   ├── logo.svg
│   ├── logo.png
│   └── favicon.ico
├── icons/
│   ├── icon-home.svg
│   ├── icon-user.svg
│   └── icon-settings.svg
└── placeholders/
    ├── avatar-placeholder.png
    └── image-placeholder.png
```

## 🔤 Fonts

存放自定義字體檔案（如需要）：

- Web 字體 (.woff, .woff2)
- TrueType 字體 (.ttf)
- OpenType 字體 (.otf)

### 字體優化建議

1. 優先使用 `.woff2` 格式（最小、最快）
2. 使用字體子集化減少檔案大小
3. 使用 `font-display: swap` 避免 FOIT

## 📝 使用方式

### 在 Next.js 中使用

```tsx
import Image from 'next/image';

// 使用 public 目錄的圖片
<Image 
  src="/images/logo/logo.png" 
  alt="Logo" 
  width={200} 
  height={50} 
/>

// 或直接在 HTML 中
<img src="/images/icon-home.svg" alt="Home" />
```

### 在 CSS 中使用

```css
/* 字體 */
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom-font.woff2') format('woff2');
  font-display: swap;
}

/* 背景圖片 */
.hero {
  background-image: url('/images/hero-bg.jpg');
}
```

## 🎨 圖片優化建議

1. **格式選擇**:
   - 照片: JPEG, WebP
   - 圖標、插圖: SVG, PNG
   - 動畫: GIF, WebP, AVIF

2. **大小優化**:
   - 壓縮圖片（TinyPNG, Squoosh）
   - 使用適當的尺寸
   - 提供多種解析度（響應式）

3. **Next.js Image 優化**:
   - 自動 WebP/AVIF 轉換
   - 自動尺寸調整
   - 懶加載

## 📊 檔案大小建議

| 類型 | 建議大小 |
|------|---------|
| Logo | < 50KB |
| Icon | < 10KB |
| 一般圖片 | < 200KB |
| Hero 圖片 | < 500KB |
| 字體檔案 | < 100KB |

## 🚀 效能最佳化

```tsx
// next.config.ts 中的圖片配置
export default {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
  },
}
```

## 🔗 相關資源

- [Next.js Image Optimization](https://nextjs.org/docs/basic-features/image-optimization)
- [MDN: Responsive Images](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)
- [Web Font Best Practices](https://web.dev/font-best-practices/)
