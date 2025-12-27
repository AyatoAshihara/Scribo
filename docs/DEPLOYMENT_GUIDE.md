# Scribo デプロイガイド

## 概要

このドキュメントでは、Scriboアプリケーションのデプロイ手順を説明します。

**本番URL:** http://scribo-alb-760941679.ap-northeast-1.elb.amazonaws.com/

---

## デプロイ方式

### 自動デプロイ（推奨）

GitHub Actionsによる自動CI/CDパイプラインが設定されています。

| トリガー | 対象ファイル | 処理 |
|---------|-------------|------|
| `main` push | `app/**` | Docker ビルド → ECR → ECS |
| `main` push | `backend/lib/**` | CDK deploy |

**手順:**
1. 変更をコミット
2. `main`ブランチにプッシュ
3. GitHub Actions が自動実行

```bash
git add .
git commit -m "feat: Add new feature"
git push origin main
```

**デプロイ状況の確認:**
```bash
# GitHub CLIで確認
gh run list --limit 5
gh run view <run_id>

# または GitHub Web UI
# https://github.com/AyatoAshihara/Scribo/actions
```

---

## 初回セットアップ

### 前提条件

- AWS CLI 設定済み
- Node.js 18+ インストール済み
- Docker インストール済み
- GitHub リポジトリへのアクセス権

### 1. CDKスタックのデプロイ

```bash
cd backend

# 依存関係インストール
npm install

# CDK Bootstrap（初回のみ）
npx cdk bootstrap

# ECRスタックをデプロイ
npx cdk deploy ScriboEcrStack

# GitHub OIDCスタックをデプロイ
npx cdk deploy ScriboGitHubOidcStack

# Fargateスタックをデプロイ
npx cdk deploy ScriboFargateStack
```

### 2. GitHub Secretsの設定

GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定:

| Secret名 | 値 |
|---------|-----|
| `AWS_ROLE_ARN` | `arn:aws:iam::152489143901:role/github-actions-scribo-role` |

### 3. 初回イメージのビルド

GitHub Actions の `initial-build.yml` を手動実行するか、以下を実行:

```bash
# ローカルでビルド＆プッシュ
cd app
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 152489143901.dkr.ecr.ap-northeast-1.amazonaws.com

docker build -t scribo-app .
docker tag scribo-app:latest 152489143901.dkr.ecr.ap-northeast-1.amazonaws.com/scribo-app:latest
docker push 152489143901.dkr.ecr.ap-northeast-1.amazonaws.com/scribo-app:latest
```

---

## ローカル開発

### 起動方法

```bash
cd app

# 仮想環境作成（初回のみ）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 依存関係インストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn main:app --reload --port 8000
```

**アクセス:** http://localhost:8000

### Docker Compose（推奨）

```bash
cd app
docker-compose up
```

### 環境変数

`.env` ファイルを作成（オプション）:

```env
AWS_REGION=ap-northeast-1
DYNAMODB_EXAM_TABLE=scribo-ipa
DYNAMODB_SUBMISSION_TABLE=SubmissionTable
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
DEBUG=true
```

---

## インフラ変更

### CDKスタックの更新

```bash
cd backend

# 差分確認
npx cdk diff ScriboFargateStack

# デプロイ
npx cdk deploy ScriboFargateStack
```

### 主要なスタック

| スタック | 説明 | 変更時の影響 |
|---------|------|------------|
| ScriboEcrStack | ECRリポジトリ | 低（基本変更不要） |
| ScriboGitHubOidcStack | GitHub OIDC認証 | 低 |
| ScriboFargateStack | VPC, ECS, ALB | 高（サービス再起動） |

---

## ロールバック

### ECSタスク定義のロールバック

```bash
# 過去のタスク定義を確認
aws ecs list-task-definitions --family-prefix ScriboFargateStack

# 特定のリビジョンに戻す
aws ecs update-service \
  --cluster scribo-cluster \
  --service scribo-service \
  --task-definition ScriboFargateStackScriboTaskDef699F64BA:3
```

### Gitでのロールバック

```bash
# コミットを確認
git log --oneline

# 特定のコミットに戻す
git revert <commit_hash>
git push origin main
```

---

## トラブルシューティング

### デプロイ失敗時

1. **ECS Circuit Breaker発動**
   ```bash
   # タスクログを確認
   aws logs tail /ecs/scribo-app --follow
   ```

2. **イメージプッシュ失敗**
   ```bash
   # ECRログイン
   aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 152489143901.dkr.ecr.ap-northeast-1.amazonaws.com
   ```

3. **ヘルスチェック失敗**
   - ALBターゲットグループでステータス確認
   - `/health` エンドポイントが応答するか確認

### よくあるエラー

| エラー | 原因 | 対処 |
|-------|------|------|
| `ResourceNotFoundException` | DynamoDBテーブル未作成 | テーブル名を確認 |
| `AccessDeniedException` | IAM権限不足 | タスクロールを確認 |
| `Bedrock timeout` | 採点処理が120秒超過 | ALBタイムアウト確認 |
| `S3 Access Denied` | S3読み取り権限なし | バケットポリシー確認 |

---

## 運用コマンド

### サービス状態確認

```bash
# ECSサービス状態
aws ecs describe-services \
  --cluster scribo-cluster \
  --services scribo-service

# タスク一覧
aws ecs list-tasks --cluster scribo-cluster

# CloudWatch Logs
aws logs tail /ecs/scribo-app --follow
```

### 手動スケーリング

```bash
# タスク数を変更
aws ecs update-service \
  --cluster scribo-cluster \
  --service scribo-service \
  --desired-count 2
```

---

## CI/CD ワークフロー詳細

### deploy.yml

```yaml
トリガー: main push (app/**)
処理:
  1. Docker ビルド
  2. ECR にプッシュ
  3. タスク定義を更新
  4. ECS サービスをデプロイ
  5. 安定化を待機
```

### cdk-deploy.yml

```yaml
トリガー: main push (backend/lib/**)
処理:
  1. npm install
  2. cdk diff
  3. cdk deploy --require-approval never
```

---

## 関連ドキュメント

- [アーキテクチャ](./ARCHITECTURE.md)
- [API仕様書](./API_SPECIFICATION.md)
- [採点API詳細](./SCORING_API.md)
