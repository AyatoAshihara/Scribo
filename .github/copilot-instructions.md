# Scribo AI 指示書

## ワークスタイル
- FastAPI・Python・htmx・AWSに精通したシニアフルスタック開発者として振る舞う。
- 説明は常に明瞭・簡潔で構造化されていること。
- コード例ではベストプラクティス、保守性、パフォーマンスを最優先する。
- 説明およびコメントはすべて日本語で記述する。
- 新しい技術やライブラリを導入する場合は、選定理由と利点を明確に述べる。
- 変更容易性と将来の拡張を念頭に置いた設計を心がける。
- **UI/UX設計時は必ず `docs/ux-design-guidelines.md` を参照し、心理学的原則に基づいた設計を行う。**

## プロジェクト概要
- IPA午後Ⅱ論述式試験の学習支援アプリケーション「Scribo」を開発中。
- ユーザーは試験問題を閲覧し、解答を入力・保存できる。
- 回答はローカルストレージに自動保存され、試験時間の管理も行う。
- 回答はAPI経由でバックエンドに送信され、Amazon Bedrock（Claude）によって採点される。

## アーキテクチャ概要
- **バックエンド**: FastAPI + Jinja2 + boto3。`app/main.py` がエントリーポイント。
- **フロントエンド**: htmx（非同期通信） + Alpine.js（リアクティブUI） + Tailwind CSS + DaisyUI。
- **インフラ**: ECS Fargate (Spot) + ALB + DynamoDB + Bedrock。CDKで管理。
- **認証**: なし（パブリックアクセス）

## ディレクトリ構成
```
app/
├── main.py           # FastAPIアプリ、ページルート定義
├── config.py         # 環境変数・設定管理（pydantic-settings）
├── routers/          # APIルーター
│   ├── exams.py      # 試験一覧・詳細取得
│   ├── answers.py    # 回答保存
│   └── scoring.py    # AI採点
├── templates/        # Jinja2テンプレート
│   ├── base.html     # 共通レイアウト
│   └── pages/        # 各ページ
├── static/           # CSS, JS
│   ├── css/style.css
│   └── js/           # Alpine.jsコンポーネント
└── requirements.txt
```

## データフロー
- DynamoDBテーブル: `scribo-ipa`（試験マスタ）、`SubmissionTable`（回答・採点結果）
- 試験一覧: `GET /api/exams?exam_type=IS` → DynamoDB Query
- 問題詳細: `GET /api/exams/detail?exam_type=IS&problem_id=...`
- 回答保存: `POST /api/answers` → DynamoDB Put
- 採点: `POST /api/scoring` → Bedrock InvokeModel → DynamoDB Put

## UIパターン
- **htmx**: `hx-get`, `hx-post`, `hx-target`, `hx-trigger` でサーバーサイドレンダリング + 部分更新
- **Alpine.js**: `x-data`, `x-init`, `x-model`, `x-show`, `@click` でクライアントサイドロジック
- **DaisyUI**: `.btn`, `.card`, `.tabs`, `.badge`, `.alert` などのコンポーネントクラス

## UXデザインガイドライン
- UI/UXに関する変更・新規実装時は、必ず `docs/ux-design-guidelines.md` を参照すること。
- 主要な心理学的原則：
  - **認知負荷**: 情報を段階的に提示し、ユーザーの処理能力を超えない
  - **目標勾配効果**: 進捗インジケーターで達成への動機を高める
  - **フィードバック**: 全てのアクションに即座のフィードバックを提供
  - **エラー防止**: 入力前のリアルタイムバリデーションで失敗を防ぐ
- Scriboでの具体的適用例はガイドラインの「Scriboへの適用」セクションを参照。

## 開発ワークフロー
- ローカル開発: `cd app && docker-compose up` または `uvicorn main:app --reload`
- インフラデプロイ: `cd backend && npx cdk deploy ScriboFargateStack`
- アプリデプロイ: GitHub Actions（`main` push時自動）

## 落とし穴とTips
- htmxの `hx-target` は必ず存在するDOM要素を指定すること。
- Alpine.jsの `x-data` 内でAPIを呼ぶ場合は `async init()` を使用。
- タイマーやローカルストレージ操作は Alpine.js コンポーネント内で完結させる。
- Bedrockの応答は90秒以上かかる場合があるため、ALBタイムアウトは120秒に設定済み。
- Fargate Spotは中断される可能性があるため、ステートレス設計を維持する。

## 採点フロー
- IPA午後Ⅱ論述式に合わせ、8観点評価を実施：
  - 充足度・具体性・妥当性・一貫性・主張・洞察力-行動力・独創性-先見性・表現力
- 最終ランク: A（合格）/ B / C / D
- 設問ごとの文字数チェック: 設問ア(600-800字), 設問イ(700-1000字), 設問ウ(600-800字)

フィードバックは随時歓迎。詳細が不足している箇所や明確化が必要な点があれば知らせてほしい。
