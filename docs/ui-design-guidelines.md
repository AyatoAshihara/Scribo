# Scribo UIデザインガイドライン v2.0

本ドキュメントは、モダンSaaSアプリ（Notion, Linear, Vercel等）のトレンドを参考に、Scriboの視覚的デザインの指針を定める。

## デザイン原則

### 1. クリーン & ミニマル
- 不要な装飾を排除し、コンテンツを主役にする
- 余白を十分に確保し、視覚的な呼吸感を与える
- 情報の階層を明確にし、認知負荷を最小化する

### 2. 一貫性
- 全ページで同じデザインパターンを使用
- コンポーネントの再利用を徹底
- トランジション・アニメーションを統一

### 3. アクセシビリティ
- コントラスト比 4.5:1 以上を確保
- フォーカス状態の明示
- ダークモード対応

---

## カラーシステム

### ブランドカラー

| 名称 | Light Mode | Dark Mode | 用途 |
|------|------------|-----------|------|
| **Primary** | `#6366f1` (Indigo-500) | `#818cf8` (Indigo-400) | CTA、主要アクセント |
| **Secondary** | `#8b5cf6` (Violet-500) | `#a78bfa` (Violet-400) | サブアクション |
| **Accent** | `#06b6d4` (Cyan-500) | `#22d3ee` (Cyan-400) | ハイライト、リンク |

### セマンティックカラー

| 名称 | Light Mode | Dark Mode | 用途 |
|------|------------|-----------|------|
| **Success** | `#10b981` (Emerald-500) | `#34d399` | 合格、成功 |
| **Warning** | `#f59e0b` (Amber-500) | `#fbbf24` | 注意、警告 |
| **Error** | `#ef4444` (Red-500) | `#f87171` | エラー、不合格 |
| **Info** | `#3b82f6` (Blue-500) | `#60a5fa` | 情報、ヒント |

### 背景・サーフェス

| 名称 | Light Mode | Dark Mode | 用途 |
|------|------------|-----------|------|
| **Background** | `#fafafa` | `#09090b` | ページ全体背景 |
| **Surface** | `#ffffff` | `#18181b` | カード背景 |
| **Surface-Alt** | `#f4f4f5` | `#27272a` | 代替背景 |
| **Border** | `#e4e4e7` | `#3f3f46` | ボーダー |
| **Border-Light** | `#f4f4f5` | `#27272a` | 薄いボーダー |

### グラデーション

```css
/* プライマリグラデーション - CTAボタン等 */
.gradient-primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

/* ヒーローグラデーション - ヘッダー背景等 */
.gradient-hero {
  background: linear-gradient(135deg, 
    rgba(99, 102, 241, 0.1) 0%, 
    rgba(139, 92, 246, 0.1) 100%);
}

/* サーフェスグラデーション - 微細な奥行き */
.gradient-surface {
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
}
```

### DaisyUIカスタムテーマ設定

```javascript
// tailwind.config.js
module.exports = {
  daisyui: {
    themes: [
      {
        scribo: {
          "primary": "#6366f1",
          "secondary": "#8b5cf6",
          "accent": "#06b6d4",
          "neutral": "#18181b",
          "base-100": "#ffffff",
          "base-200": "#f4f4f5",
          "base-300": "#e4e4e7",
          "info": "#3b82f6",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
        "scribo-dark": {
          "primary": "#818cf8",
          "secondary": "#a78bfa",
          "accent": "#22d3ee",
          "neutral": "#fafafa",
          "base-100": "#18181b",
          "base-200": "#27272a",
          "base-300": "#3f3f46",
          "info": "#60a5fa",
          "success": "#34d399",
          "warning": "#fbbf24",
          "error": "#f87171",
        },
      },
    ],
  },
}
```

---

## タイポグラフィ

### フォントファミリー

```css
/* システムフォントスタック */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             'Hiragino Sans', 'Noto Sans JP', sans-serif;

/* モノスペース（スコア・タイマー等） */
font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
```

### フォントスケール

| 名称 | Tailwind | サイズ | ウェイト | 行高 | 用途 |
|------|----------|--------|---------|------|------|
| **Display** | `text-4xl font-bold` | 36px | 700 | 1.2 | ヒーロータイトル |
| **H1** | `text-2xl font-semibold` | 24px | 600 | 1.3 | ページタイトル |
| **H2** | `text-xl font-semibold` | 20px | 600 | 1.4 | セクションタイトル |
| **H3** | `text-lg font-medium` | 18px | 500 | 1.4 | カードタイトル |
| **Body** | `text-base` | 16px | 400 | 1.6 | 本文 |
| **Small** | `text-sm` | 14px | 400 | 1.5 | 補足テキスト |
| **XSmall** | `text-xs` | 12px | 400 | 1.4 | ラベル、注釈 |
| **Mono** | `font-mono text-lg` | 18px | 500 | 1.2 | スコア、タイマー |

### テキストカラー

| 用途 | Light Mode | Dark Mode | Tailwind |
|------|------------|-----------|----------|
| 主要テキスト | `#18181b` | `#fafafa` | `text-base-content` |
| 副次テキスト | `#71717a` | `#a1a1aa` | `text-base-content/70` |
| 薄いテキスト | `#a1a1aa` | `#71717a` | `text-base-content/50` |
| リンク | `#6366f1` | `#818cf8` | `text-primary` |

---

## スペーシング

### スケール

| Token | 値 | Tailwind | 用途 |
|-------|-----|----------|------|
| `space-1` | 4px | `gap-1`, `p-1` | インライン要素間 |
| `space-2` | 8px | `gap-2`, `p-2` | 密接な要素間 |
| `space-3` | 12px | `gap-3`, `p-3` | ボタン内padding |
| `space-4` | 16px | `gap-4`, `p-4` | カード内padding (小) |
| `space-5` | 20px | `gap-5`, `p-5` | カード内padding (標準) |
| `space-6` | 24px | `gap-6`, `p-6` | カード内padding (大) |
| `space-8` | 32px | `gap-8`, `p-8` | セクション間 |
| `space-12` | 48px | `gap-12`, `p-12` | 大セクション間 |

### 余白の原則

- **カード内**: `p-5` または `p-6` を標準とする
- **セクション間**: `mb-8` または `space-y-8`
- **要素グループ内**: `gap-4` または `space-y-4`
- **インライン**: `gap-2` または `gap-3`

---

## コンポーネント

### ヘッダー（ガラスモーフィズム）

```html
<header class="navbar bg-base-100/80 backdrop-blur-xl border-b border-base-200/50 
               sticky top-0 z-50 shadow-sm">
  <div class="flex-1">
    <a href="/" class="btn btn-ghost gap-2 text-xl font-bold hover:bg-transparent">
      <!-- SVGロゴ -->
      <svg class="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="currentColor">
        <path d="..."/>
      </svg>
      <span class="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
        Scribo
      </span>
    </a>
  </div>
  <div class="flex-none gap-2">
    <!-- ナビゲーション項目 -->
  </div>
</header>
```

### カード

```html
<!-- 標準カード -->
<div class="card bg-base-100 border border-base-200 rounded-2xl 
            shadow-sm hover:shadow-md hover:border-primary/20 
            transition-all duration-200">
  <div class="card-body p-5">
    <!-- コンテンツ -->
  </div>
</div>

<!-- インタラクティブカード（クリック可能） -->
<div class="card bg-base-100 border border-base-200 rounded-2xl 
            shadow-sm hover:shadow-lg hover:border-primary/30 hover:-translate-y-1
            cursor-pointer transition-all duration-200">
  <div class="card-body p-5">
    <!-- コンテンツ -->
  </div>
</div>

<!-- ハイライトカード -->
<div class="card bg-gradient-to-br from-primary/5 to-secondary/5 
            border border-primary/20 rounded-2xl">
  <div class="card-body p-5">
    <!-- コンテンツ -->
  </div>
</div>
```

### ボタン

```html
<!-- プライマリボタン（CTA） -->
<button class="btn bg-gradient-to-r from-primary to-secondary 
               text-white border-0 rounded-xl px-6
               shadow-lg shadow-primary/25
               hover:shadow-xl hover:shadow-primary/30 hover:scale-[1.02]
               active:scale-[0.98] transition-all duration-200">
  アクション
</button>

<!-- セカンダリボタン -->
<button class="btn btn-ghost border border-base-300 rounded-xl
               hover:bg-base-200 hover:border-base-400
               transition-all duration-200">
  キャンセル
</button>

<!-- アウトラインボタン -->
<button class="btn btn-outline btn-primary rounded-xl
               hover:bg-primary hover:text-white
               transition-all duration-200">
  詳細を見る
</button>

<!-- ゴーストボタン（アイコン用） -->
<button class="btn btn-ghost btn-circle hover:bg-base-200
               transition-all duration-200">
  <svg class="w-5 h-5">...</svg>
</button>
```

### 入力フィールド

```html
<!-- テキスト入力 -->
<input type="text" 
       class="input bg-base-100 border-base-300 rounded-xl w-full
              focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none
              placeholder:text-base-content/40
              transition-all duration-200" 
       placeholder="入力してください..." />

<!-- テキストエリア -->
<textarea class="textarea bg-base-100 border-base-300 rounded-xl w-full
                 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none
                 placeholder:text-base-content/40
                 transition-all duration-200"
          placeholder="回答を入力..."></textarea>

<!-- 検索ボックス -->
<div class="relative">
  <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-base-content/40">...</svg>
  <input type="search" 
         class="input bg-base-200/50 border-0 rounded-xl pl-10 w-full
                focus:bg-base-100 focus:ring-2 focus:ring-primary/20
                transition-all duration-200"
         placeholder="検索..." />
</div>
```

### バッジ

```html
<!-- ステータスバッジ -->
<span class="badge bg-success/10 text-success border-0 rounded-lg px-3 py-1">合格</span>
<span class="badge bg-warning/10 text-warning border-0 rounded-lg px-3 py-1">要改善</span>
<span class="badge bg-error/10 text-error border-0 rounded-lg px-3 py-1">不合格</span>
<span class="badge bg-info/10 text-info border-0 rounded-lg px-3 py-1">情報</span>

<!-- ランクバッジ -->
<span class="badge badge-lg bg-gradient-to-r from-amber-400 to-amber-500 text-white border-0 
             rounded-lg px-4 py-2 font-bold shadow-md">A</span>
```

### アラート

```html
<!-- 情報アラート -->
<div class="alert bg-info/10 border border-info/20 rounded-xl">
  <svg class="w-5 h-5 text-info shrink-0">...</svg>
  <span class="text-info">ヒント: 問題文を最後まで読んでから回答を始めましょう。</span>
</div>

<!-- 成功アラート -->
<div class="alert bg-success/10 border border-success/20 rounded-xl">
  <svg class="w-5 h-5 text-success shrink-0">...</svg>
  <span class="text-success">回答が保存されました。</span>
</div>

<!-- 警告アラート -->
<div class="alert bg-warning/10 border border-warning/20 rounded-xl">
  <svg class="w-5 h-5 text-warning shrink-0">...</svg>
  <span class="text-warning">文字数が目安に達していません。</span>
</div>
```

### プログレスバー

```html
<!-- 標準プログレス -->
<progress class="progress progress-primary h-2 rounded-full" value="75" max="100"></progress>

<!-- グラデーションプログレス -->
<div class="w-full bg-base-200 rounded-full h-2 overflow-hidden">
  <div class="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-500"
       style="width: 75%"></div>
</div>

<!-- ステップインジケーター -->
<div class="flex gap-1">
  <div class="flex-1 h-2 rounded-full bg-success"></div>
  <div class="flex-1 h-2 rounded-full bg-success"></div>
  <div class="flex-1 h-2 rounded-full bg-base-300"></div>
</div>
```

### モーダル

```html
<dialog class="modal modal-bottom sm:modal-middle">
  <div class="modal-box bg-base-100 rounded-2xl border border-base-200 shadow-2xl max-w-lg">
    <button class="btn btn-sm btn-circle btn-ghost absolute right-4 top-4">✕</button>
    <h3 class="font-semibold text-xl mb-4">タイトル</h3>
    <p class="text-base-content/70">コンテンツ</p>
    <div class="modal-action">
      <button class="btn btn-ghost rounded-xl">キャンセル</button>
      <button class="btn btn-primary rounded-xl">確認</button>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop bg-black/50 backdrop-blur-sm">
    <button>close</button>
  </form>
</dialog>
```

### ツールチップ

```html
<div class="tooltip tooltip-bottom" data-tip="説明テキスト">
  <button class="btn btn-ghost btn-circle btn-sm">
    <svg class="w-4 h-4 text-base-content/60">...</svg>
  </button>
</div>
```

---

## アイコン

### 推奨ライブラリ
[Heroicons](https://heroicons.com/) を標準アイコンセットとして使用する。

### 使用方法

```html
<!-- インラインSVG（推奨） -->
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" 
     stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M..."/>
</svg>
```

### サイズ規則

| サイズ | Tailwind | 用途 |
|--------|----------|------|
| 16px | `w-4 h-4` | インラインアイコン、バッジ内 |
| 20px | `w-5 h-5` | ボタン内、リスト項目 |
| 24px | `w-6 h-6` | ナビゲーション、アクション |
| 32px | `w-8 h-8` | 特徴アイコン、空状態 |
| 48px | `w-12 h-12` | 大型アイコン、イラスト |

### 絵文字の使用

❌ **避けるべき:**
```html
<span>📝 Scribo</span>
```

✅ **推奨:**
```html
<svg class="w-6 h-6 text-primary">...</svg>
<span>Scribo</span>
```

**例外:** 装飾的な用途（励ましメッセージ等）では絵文字を許可する。

---

## アニメーション・トランジション

### トランジション設定

| 用途 | Duration | Easing | Tailwind |
|------|----------|--------|----------|
| ホバー | 200ms | ease-out | `duration-200` |
| フォーカス | 150ms | ease-out | `duration-150` |
| モーダル | 300ms | ease-out | `duration-300` |
| ページ遷移 | 500ms | ease-in-out | `duration-500` |

### 標準トランジションクラス

```html
<!-- 全プロパティ -->
<div class="transition-all duration-200 ease-out">

<!-- 色のみ -->
<div class="transition-colors duration-200">

<!-- 変形のみ -->
<div class="transition-transform duration-200">

<!-- シャドウ + ボーダー -->
<div class="transition-shadow duration-200">
```

### ホバーエフェクト

```html
<!-- カードのホバー -->
<div class="hover:shadow-lg hover:-translate-y-1 hover:border-primary/20 
            transition-all duration-200">

<!-- ボタンのホバー -->
<button class="hover:scale-[1.02] active:scale-[0.98] transition-transform duration-200">

<!-- リンクのホバー -->
<a class="hover:text-primary hover:underline underline-offset-4 transition-colors duration-200">
```

### ローディングアニメーション

```html
<!-- スピナー -->
<span class="loading loading-spinner loading-md text-primary"></span>

<!-- パルス -->
<div class="animate-pulse bg-base-300 rounded-lg h-4 w-32"></div>

<!-- スケルトン -->
<div class="flex flex-col gap-4">
  <div class="skeleton h-4 w-full"></div>
  <div class="skeleton h-4 w-3/4"></div>
</div>
```

---

## レイアウト

### コンテナ

```html
<!-- 標準コンテナ -->
<div class="container mx-auto px-4 max-w-5xl">

<!-- 狭いコンテナ（フォーム等） -->
<div class="container mx-auto px-4 max-w-2xl">

<!-- 広いコンテナ（ダッシュボード） -->
<div class="container mx-auto px-4 max-w-7xl">
```

### グリッド

```html
<!-- 2カラム（レスポンシブ） -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

<!-- 3カラム（レスポンシブ） -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- 統計カード（4カラム） -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
```

### フレックス

```html
<!-- 中央寄せ -->
<div class="flex items-center justify-center">

<!-- 両端揃え -->
<div class="flex items-center justify-between">

<!-- スタック（縦積み） -->
<div class="flex flex-col gap-4">
```

---

## ダークモード

### 実装方法

```html
<!-- HTML要素にテーマ属性を設定 -->
<html data-theme="scribo">      <!-- ライトモード -->
<html data-theme="scribo-dark"> <!-- ダークモード -->
```

### 切り替えコンポーネント

```html
<label class="swap swap-rotate">
  <input type="checkbox" class="theme-controller" value="scribo-dark" />
  <!-- 太陽アイコン（ライト時表示） -->
  <svg class="swap-off w-6 h-6 fill-current">...</svg>
  <!-- 月アイコン（ダーク時表示） -->
  <svg class="swap-on w-6 h-6 fill-current">...</svg>
</label>
```

### Alpine.jsでの制御

```javascript
// ダークモード状態管理
Alpine.store('theme', {
  dark: localStorage.getItem('theme') === 'dark',
  
  toggle() {
    this.dark = !this.dark;
    localStorage.setItem('theme', this.dark ? 'dark' : 'light');
    document.documentElement.setAttribute(
      'data-theme', 
      this.dark ? 'scribo-dark' : 'scribo'
    );
  },
  
  init() {
    // システム設定を検出
    if (localStorage.getItem('theme') === null) {
      this.dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    document.documentElement.setAttribute(
      'data-theme', 
      this.dark ? 'scribo-dark' : 'scribo'
    );
  }
});
```

---

## レスポンシブ対応

### ブレークポイント

| 名称 | 幅 | 用途 |
|------|-----|------|
| `sm` | 640px | スマートフォン（横） |
| `md` | 768px | タブレット |
| `lg` | 1024px | 小型デスクトップ |
| `xl` | 1280px | デスクトップ |

### モバイルファースト原則

```html
<!-- モバイルをベースに、大画面で拡張 -->
<div class="text-base md:text-lg lg:text-xl">
<div class="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
<div class="p-4 md:p-6 lg:p-8">
```

### タッチターゲット

モバイルでのタッチ操作を考慮し、最小44x44pxのタップ領域を確保する。

```html
<!-- 小さいボタンでもタップ領域は確保 -->
<button class="btn btn-sm min-h-[44px] min-w-[44px]">
```

---

## 実装チェックリスト

### 新規コンポーネント作成時

- [ ] カラーはテーマ変数を使用しているか
- [ ] スペーシングは規定のスケールを使用しているか
- [ ] トランジションは統一されているか
- [ ] ダークモードで正しく表示されるか
- [ ] モバイルでの表示を確認したか
- [ ] フォーカス状態が適切か
- [ ] アイコンはHeroiconsを使用しているか

### デザインレビュー時

- [ ] 視覚的階層は明確か
- [ ] 余白は十分か
- [ ] インタラクションは直感的か
- [ ] ローディング状態があるか
- [ ] エラー状態の表示があるか
- [ ] 空状態の表示があるか
