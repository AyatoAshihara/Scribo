# Scribo 開発ロードマップ (The Strategist's Forge)

本ドキュメントは、Scriboを「ITストラテジスト合格のための戦略的執筆トレーニングプラットフォーム」へと進化させるための開発タスクを管理します。

## Phase 0: 基盤刷新 (Material Design & Architecture)

- [x] **UIデザイン刷新 (Material Design 3)**
    - [x] `docs/ui-design-guidelines.md` に基づき、Tailwind/DaisyUI設定を更新
    - [x] `templates/base.html` のレイアウトをMaterial Design (Navigation Rail/Drawer) に変更
    - [x] フォント (Roboto/Noto Sans JP) とアイコン (Material Symbols) の導入
    - [x] 既存ページ (`index.html`, `problem.html`, `result.html`) のコンポーネントをMaterial化

- [x] **データモデル拡張**
    - [x] `modules` テーブル設計 (背景、課題、解決策などのネタ管理)
    - [x] `designs` テーブル設計 (論文設計図管理)
    - [x] DynamoDBスキーマ定義の更新 (`backend/lib/scribo-fargate-stack.ts`)

## Phase 1: 資産化フェーズ (Asset Preparation)

- [x] **準備モジュール管理機能**
    - [x] `GET /modules` - モジュール一覧画面
    - [x] `POST /api/modules` - モジュール作成・編集API
    - [x] モジュール作成UI (CRUD) の実装
    - [x] テンプレートデータの投入 (ビル管理、電力会社などのFew-shot)

- [x] **AIリライティング機能**
    - [x] `POST /api/modules/rewrite` - AIによる専門用語変換API
    - [x] 「平易な表現」→「論文用語」変換プロンプトの実装
    - [x] モジュール編集画面へのAIリライトボタン統合

## Phase 2: 設計フェーズ (Strategic Planning)

- [x] **論文設計ウィザード**
    - [x] `GET /design/{exam_id}` - 設計画面
    - [x] 設問分解UI (ドラッグ＆ドロップで設問要素を抽出)
    - [x] 章構成ビルダー (1.1, 1.2... の骨子作成)
    - [x] モジュールマッピング (作成済みモジュールを章に割り当て)

- [ ] **設計書プレビュー**
    - [ ] 設計完了後の全体像確認画面
    - [ ] 「執筆開始」ボタンの制御 (設計完了までロック)

## Phase 3: 執筆・評価フェーズ (Execution & Feedback)

- [ ] **執筆画面 (Editor) の高度化**
    - [ ] スプリットビュー実装 (左: 設計図・モジュール / 右: エディタ)
    - [ ] ドラッグ＆ドロップ引用機能
    - [ ] リアルタイムバリデーター (行頭句読点、行空け検知)
    - [ ] ペース配分タイマー (構想/執筆/見直しのフェーズ管理)

- [ ] **採点ロジックの刷新**
    - [ ] `docs/ITストラテジスト試験 論文対策ノウハウ/9_論文自己評価ガイドライン.md` に基づくプロンプト作成
    - [ ] 減点方式 (レベル1〜5) の実装
    - [ ] 採点レポートUIの改善 (合格ランク、減点詳細表示)

## 完了済み (Legacy) ✅

- [x] **FastAPIプロジェクト基盤作成**
- [x] **基本APIエンドポイント実装**
- [x] **CDK Fargateインフラ定義**
- [x] **GitHub Actions CI/CD構築**

