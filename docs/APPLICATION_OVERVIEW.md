# Scribo アプリケーション概要

## 1. プロジェクト概要

**Scribo** は、ITストラテジスト試験合格のための**「戦略的執筆トレーニング」プラットフォーム**です。
単なる模試・採点ツールではなく、「準備（資産化）→設計→執筆」という合格のための正しいプロセスをアプリ体験として提供します。

**本番URL:** http://scribo-alb-760941679.ap-northeast-1.elb.amazonaws.com/

---

## 2. コンセプト: "The Strategist's Forge"

合格ノウハウに基づき、以下の3つのフェーズで学習を支援します。

1.  **資産化 (Asset Preparation)**:
    *   「準備モジュール」を作成・管理。
    *   AIが経験談を「論文用語」にリライトし、合格レベルのネタを蓄積。
2.  **設計 (Strategic Planning)**:
    *   いきなり書き始めず、設問分解と章構成（設計図）を作成。
    *   蓄積したモジュールを設計図にマッピング。
3.  **執筆・評価 (Execution & Feedback)**:
    *   設計図を見ながら執筆するスプリットビューエディタ。
    *   形式不備（行頭句読点など）のリアルタイム検知。
    *   IPA基準の厳密なAI採点（減点方式）。

---

## 3. 技術スタック

サーバーサイドレンダリング中心のモダンな軽量アーキテクチャを採用しています。

### バックエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| FastAPI | 0.115.6 | Webフレームワーク |
| Jinja2 | 3.1.4 | テンプレートエンジン |
| uvicorn | 0.32.1 | ASGIサーバー |
| boto3 | 1.35.x | AWS SDK |
| pydantic-settings | 2.6.x | 設定管理 |

### フロントエンド (Material Design 3)

| 技術 | バージョン | 用途 |
|------|-----------|------|
| htmx | 2.0.4 | 非同期通信、部分更新 |
| Alpine.js | 3.14.3 | リアクティブUI、状態管理 |
| Tailwind CSS | CDN | ユーティリティCSS |
| DaisyUI | 4.12.14 | UIコンポーネント (Materialテーマ) |
| Material Symbols | Google Fonts | アイコン |

### インフラ

| サービス | 用途 |
|---------|------|
| ECS Fargate (Spot) | コンテナホスティング |
| ALB | ロードバランシング |
| ECR | コンテナイメージ |
| DynamoDB | データストア (回答、モジュール、設計図) |
| S3 | 問題本文格納 |
| Amazon Bedrock | AI採点・リライト |

---

## 4. ディレクトリ構造

```text
app/
├── main.py                 # FastAPIエントリーポイント
├── config.py               # 環境変数・設定管理
├── routers/                # APIルーター
│   ├── exams.py            # 試験一覧・詳細
│   ├── modules.py          # [New] 準備モジュール管理
│   ├── designs.py          # [New] 論文設計
│   ├── answers.py          # 回答保存
│   └── scoring.py          # AI採点
├── templates/              # Jinja2テンプレート
│   ├── base.html           # 共通レイアウト (Material Design)
│   └── pages/
│       ├── index.html      # ダッシュボード
│       ├── modules/        # [New] モジュール管理画面
│       ├── design/         # [New] 設計ウィザード
│       ├── problem.html    # 執筆エディタ
│       └── result.html     # 採点結果
└── static/
    ├── css/style.css       # カスタムスタイル
    └── js/
        ├── app.js          # 共通ユーティリティ
        ├── editor.js       # [Update] 執筆エディタロジック
        └── ...

backend/
├── lib/
│   ├── scribo-fargate-stack.ts   # ECS Fargate構成
│   └── ...
```

---

## 5. 主要機能ロードマップ

詳細は `todo.md` を参照してください。

### Phase 1: 資産化
- 準備モジュール管理 (CRUD)
- AIリライティング (平易な表現→論文用語)

### Phase 2: 設計
- 設問分解UI
- 論文設計ウィザード

### Phase 3: 執筆・評価
- スプリットビューエディタ
- リアルタイムバリデーション
- 減点方式AI採点


- **ページ:** `/` (index.html)
- **機能:**
  - 試験区分タブ（IS: ITストラテジスト, PM: プロジェクトマネージャ, SA: システムアーキテクト）
  - 問題カード一覧表示（年度降順）
  - htmxによる非同期タブ切り替え

### 4.3 問題演習

- **ページ:** `/problem/{exam_type}/{problem_id}` (problem.html)
- **機能:**
  - **左右分割レイアウト**: 左に問題文、右に回答入力
  - **設問タブ**: 設問ア/イ/ウを切り替え
  - **リアルタイム文字数カウント**: 目標範囲に応じた色分け
  - **進捗インジケーター**: 設問完了状況の可視化
  - **「あと○文字」メッセージ**: 目標達成への動機付け
  - **試験タイマー**: 120分カウントダウン、残り時間警告
  - **ローカルストレージ自動保存**: 回答の永続化

### 4.4 採点機能

- **エンドポイント:** `POST /api/scoring`
- **機能:**
  - Amazon Bedrock (Claude 3.5 Sonnet) による8観点評価
  - 設問別・観点別の詳細スコアリング
  - 最終ランク判定（A/B/C/D）

**評価観点:**
1. 充足度 (0.15)
2. 具体性 (0.15)
3. 妥当性 (0.15)
4. 一貫性 (0.10)
5. 主張 (0.15)
6. 洞察力-行動力 (0.10)
7. 独創性-先見性 (0.10)
8. 表現力 (0.10)

### 4.5 採点結果表示

- **ページ:** `/result/{submission_id}` (result.html)
- **機能:**
  - **労働の錯覚**: 採点中のステップ表示（回答受信→分析→評価→計算）
  - **段階的開示**: まずランク表示、詳細は折りたたみ
  - **合格時祝福**: 紙吹雪エフェクト
  - **不合格時励まし**: 「あと○点で合格」のポジティブメッセージ

---

## 5. データモデル

### 試験データ (DynamoDB: scribo-ipa)

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | String | `EXAM#{exam_type}` |
| SK | String | `YEAR#{year}{term}#ESSAY#Q{num}` |
| title | String | 問題タイトル |
| year_term | String | 年度・期 |
| s3_uri | String | S3問題本文URI |

### 回答・採点データ (DynamoDB: SubmissionTable)

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | String | `SUBMISSION#{submission_id}` |
| SK | String | `ANSWER` or `SCORE` |
| exam_type | String | 試験区分 |
| problem_id | String | 問題ID |
| answers | Map | 設問別回答 |
| aggregate_score | Number | 総合スコア |
| final_rank | String | A/B/C/D |

### 問題本文 (S3: scribo-essay-evaluator)

```json
{
  "problemContent": "問題本文...",
  "problemQuestion": {
    "設問ア": "あなたが携わった...",
    "設問イ": "設問アで述べた...",
    "設問ウ": "設問イで述べた..."
  },
  "wordCountLimits": {
    "設問ア": { "min": 600, "max": 800 },
    "設問イ": { "min": 700, "max": 1000 },
    "設問ウ": { "min": 600, "max": 800 }
  }
}
```

---

## 6. UIパターン

### htmx

```html
<!-- 非同期読み込み -->
<div hx-get="/api/exams/partial/list?exam_type=IS" 
     hx-trigger="load" 
     hx-target="#exam-list">
</div>

<!-- フォーム送信 -->
<button hx-post="/api/answers" 
        hx-target="#result">
</button>
```

### Alpine.js

```html
<!-- リアクティブ状態管理 -->
<div x-data="{ count: 0 }">
    <span x-text="count"></span>
    <button @click="count++">+</button>
</div>

<!-- 非同期初期化 -->
<div x-data="problemViewer('IS', '...')" x-init="init()">
    ...
</div>
```

### DaisyUI

```html
<!-- コンポーネント例 -->
<button class="btn btn-primary">送信</button>
<div class="card bg-base-100 shadow-xl">...</div>
<div class="tabs tabs-boxed">...</div>
<span class="badge badge-success">完了</span>
```

---

## 7. 開発・運用

### ローカル開発

```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### デプロイ

```bash
# 自動デプロイ（mainブランチpush時）
git add .
git commit -m "feat: New feature"
git push origin main

# 手動CDKデプロイ
cd backend
npx cdk deploy ScriboFargateStack
```

### ログ確認

```bash
aws logs tail /ecs/scribo-app --follow
```

---

## 8. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | システム構成図、AWS構成 |
| [API_SPECIFICATION.md](./API_SPECIFICATION.md) | API仕様、エンドポイント詳細 |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | デプロイ手順、CI/CD |
| [SCORING_API.md](./SCORING_API.md) | 採点ロジック詳細 |
| [ux-design-guidelines.md](./ux-design-guidelines.md) | UX設計の心理学的原則 |
