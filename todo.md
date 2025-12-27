# Scribo 開発 TODO リスト

このドキュメントは、FastAPI + htmx 構成のScriboアプリケーションの開発タスクを管理します。

## 完了済み ✅

- [x] **FastAPIプロジェクト基盤作成**
    - [x] `app/main.py` - エントリーポイント
    - [x] `app/config.py` - 設定管理
    - [x] `app/requirements.txt` - 依存関係
    - [x] `app/Dockerfile` - コンテナ定義
    - [x] `app/docker-compose.yml` - ローカル開発環境

- [x] **APIエンドポイント実装**
    - [x] `GET /api/exams` - 試験一覧取得
    - [x] `GET /api/exams/detail` - 問題詳細取得
    - [x] `POST /api/answers` - 回答保存
    - [x] `POST /api/scoring` - AI採点リクエスト
    - [x] `GET /api/scoring/{submission_id}` - 採点結果取得

- [x] **UI画面構築（htmx + Alpine.js）**
    - [x] `templates/base.html` - 共通レイアウト
    - [x] `templates/pages/index.html` - 試験一覧ページ
    - [x] `templates/pages/problem.html` - 問題閲覧・回答ページ
    - [x] `templates/pages/result.html` - 採点結果ページ
    - [x] `static/js/timer.js` - タイマーコンポーネント
    - [x] `static/js/problem.js` - 問題ビューアコンポーネント
    - [x] `static/js/result.js` - 結果表示コンポーネント

- [x] **CDK Fargateインフラ定義**
    - [x] `backend/lib/scribo-fargate-stack.ts` - ECS Fargate + ALB構成
    - [x] `backend/bin/scribo-fargate.ts` - CDKアプリ定義

- [x] **GitHub Actions CI/CD構築**
    - [x] `.github/workflows/deploy.yml` - アプリデプロイ
    - [x] `.github/workflows/deploy-infra.yml` - インフラデプロイ

- [x] **既存React srcフォルダ削除**

## 優先度: 高 (次のステップ)

- [ ] **ローカル動作確認**
    - [ ] `docker-compose up` でアプリ起動確認
    - [ ] DynamoDBテーブルとの接続確認
    - [ ] 試験一覧・問題詳細の表示確認

- [ ] **初回インフラデプロイ**
    - [ ] `cdk deploy ScriboFargateStack` 実行
    - [ ] ECRリポジトリへの初回イメージプッシュ
    - [ ] ALB経由でのアクセス確認

- [ ] **GitHub Actions設定**
    - [ ] AWS OIDC連携用IAMロール作成
    - [ ] `AWS_ROLE_ARN` シークレット設定

## 優先度: 中 (機能拡充)

- [ ] **採点結果のストリーミング表示**
    - [ ] SSE (Server-Sent Events) でリアルタイム採点進捗を表示
    - [ ] htmx SSE拡張の導入

- [ ] **学習履歴機能**
    - [ ] 過去の回答一覧ページ (`/history`)
    - [ ] 回答詳細・再採点ページ (`/history/{submission_id}`)

- [ ] **UIの改善**
    - [ ] ダークモード対応
    - [ ] レスポンシブ対応の強化
    - [ ] キーボードショートカット

## 優先度: 低 (将来検討)

- [ ] **HTTPS対応**
    - [ ] ACM証明書の取得
    - [ ] Route 53でカスタムドメイン設定
    - [ ] ALBリスナーをHTTPS化

- [ ] **監視・アラート**
    - [ ] CloudWatch Alarms設定
    - [ ] エラー通知（SNS/Slack）

- [ ] **パフォーマンス最適化**
    - [ ] CloudFrontによるキャッシュ
    - [ ] 静的ファイルのS3配信
