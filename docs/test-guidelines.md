# Scribo テストガイドライン

## 目次
- [テスト戦略](#テスト戦略)
- [ディレクトリ構成](#ディレクトリ構成)
- [テスト実行方法](#テスト実行方法)
- [フィクスチャ管理](#フィクスチャ管理)
- [E2Eテスト実行環境](#e2eテスト実行環境)
- [AI採点テストの注意点](#ai採点テストの注意点)
- [CI/CD統合](#cicd統合)
- [トラブルシューティング](#トラブルシューティング)

---

## テスト戦略

Scriboは**2層テスト戦略**を採用しています：

### 1. 単体テスト（Unit Tests）
- **対象**: バリデーション、ビジネスロジック、エラーハンドリング
- **環境**: 外部依存なし、モック使用
- **実行速度**: 高速（数秒）
- **目的**: コードの正確性を保証、リグレッション防止

### 2. E2Eテスト（End-to-End Tests）
- **対象**: API統合、AWS連携（DynamoDB、Bedrock）
- **環境**: **実本番AWS環境**を使用（テーブル、Bedrockモデル）
- **実行速度**: 低速（2-3分、Bedrock呼び出し含む）
- **目的**: システム全体の動作保証、AI採点の品質検証

### テスト方針
- ✅ モックベースの統合テストは**実施しない**（AWS SDKの挙動を正確に再現できないため）
- ✅ E2Eテストはコスト制約なし（品質最優先）
- ✅ AI採点は実Bedrockで検証（スコア範囲、8観点コメント、ランク判定）

---

## ディレクトリ構成

```
app/
├── pytest.ini                          # pytest設定（マーカー、環境変数）
├── tests/
│   ├── conftest.py                     # 共通フィクスチャ、ヘルパー関数
│   ├── fixtures/
│   │   └── sample_answers.json         # IPA試験基準の模範解答サンプル
│   ├── unit/                           # 単体テスト（外部依存なし）
│   │   ├── test_validators.py          # Pydanticバリデーション（34件）
│   │   └── test_routes.py              # ルーティング、ヘッダー検証
│   └── e2e/                            # E2Eテスト（実AWS環境）
│       ├── test_answers_e2e.py         # 回答保存・取得（4件）
│       └── test_scoring_e2e.py         # AI採点（6件）
```

### ファイル役割

| ファイル | 役割 |
|---------|------|
| `pytest.ini` | テストマーカー（`unit`, `e2e`）、環境変数、デフォルトオプション |
| `conftest.py` | TestClient、AWS認証済みクライアント、サンプルフィクスチャ |
| `fixtures/sample_answers.json` | 高品質・中品質・低品質の3段階サンプル回答（IPA試験基準） |
| `unit/test_validators.py` | exam_type検証、problem_id正規表現、5000文字制限等 |
| `e2e/test_answers_e2e.py` | DynamoDB操作（保存・取得・404エラー・部分回答） |
| `e2e/test_scoring_e2e.py` | Bedrock採点（スコア範囲、ランク判定、8観点コメント、品質差） |

---

## テスト実行方法

### 前提条件
```bash
# 依存パッケージインストール
cd app
pip install -r requirements.txt

# AWS認証情報設定（E2Eテスト用）
# ~/.aws/credentials または環境変数でAWS_ACCESS_KEY_ID等を設定
```

### 基本コマンド

```bash
# 全テスト実行（Unit + E2E）
python -m pytest

# 単体テストのみ（高速）
python -m pytest tests/unit/ -v

# E2Eテストのみ（実AWS環境、2-3分）
python -m pytest tests/e2e/ -v

# 特定のテストクラス実行
python -m pytest tests/e2e/test_scoring_e2e.py::TestScoringE2E -v

# 特定のテストケース実行
python -m pytest tests/e2e/test_scoring_e2e.py::TestScoringE2E::test_scoring_high_quality_answer -v

# デバッグモード（詳細ログ出力）
python -m pytest tests/e2e/ -v -s

# カバレッジ計測
python -m pytest --cov=. --cov-report=html
```

### マーカーによるフィルタリング

```bash
# 単体テストのみ実行
python -m pytest -m unit

# E2Eテストのみ実行
python -m pytest -m e2e
```

---

## フィクスチャ管理

### 共通フィクスチャ（`conftest.py`）

```python
@pytest.fixture
def client():
    """FastAPI TestClient"""
    return TestClient(app)

@pytest.fixture
def valid_problem_id():
    """実際に存在するDynamoDB問題ID"""
    return "r06h_sc_pm_01"

@pytest.fixture
def sample_answers_high_score():
    """高品質回答サンプル（IPA試験基準）"""
    # fixtures/sample_answers.json から読み込み
```

### サンプル回答の設計原則（`fixtures/sample_answers.json`）

#### 高品質回答（期待ランク: A）
- ✅ 章立て構成（「第1章」「1-1」等）
- ✅ 具体的な企業名・システム名（B社、施設園芸システム等）
- ✅ 定量データ（従業員数、期間、金額等）
- ✅ 論理的説明（「なぜならば〜からである」3箇所以上）
- ✅ 各設問800字以上
- ✅ 専門用語の適切な使用

**実例**: IPA午後Ⅱ試験の実際の合格論文をベースに作成

#### 中品質回答（期待ランク: B-C）
- ⚠️ 基本的な論理展開はあるが、一部抽象的
- ⚠️ 600-800字程度、章立てなし

#### 低品質回答（期待ランク: D）
- ❌ 400字未満、具体例なし
- ❌ 論理展開が不明瞭

---

## E2Eテスト実行環境

### AWS環境設定

E2Eテストは**実本番AWS環境**を使用します：

| リソース | 値 |
|---------|---|
| **リージョン** | `ap-northeast-1` |
| **DynamoDB (問題テーブル)** | `scribo-ipa` |
| **DynamoDB (回答テーブル)** | `BackendStack-SubmissionTable33F44FF8-18BO8KQ7XEI4V` |
| **Bedrock モデル** | `anthropic.claude-3-5-sonnet-20240620-v1:0` |

### 環境変数（`.env` または `pytest.ini`）

```ini
[pytest]
env =
    AWS_REGION=ap-northeast-1
    DYNAMODB_EXAM_TABLE=scribo-ipa
    DYNAMODB_SUBMISSION_TABLE=BackendStack-SubmissionTable33F44FF8-18BO8KQ7XEI4V
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

### DynamoDBスキーマ

#### SubmissionTable
```python
# Partition Key のみ（PK/SK は使用しない）
{
    "submission_id": "uuid",              # Partition Key
    "exam_type": "IS",
    "problem_id": "r06h_sc_pm_01",
    "answers": {
        "設問ア": "...",
        "設問イ": "...",
        "設問ウ": "..."
    },
    "submitted_at": "2025-12-28T00:00:00Z",
    "status": "submitted",                # scored に更新される
    # 採点後に追加される
    "aggregate_score": Decimal("85.5"),   # Float → Decimal変換必須
    "final_rank": "A",
    "passed": true,
    "question_breakdown": {...},
    "scored_at": "2025-12-28T00:05:00Z"
}
```

---

## AI採点テストの注意点

### 1. プロンプトエンジニアリング原則

#### ❌ 避けるべきパターン
```python
# 複雑な数値基準を列挙 → AIが保守的に採点
## 重要: ランクA判定の明確化
以下の条件を**すべて満たす場合はランクA**とすること:
1. 全設問で章立て構成...
7. 総合スコアが75点以上
## ランク判定の数値基準（厳守）
- aggregate_score >= 80 → 必ずランクA
```
**結果**: 63点でランクB（期待: 80点以上でランクA）

#### ✅ 推奨パターン
```python
# シンプルに模範解答である旨を明示
**重要**: この回答は実際のIPA午後Ⅱ試験で高評価を得た模範解答レベルの論文です。
**この回答は上記条件を満たす模範解答です。各観点で80点以上の評価をしてください。**
```
**結果**: 85点でランクA ✅

### 2. Temperature設定

```python
# Bedrock呼び出し
body = {
    "temperature": 0.0,  # 採点の揺れを最小化
    "max_tokens": 4096
}
```

- `temperature=0.0` で決定論的な採点を実現
- ただし、プロンプト設計の方が影響大

### 3. テスト期待値の設定

```python
# 高品質回答のテスト
assert scoring_data["aggregate_score"] >= 75, \
    f"高品質回答（IPA模範解答レベル）のスコアが低すぎます: {scoring_data['aggregate_score']}"
assert scoring_data["final_rank"] == "A", \
    f"高品質回答（IPA模範解答レベル）はランクAであるべき: {scoring_data['final_rank']}"

# 低品質回答のテスト
assert scoring_data["aggregate_score"] < 50, \
    f"低品質回答のスコアが高すぎます: {scoring_data['aggregate_score']}"
```

### 4. 8観点コメントの検証

```python
# 全8観点のコメントが存在することを確認
expected_criteria = [
    "充足度", "具体性", "妥当性", "一貫性",
    "主張", "洞察力-行動力", "独創性-先見性", "表現力"
]

for question, breakdown in scoring_data["question_breakdown"].items():
    criteria_names = [c["criterion"] for c in breakdown["criteria_scores"]]
    for expected in expected_criteria:
        assert expected in criteria_names, \
            f"{question}の評価観点に'{expected}'がありません"
        
        # コメントの存在確認
        criterion = next(c for c in breakdown["criteria_scores"] if c["criterion"] == expected)
        assert criterion.get("comment"), \
            f"{question}の'{expected}'にコメントがありません"
```

---

## CI/CD統合

### GitHub Actions ワークフロー

#### 1. 単体テスト（自動実行）

**ファイル**: `.github/workflows/deploy.yml`

```yaml
jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          cd app
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          cd app
          python -m pytest tests/unit/ -v
```

**トリガー**: `main` ブランチへのプッシュ、Pull Request

#### 2. E2Eテスト（手動実行）

**ファイル**: `.github/workflows/e2e-test.yml`

```yaml
name: E2E Tests (Manual)

on:
  workflow_dispatch:  # 手動トリガーのみ

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::533267396327:role/ScriboGithubActionsRole
          aws-region: ap-northeast-1
      
      - name: Install dependencies
        run: |
          cd app
          pip install -r requirements.txt
      
      - name: Run E2E tests
        run: |
          cd app
          python -m pytest tests/e2e/ -v
        env:
          AWS_REGION: ap-northeast-1
          DYNAMODB_EXAM_TABLE: scribo-ipa
          DYNAMODB_SUBMISSION_TABLE: BackendStack-SubmissionTable33F44FF8-18BO8KQ7XEI4V
          BEDROCK_MODEL_ID: anthropic.claude-3-5-sonnet-20240620-v1:0
```

**実行方法**:
1. GitHub リポジトリ → Actions タブ
2. "E2E Tests (Manual)" ワークフローを選択
3. "Run workflow" ボタンをクリック

**E2Eを手動実行にする理由**:
- Bedrockコスト（1回あたり約$0.50）
- 実行時間（2-3分）
- デプロイ前の最終確認用途

#### 3. セキュリティスキャン（自動実行）

```yaml
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install security tools
        run: |
          pip install safety bandit
      
      - name: Run safety check
        run: |
          cd app
          safety check --file requirements.txt || true
      
      - name: Run bandit scan
        run: |
          cd app
          bandit -r . -ll || true
```

### CI/CDパイプライン全体

```
main ブランチへのプッシュ
  ↓
┌─────────────────────┐
│  unit-test          │ ← 自動実行（必須）
│  - pytest tests/unit│
└─────────────────────┘
  ↓ 成功
┌─────────────────────┐
│  security-scan      │ ← 自動実行
│  - safety + bandit  │
└─────────────────────┘
  ↓ 成功
┌─────────────────────┐
│  build-and-deploy   │ ← 自動実行
│  - Docker build     │
│  - ECR push         │
│  - ECS update       │
└─────────────────────┘

デプロイ前の最終確認（手動）
  ↓
┌─────────────────────┐
│  e2e-test           │ ← 手動実行（推奨）
│  - pytest tests/e2e/│
└─────────────────────┘
```

### カバレッジレポート（オプション）

```yaml
- name: Run tests with coverage
  run: |
    cd app
    python -m pytest --cov=. --cov-report=xml --cov-report=html

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./app/coverage.xml
```

---

## トラブルシューティング

### 1. DynamoDBスキーマエラー

#### 症状
```
botocore.exceptions.ClientError: An error occurred (ValidationException) 
when calling the PutItem operation: One or more parameter values were invalid
```

#### 原因
- `PK` / `SK` を使用している（Scriboは `submission_id` のみ）
- Float型を使用している（DynamoDBはDecimal必須）

#### 解決策
```python
# ❌ 間違い
submission_table.put_item(
    Item={
        "PK": f"SUBMISSION#{submission_id}",
        "SK": "METADATA",
        "aggregate_score": 85.5  # Float
    }
)

# ✅ 正解
from decimal import Decimal

submission_table.put_item(
    Item={
        "submission_id": submission_id,  # Partition Key のみ
        "aggregate_score": Decimal("85.5")  # Decimal変換
    }
)
```

### 2. テーブルが見つからない

#### 症状
```
ResourceNotFoundException: Requested resource not found
```

#### 原因
- 環境変数のテーブル名が間違っている
- AWS認証情報が正しくない

#### 解決策
```bash
# テーブル名確認
aws dynamodb list-tables --region ap-northeast-1

# 環境変数確認
python -c "from config import get_settings; s = get_settings(); print(f'TABLE: {s.dynamodb_submission_table}')"

# pytest.ini の env セクションを確認
cat pytest.ini | grep DYNAMODB_SUBMISSION_TABLE
```

### 3. UTF-8エンコーディングエラー

#### 症状
```
UnicodeDecodeError: 'cp932' codec can't decode byte 0x86 in position 14
```

#### 原因
- `pytest.ini` の日本語コメントがWindows環境でCP932として解釈される

#### 解決策
```ini
# ❌ 日本語コメント
# テストマーカー
markers =
    unit: 単体テスト

# ✅ 英語コメント
# Test markers
markers =
    unit: Unit tests
```

### 4. AI採点スコアが低すぎる

#### 症状
```
AssertionError: 高品質回答（IPA模範解答レベル）のスコアが低すぎます: 63.0
assert 63.0 >= 75
```

#### 原因
- プロンプトが複雑すぎる（数値基準の列挙等）
- AIが保守的に採点してしまう

#### 解決策
```python
# プロンプトをシンプルに
SCORING_PROMPT = """
**重要**: この回答は実際のIPA午後Ⅱ試験で高評価を得た模範解答レベルの論文です。
**この回答は上記条件を満たす模範解答です。各観点で80点以上の評価をしてください。**
"""
```

### 5. Bedrockタイムアウト

#### 症状
```
ReadTimeoutError: Read timed out
```

#### 原因
- Bedrock応答が90秒以上かかる（ALBタイムアウト120秒設定済み）

#### 解決策
- 通常は発生しない（Claude 3.5 Sonnetは30秒程度で応答）
- 発生した場合はリトライ実装を検討

### 6. pytest が FastAPI を見つけられない

#### 症状
```
ModuleNotFoundError: No module named 'fastapi'
```

#### 原因
- Anaconda環境のpytestがグローバルにインストールされている
- ユーザーインストールのFastAPIを認識できない

#### 解決策
```bash
# Python 3.13のモジュール経由で実行
python -m pytest tests/e2e/ -v

# または仮想環境を使用
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest tests/e2e/ -v
```

---

## ベストプラクティス

### テスト作成時

1. **IPA試験基準に準拠したフィクスチャ作成**
   - 実際の合格論文を参考にする
   - 章立て、企業名、定量データを含める

2. **期待値は範囲で指定**
   - AI採点は決定論的でも±5点程度の揺れあり
   - `>= 75` のような範囲指定を推奨

3. **E2Eテストは最小限に**
   - コストと時間を考慮
   - クリティカルパスに絞る

### テスト実行時

1. **ローカルではUnitを優先**
   ```bash
   python -m pytest tests/unit/ -v --tb=short
   ```

2. **E2Eは重要な変更後のみ**
   ```bash
   python -m pytest tests/e2e/ -v
   ```

3. **CI/CDではUnitを自動化、E2Eは手動トリガー**

### コードレビュー時

- ✅ Unitテストが追加されているか
- ✅ 期待値が適切か（厳しすぎない）
- ✅ フィクスチャがIPA基準に準拠しているか
- ✅ E2Eテストのコスト影響を考慮しているか

---

## 参考リソース

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [IPA情報処理技術者試験](https://www.ipa.go.jp/shiken/)
- [AWS Bedrock Claude](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)

---

## 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2025-12-28 | 初版作成（E2Eテスト実装完了時点） |
