# Scoring API Contract

Scribo の採点機能は IPA ITストラテジスト 午後Ⅱ（論述式）の評価観点を再現し、**設問単位で 8 観点の合計が 100 点**になる配点設計です。トップレベルの観点一覧は持たず、`question_breakdown.{設問}.criteria_scores[]` に統一。各設問で **同一の 8 観点**（充足度 / 論述の具体性 / 内容の妥当性 / 論理の一貫性 / 見識に基づく主張 / 洞察力・行動力 / 独創性・先見性 / 表現力・文章作成能力）を必ず評価します。

## 0. 概念モデル
| レイヤ | 目的 | 主フィールド | 備考 |
| ------ | ---- | ------------ | ---- |
| 提出 (Submission) | 一回の答案送信識別 | `submission_id`, `problem_id` | 冪等性確保 |
| 設問 (Question) | 設問ごとの合成評価 | `level`, `question_score`, `word_count` | A/B/C/D 段階（0–100点） |
| 観点 (Criterion) | 詳細評価要素 | `criterion`, `weight`, `points`, `comment` | points は 0–weight（weight 合計100） |
| 集計 (Aggregate) | 合否判定用 | `aggregate_score`, `final_rank`, `passed` | ランクは IPA 規定 |
| 指示遵守 (Compliance) | 減点要因管理 | `instruction_compliance.followed`, `violations[]` | 重大違反で降格可 |

### スコア算出の流れ
1. 各設問で 8 観点を評価し `criteria_scores[]` を生成。
2. 各観点には配点 `weight`（合計100）が割り当てられる。サーバーは各観点の到達度に応じて `points`（0–weight）を付与。
3. 設問スコア `question_score` は各観点の `points` 合計（0–100点）。
4. 設問ア/イ/ウに 4:8:6 のウェイトを適用して加重平均し `aggregate_score` を算出。
5. 閾値に基づき `final_rank` (A–D) を決定。Aのみ `passed=true`。違反がある場合は降格規則を適用（軽微=影響なし / 中程度=1段階 / 重大=直接D）。

## 1. Endpoint
- `POST https://0pq03jbmag.execute-api.ap-northeast-1.amazonaws.com/scribo/scoring`
- 認証: `Authorization: Bearer <id_token>` (`useAuth()` が提供)
- 冪等性: `submission_id` を UUID で発行し、再送時も同じ ID を送る

## 2. Request Payload
```jsonc
{
  "exam_type": "IS",
  "problem_id": "2024_Spring_Q1",
  "submission_id": "uuid-v4",
  "submitted_at": "2025-11-22T12:34:56.789Z",
  "answers": {
    "設問ア": "...markdown...",
    "設問イ": "...",
    "設問ウ": "..."
  },
  "instruction_compliance": {
    "followed": true,
    "violations": []
  },
  "metadata": {
    "exam_term": "令和6年度春期",
    "exam_session": "午後Ⅱ",
    "timer_seconds_used": 4200,
    "word_counts": {
      "設問ア": 820,
      "設問イ": 760,
      "設問ウ": 810
    },
    "client_version": "web-0.0.0"
  }
}
```
- `instruction_compliance.followed` が `false` の場合は `violations` に違反内容を列挙（例: "指定文字数未満"）。

## 3. Response Payload（設問別観点のみ）
```jsonc
{
  "submission_id": "uuid-v4",
  "problem_id": "2024_Spring_Q1",
  "instruction_compliance": {
    "followed": true,
    "violations": []
  },
  "question_breakdown": {
    "設問ア": {
      "level": "B",
      "question_score": 68,
      "word_count": 820,
      "criteria_scores": [
        { "criterion": "充足度", "weight": 20, "points": 16, "comment": "要求事項を概ね網羅" },
        { "criterion": "論述の具体性", "weight": 15, "points": 9, "comment": "数値的根拠が弱い" },
        { "criterion": "内容の妥当性", "weight": 15, "points": 12, "comment": "対策との整合良好" },
        { "criterion": "論理の一貫性", "weight": 15, "points": 9, "comment": "段落接続が弱い" },
        { "criterion": "見識に基づく主張", "weight": 10, "points": 8, "comment": "経験記述妥当" },
        { "criterion": "洞察力・行動力", "weight": 10, "points": 6, "comment": "リスク対応が浅い" },
        { "criterion": "独創性・先見性", "weight": 5, "points": 2, "comment": "一般的施策" },
        { "criterion": "表現力・文章作成能力", "weight": 10, "points": 6, "comment": "語尾表現が単調" }
      ]
    },
    "設問イ": {
      "level": "B",
      "question_score": 75,
      "word_count": 760,
      "criteria_scores": [
        { "criterion": "充足度", "weight": 20, "points": 16, "comment": "要求範囲に概ね対応" },
        { "criterion": "論述の具体性", "weight": 15, "points": 12, "comment": "具体事例と数値あり" },
        { "criterion": "内容の妥当性", "weight": 15, "points": 12, "comment": "手段と効果が整合" },
        { "criterion": "論理の一貫性", "weight": 15, "points": 12, "comment": "流れ自然" },
        { "criterion": "見識に基づく主張", "weight": 10, "points": 8, "comment": "過去経験引用適切" },
        { "criterion": "洞察力・行動力", "weight": 10, "points": 6, "comment": "リスク軽減策が浅い" },
        { "criterion": "独創性・先見性", "weight": 5, "points": 3, "comment": "業界標準的" },
        { "criterion": "表現力・文章作成能力", "weight": 10, "points": 6, "comment": "構成明瞭も語彙平板" }
      ]
    },
    "設問ウ": {
      "level": "A",
      "question_score": 83,
      "word_count": 810,
      "criteria_scores": [
        { "criterion": "充足度", "weight": 20, "points": 20, "comment": "全要求網羅" },
        { "criterion": "論述の具体性", "weight": 15, "points": 12, "comment": "具体手順と指標" },
        { "criterion": "内容の妥当性", "weight": 15, "points": 12, "comment": "妥当性高い" },
        { "criterion": "論理の一貫性", "weight": 15, "points": 12, "comment": "構成滑らか" },
        { "criterion": "見識に基づく主張", "weight": 10, "points": 8, "comment": "業務知識反映" },
        { "criterion": "洞察力・行動力", "weight": 10, "points": 8, "comment": "改善サイクル記述" },
        { "criterion": "独創性・先見性", "weight": 5, "points": 3, "comment": "新規視点一部" },
        { "criterion": "表現力・文章作成能力", "weight": 10, "points": 8, "comment": "冗長なし" }
      ]
    }
  },
  "aggregate_score": 76.11,  // (68*4 + 75*8 + 83*6) / 18 = 76.11
  "final_rank": "A",
  "passed": true,
  "feedback": {
    "strengths": ["要求事項の網羅", "経験知に基づく主張"],
    "improvements": ["独創性の裏付け強化"],
    "notes": "タイマー残り 10 分で送信"
  },
  "model_metadata": {
    "engine": "gpt-4o-mini",
    "latency_ms": 1833,
    "confidence": 0.82
  }
}
```

### 3.1 評価・ランク判定
- **設問評価**: 各設問 8 観点は配点 weight（合計100）で構成し、観点ごとの到達度に応じて `points`（0–weight）を付与。合計を `question_score`（0–100）とする。
- **集計ウェイト 4:8:6**: `aggregate_score = Σ(question_score_i * weight_i) / Σweight`。
  - 例: (68×4 + 75×8 + 83×6) / 18 = 76.11 → A。
- **ランク閾値（例）**: A≥70, B≥60, C≥50, D<50。（調整可能）
- **合格条件**: `final_rank === 'A'`。
- **降格条件**: 重大指示違反 / 設問D含む場合A不可 / B以上設問が2未満ならA不可。
- **冪等性**: 同一 `submission_id` は再計算せずキャッシュ返却。

#### Worked Example（実数での算出例）
- 観点配点（合計100の一例）:
  - 充足度 20, 論述の具体性 15, 内容の妥当性 15, 論理の一貫性 15, 見識に基づく主張 10, 洞察力・行動力 10, 独創性・先見性 5, 表現力・文章作成能力 10
- 設問ア points: 16, 9, 12, 9, 8, 6, 2, 6 → 合計 68
- 設問イ points: 16, 12, 12, 12, 8, 6, 3, 6 → 合計 75
- 設問ウ points: 20, 12, 12, 12, 8, 8, 3, 8 → 合計 83
- 集計（4:8:6）: (68×4 + 75×8 + 83×6) / 18 = 76.11 → A（A≥70）
- 丸め方針: 内部はフル精度保持。`question_score` は整数表示、`aggregate_score` は小数2桁表示を推奨。

### 3.1.1 フィールド相互関係
| フィールド | 由来 | 依存 | 用途 |
| ---------- | ---- | ---- | ---- |
| `criteria_scores[].weight` | 観点配点（合計100） | ルーブリック | 比重の明示 |
| `criteria_scores[].points` | 観点得点（0–weight） | weight | 設問合計への寄与 |
| `question_breakdown.{設問}.question_score` | 観点points合計 | `criteria_scores[]` | 設問総合力 |
| `aggregate_score` | 重み付正規化 | question_score 群 | ランク判定 |
| `final_rank` | 規則適用 | aggregate_score + compliance | 合否表示 |
| `passed` | ランク | final_rank | 合格フラグ |
| `demotion_reasons` | 判定ロジック | compliance + levels | 改善要素提示 |
| `instruction_compliance` | 指示遵守解析 | 送信メタ | 降格トリガ |

### 3.2 エラーレスポンス
| Status | Body例 | 対応 |
| ------ | ------ | ---- |
| 401 | `{ "message": "invalid token" }` | 再認証 (`auth.signinRedirect()`) |
| 409 | `{ "message": "duplicate submission" }` | `submission_id` を変えずに結果ポーリング |
| 422 | `{ "errors": { "answers.設問イ": "600字以上で記述" } }` | UIで対象タブをハイライト |
| 429/5xx | `{ "message": "try later" }` | React Query の再試行/バックオフ |

## 4. 実装メモ
- React Query mutation 名: `useScoreSubmission`（成功時 draft をクリア）。
- UI: 設問タブ内で 8 観点一覧（points/weight）+ 設問総合点。全体で総合得点とランク、指示違反表示。
- キャッシュ: 採点結果は不変とみなし `staleTime: Infinity` 検討。履歴表示向け GET 実装を後続。
- バージョン管理: `evaluation_version` で採点ロジック差分追跡。
- 重み調整: 設問ウェイト（4:8:6）および観点配点（合計100）は .env やサーバー側設定で将来変更可能に。

## 5. 今後の拡張候補
- `evaluation_version` フィールド追加でアルゴリズム差分管理。
- `explanation_chain` でモデルが導いた根拠ステップを返却（LLM可視化）。
- `rubric_weights` をレスポンスに含め UI 側でランキンググラフ描画。
