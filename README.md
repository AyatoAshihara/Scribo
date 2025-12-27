# Scribo - IPA午後Ⅱ論述式試験 学習支援アプリ

FastAPI + htmx + Alpine.js で構築された、IPA情報処理技術者試験の午後Ⅱ論述式問題の学習支援アプリケーションです。

## 技術スタック

### バックエンド
- **FastAPI** - Python Web フレームワーク
- **Jinja2** - テンプレートエンジン
- **boto3** - AWS SDK (DynamoDB, Bedrock)
- **uvicorn** - ASGI サーバー

### フロントエンド
- **htmx** - HTML属性ベースの非同期通信
- **Alpine.js** - 軽量リアクティブフレームワーク
- **Tailwind CSS + DaisyUI** - UIコンポーネント

### インフラ
- **ECS Fargate (Spot)** - コンテナ実行環境
- **ALB** - ロードバランサー
- **DynamoDB** - データストア
- **Amazon Bedrock** - AI採点 (Claude 3.5 Sonnet)
- **AWS CDK** - Infrastructure as Code

## プロジェクト構成

```
Scribo/
├── app/                          # FastAPIアプリケーション
│   ├── main.py                   # エントリーポイント
│   ├── config.py                 # 設定管理
│   ├── routers/                  # APIルーター
│   │   ├── exams.py              # 試験一覧・詳細API
│   │   ├── answers.py            # 回答保存API
│   │   └── scoring.py            # AI採点API
│   ├── templates/                # Jinja2テンプレート
│   │   ├── base.html             # ベーステンプレート
│   │   └── pages/                # ページテンプレート
│   ├── static/                   # 静的ファイル
│   │   ├── css/style.css
│   │   └── js/                   # Alpine.jsコンポーネント
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── backend/                      # CDKインフラ
│   ├── lib/
│   │   └── scribo-fargate-stack.ts
│   └── bin/
│       └── scribo-fargate.ts
├── .github/workflows/            # CI/CD
│   ├── deploy.yml                # アプリデプロイ
│   └── deploy-infra.yml          # インフラデプロイ
└── docs/                         # ドキュメント
```

## ローカル開発

### 前提条件
- Python 3.12+
- Docker & Docker Compose
- AWS CLI (認証設定済み)

### 起動方法

```bash
# 1. 環境変数を設定
cp app/.env.example app/.env
# .envファイルを編集してAWS認証情報を設定

# 2. Docker Compose で起動
cd app
docker-compose up

# 3. ブラウザでアクセス
# http://localhost:8000
```

### 直接実行（Dockerなし）

```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload
```

## デプロイ

### 初回インフラ構築

```bash
cd backend
npm install
npx cdk deploy ScriboFargateStack
```

### アプリケーションデプロイ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをビルド・プッシュ
cd app
docker build -t scribo-app .
docker tag scribo-app:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# ECSサービスを更新
aws ecs update-service --cluster scribo-cluster --service scribo-service --force-new-deployment
```

### CI/CD（GitHub Actions）

`main` ブランチへのpushで自動デプロイされます。

必要なGitHub Secrets:
- `AWS_ROLE_ARN` - OIDC連携用IAMロールARN

## 機能

### 試験一覧
- 試験区分（IS/PM/SA）でフィルタリング
- htmxによる非同期一覧取得

### 問題閲覧・回答
- 2カラムレイアウト（問題文 | 回答入力）
- タブ切替（設問ア/イ/ウ）
- リアルタイム文字数カウント
- ローカルストレージ自動保存
- 試験タイマー（120分）

### AI採点
- Amazon Bedrock (Claude 3.5 Sonnet) による自動採点
- 8観点評価（充足度、具体性、妥当性、一貫性、主張、洞察力、独創性、表現力）
- ランク判定（A〜D）

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/` | 試験一覧ページ |
| `GET` | `/exam/{exam_type}/{problem_id}` | 問題ページ |
| `GET` | `/result/{submission_id}` | 採点結果ページ |
| `GET` | `/api/exams?exam_type=IS` | 試験一覧API |
| `GET` | `/api/exams/detail?exam_type=IS&problem_id=...` | 問題詳細API |
| `POST` | `/api/answers` | 回答保存API |
| `POST` | `/api/scoring` | 採点リクエストAPI |
| `GET` | `/api/scoring/{submission_id}` | 採点結果取得API |
| `GET` | `/health` | ヘルスチェック |

## ライセンス

Private - All rights reserved
