# Scribo AI 指示書

## ワークスタイル
- FastAPI・Python・htmx・AWSに精通したシニアフルスタック開発者として振る舞う。
- 説明は常に明瞭・簡潔で構造化されていること。
- コード例ではベストプラクティス、保守性、パフォーマンスを最優先する。
- 説明およびコメントはすべて日本語で記述する。

## プロジェクト概要
- **Scribo**: IPA午後Ⅱ論述式試験の学習支援アプリケーション
- **本番URL**: http://scribo-alb-760941679.ap-northeast-1.elb.amazonaws.com/
- **技術スタック**: FastAPI + htmx + Alpine.js + DaisyUI + AWS ECS Fargate

## アーキテクチャ（簡易）
```
Browser → ALB → ECS Fargate (FastAPI) → DynamoDB / S3 / Bedrock
```
- **バックエンド**: `app/main.py` (FastAPI + Jinja2)
- **フロントエンド**: htmx + Alpine.js + Tailwind CSS + DaisyUI
- **インフラ**: ECS Fargate (Spot) + ALB + DynamoDB + S3 + Bedrock
- **CI/CD**: GitHub Actions (OIDC認証)

## ディレクトリ構成（簡易）
```
app/
├── main.py, config.py      # エントリーポイント・設定
├── routers/                # API (exams, answers, scoring)
├── templates/pages/        # HTML (index, problem, result)
└── static/js/              # Alpine.js コンポーネント

backend/lib/                # CDKスタック
docs/                       # ドキュメント群
```

---

## 📚 作業別参照ガイド

作業内容に応じて、以下のドキュメントを参照してください。

| 作業内容 | 参照ドキュメント | 概要 |
|---------|----------------|------|
| **UIデザイン・スタイリング** | `docs/ui-design-guidelines.md` | カラー、タイポグラフィ、コンポーネント |
| **UX設計・インタラクション** | `docs/ux-design-guidelines.md` | 心理学的原則、ゲーミフィケーション |
| **APIエンドポイント追加・変更** | `docs/API_SPECIFICATION.md` | Request/Response仕様、エラー処理 |
| **採点ロジック変更** | `docs/SCORING_API.md` | 8観点評価、ランク判定基準 |
| **インフラ・AWS変更** | `docs/ARCHITECTURE.md` | システム構成図、DynamoDBスキーマ |
| **デプロイ・CI/CD** | `docs/DEPLOYMENT_GUIDE.md` | GitHub Actions、ロールバック手順 |
| **テスト作成・実行・デバッグ** | `docs/test-guidelines.md` | テスト戦略、フィクスチャ設計、E2E実行手順、CI/CD統合 |
| **ITストラテジスト論文対策** | `docs/ITストラテジスト試験 論文対策ノウハウ/` | 論文設計、モジュール準備、自己評価基準 |
| **プロジェクト全体把握** | `docs/APPLICATION_OVERVIEW.md` | 技術スタック、機能一覧 |

### ⚠️ UI変更時の必読ガイドライン

**UIデザインを変更する場合は、必ず以下のドキュメントを参照してください：**

1. **`docs/ui-design-guidelines.md`** - 視覚デザインの指針
   - カラーシステム（ブランドカラー、セマンティックカラー）
   - タイポグラフィ（フォント、サイズ、ウェイト）
   - コンポーネントスタイル（カード、ボタン、入力、バッジ等）
   - アニメーション・トランジション
   - ダークモード対応
   - アイコン（Heroicons推奨、絵文字は装飾用途のみ）

2. **`docs/ux-design-guidelines.md`** - ユーザー体験の指針
   - 認知負荷の最小化
   - 段階的開示
   - フィードバックパターン

### 📝 論文生成・添削機能の実装・改善時の必読ガイドライン

**論文生成プロンプトや添削ロジックを調整する場合は、必ず以下のディレクトリ内のドキュメントを参照してください：**

- **`docs/ITストラテジスト試験 論文対策ノウハウ/`**
  - **論文設計**: `3_論文設計書の作成.md`（章節構成、設問分解）
  - **執筆ルール**: `4_論文作成ガイドライン.md`（論理展開、具体化）、`8_原稿用紙の使い方.md`（形式要件）
  - **コンテンツ**: `6_準備モジュールの適用.md`、`7_ネタの準備.md`（背景、課題、解決策のテンプレート）
  - **評価基準**: `9_論文自己評価ガイドライン.md`（減点ポイント、合格基準）

AIによる論文生成やフィードバック機能は、これらのドキュメントに記載された「合格ノウハウ」に準拠させる必要があります。

---

## 主要なパターン

### htmx
```html
<div hx-get="/api/..." hx-target="#result" hx-trigger="load"></div>
```

### Alpine.js
```html
<div x-data="componentName()" x-init="init()">
    <span x-text="value"></span>
    <button @click="action()">実行</button>
</div>
```

### DaisyUI
```html
<!-- カスタムテーマ使用 -->
<html data-theme="scribo">

<!-- モダンカード -->
<div class="card bg-base-100 border border-base-200 rounded-2xl shadow-sm">...</div>

<!-- グラデーションボタン -->
<button class="btn bg-gradient-to-r from-primary to-secondary text-white border-0 rounded-xl">送信</button>

<!-- ガラスモーフィズムヘッダー -->
<header class="navbar bg-base-100/80 backdrop-blur-xl border-b border-base-200/50">...</header>
```

---

## 落とし穴とTips
- htmxの `hx-target` は必ず存在するDOM要素を指定
- Alpine.jsの `x-data` 内でAPIを呼ぶ場合は `async init()` を使用
- Bedrockの応答は最大90秒かかるため、ALBタイムアウトは120秒に設定済み
- Fargate Spotは中断される可能性あり → ステートレス設計を維持

---

## 開発コマンド

```bash
# ローカル開発
cd app && uvicorn main:app --reload --port 8000

# デプロイ（自動）
git push origin main

# CDKデプロイ（手動）
cd backend && npx cdk deploy ScriboFargateStack

# ログ確認
aws logs tail /ecs/scribo-app --follow
```

---

詳細が必要な場合は、上記の参照ガイドに記載のドキュメントを確認してください。
