# Scribo アプリケーション概要

## 1. プロジェクト概要
**Scribo** は、情報処理技術者試験（特に高度試験の午後II論述式）の学習・演習を支援するためのWebアプリケーションです。ユーザーは過去問を閲覧し、実際の試験形式に近い環境で論文作成の練習を行うことができます。採点には生成AIを用いて質の高い採点をリアルタイムで行います。

## 2. 技術スタック
最新のReactエコシステムを採用し、パフォーマンスと開発体験を重視した構成になっています。

*   **フレームワーク**: React 19
*   **ビルドツール**: Vite
*   **言語**: TypeScript
*   **UIライブラリ**: Material UI (MUI) v7
*   **ルーティング**: React Router v7
*   **状態管理・データフェッチ**: TanStack Query (React Query) v5
*   **認証**: AWS Cognito (`react-oidc-context`)
*   **その他**: Emotion (スタイリング)

## 3. ディレクトリ構造
機能単位で分割された **Feature-based Architecture** を採用しています。

```text
src/
├── features/           # 機能ごとのモジュール
│   ├── exam/           # 試験一覧・選択機能
│   │   ├── components/ # ExamListなど
│   │   ├── hooks/      # useExamDataなど
│   │   └── types/      # Exam型定義など
│   └── problem/        # 問題演習機能
│       ├── components/ # ProblemViewer, ExamTimerなど
│       ├── hooks/      # useProblemData, useExamTimerなど
│       └── types/      # ProblemData型定義など
├── components/         # 共通UIコンポーネント (Layout, UIパーツ)
├── data/               # マスタデータ・静的データ (master.tsなど)
├── shared/             # 共有フック・ユーティリティ
├── App.tsx             # ルーティング定義・認証ガード
└── main.tsx            # エントリーポイント・プロバイダー設定
```

## 4. 主要機能

### 4.1 認証機能
*   AWS Cognitoを使用したOIDC認証フローを実装。
*   `react-oidc-context` を使用し、トークンの自動更新やセッション管理を行う。
*   未認証ユーザーはサインイン画面へリダイレクトされる。
*   API Gateway ( `/answers`, `/scoring` ) は Cognito User Pool Authorizer を必須化しており、`Authorization: Bearer <id_token>` を検証する。
*   すべてのAPIアクセスは `src/shared/utils/apiClient.ts` を経由し、`Authorization: Bearer <id_token>` ヘッダーを自動付与する。
*   APIが401を返した場合はReact Queryフックが `auth.removeUser()` → `auth.signinRedirect()` を実行し、ユーザーへ再サインインを求める。

### 4.2 試験一覧 (Exam Feature)
*   **コンポーネント**: `ExamListContainer`, `ExamList`
*   **機能**:
    *   試験区分（ITストラテジスト、プロジェクトマネージャ、システムアーキテクト）によるフィルタリング。
    *   年度、時期、問番号などのメタデータ表示。
*   **データ**: `Exam` 型 (`PK`, `SK`, `title` 等) で管理。DynamoDBライクなキー設計が見られる。

### 4.3 問題演習 (Problem Feature)
*   **コンポーネント**: `ProblemViewer`
*   **機能**:
    *   **問題閲覧**: 左ペインに問題文と設問（ア、イ、ウ）を表示。
    *   **回答入力**: 右ペインにMarkdown形式で回答を入力可能。タブ切り替えで設問ごとに記述。
    *   **文字数カウント**: 入力文字数をリアルタイムで表示。
    *   **タイマー**: `ExamTimer` コンポーネントによる試験時間のカウントダウン（一時停止・リセット機能付き）。
    *   **時間切れ通知**: 設定時間経過後にダイアログを表示。

    ### 4.4 採点機能 (Scoring Feature)
    *   **スコアリング**: APIへ答案を送信し、生成AIがIPA ITストラテジスト午後Ⅱの評価基準に沿って採点。
    *   **評価視点**: 設問要求事項の充足度、論述の具体性、内容の妥当性、論理の一貫性、見識に基づく主張、洞察力・行動力、独創性・先見性、表現力・文章作成能力を観点別に評価。
    *   **指示順守**: 問題冊子の「解答に当たっての指示」に従わない場合、内容にかかわらず減点対象。
    *   **コスト監視**: Bedrock API レスポンスの `usage.input_tokens` / `usage.output_tokens` を Lambda が取り出し、推定コスト (Claude 3.5 Sonnet: 入力 $0.003 /1K tokens、出力 $0.015 /1K tokens) を `model_metadata.token_usage` と CloudWatch ログに記録。実行履歴から実際のトークン消費を集計し、初期見積 ($248/月) と比較して乖離があればレートを再調整する。

## 5. データモデル

### 試験データ (Exam)
```typescript
type Exam = {
  PK: string;        // Partition Key
  SK: string;        // Sort Key
  title: string;     // 試験タイトル
  year_term: string; // 年度・期 (例: 2023_Spring)
  exam_type: string; // 試験区分 (例: IS, PM)
  question_id: string;
};
```

### 問題データ (ProblemData)
```typescript
type ProblemData = {
  examCategory: string;    // 試験区分名
  problemTitle: string;    // 問題タイトル
  problemContent: string;  // 問題本文
  problemQuestion: {       // 設問内容
    設問ア: string;
    設問イ: string;
    設問ウ: string;
  };
  // ...その他メタデータ
};
```

## 6. 開発・拡張のポイント
*   **API連携**: 現在はモックデータやJSONファイルを使用している箇所がある可能性があります。`useProblemData` などのフック内で実際のAPIコールへの置き換えが想定されます。
*   **認証エラーハンドリング**: `App.tsx` にて認証状態に応じた詳細なエラーハンドリングとリカバリ処理が実装されています。
*   **UI/UX**: MUIのGridシステムを活用し、PC画面での2カラムレイアウト（問題文 vs 回答欄）を基本としています。

## 7. 採点仕様の参考情報
午後Ⅱ（論述式）試験の評価方法に準拠し、以下を守る必要があります。

### 7.1 評価の視点
- 設問で要求した項目の充足度
- 論述の具体性
- 内容の妥当性
- 論理の一貫性
- 見識に基づく主張
- 洞察力・行動力
- 独創性・先見性
- 表現力・文章作成能力

これらの観点ごとにAIが得点やフィードバックを算出します。問題冊子で示される「解答に当たっての指示」に従わない場合、論述内容にかかわらず違反の程度に応じて評価を下げます。

### 7.2 評価ランクと合否

| 評価ランク | 内容                               | 合否   |
| ----------- | ---------------------------------- | ------ |
| A           | 合格水準にある                     | 合格   |
| B           | 合格水準まであと一歩である         | 不合格 |
| C           | 内容が不十分である / 趣旨から逸脱 | 不合格 |
| D           | 内容が著しく不十分 / 著しく逸脱   | 不合格 |

システム上でもAのみならずB以下のフィードバックを可視化し、学習者が改善点を把握できるようにします。
