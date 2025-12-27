# Scribo API 仕様書

## 概要

Scribo APIはFastAPIで実装されたRESTful APIです。  
試験一覧取得、問題詳細取得、回答保存、AI採点の機能を提供します。

**ベースURL:** `http://scribo-alb-760941679.ap-northeast-1.elb.amazonaws.com`

---

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | トップページ（HTML） |
| GET | `/problem/{exam_type}/{problem_id}` | 問題ページ（HTML） |
| GET | `/result/{submission_id}` | 採点結果ページ（HTML） |
| GET | `/api/exams` | 試験一覧取得 |
| GET | `/api/exams/detail` | 問題詳細取得 |
| GET | `/api/exams/partial/list` | 試験一覧（HTML部分） |
| POST | `/api/answers` | 回答保存 |
| GET | `/api/answers/{submission_id}` | 回答取得 |
| POST | `/api/scoring` | AI採点実行 |
| GET | `/api/scoring/{submission_id}` | 採点結果取得 |
| GET | `/health` | ヘルスチェック |

---

## ページルート（HTML）

### GET /

トップページ（試験一覧）を表示します。

**レスポンス:** HTML

---

### GET /problem/{exam_type}/{problem_id}

問題閲覧・回答入力ページを表示します。

**パラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| exam_type | string | 試験区分 (IS/PM/SA) |
| problem_id | string | 問題ID (URLエンコード済み) |

**レスポンス:** HTML

---

### GET /result/{submission_id}

採点結果ページを表示します。

**パラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| submission_id | string | 提出ID (UUID) |

**レスポンス:** HTML

---

## API エンドポイント

### GET /api/exams

試験一覧を取得します。

**クエリパラメータ:**
| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|----------|------|
| exam_type | string | No | IS | 試験区分 (IS/PM/SA) |

**レスポンス:**
```json
{
  "exams": [
    {
      "problem_id": "YEAR#2024AUTUMN#ESSAY#Q1",
      "title": "DXを推進するための組織変革について",
      "year_term": "2024秋",
      "exam_type": "IS",
      "question_id": "Q1"
    }
  ],
  "exam_type": "IS"
}
```

---

### GET /api/exams/detail

問題詳細を取得します。

**クエリパラメータ:**
| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| exam_type | string | Yes | 試験区分 |
| problem_id | string | Yes | 問題ID |

**レスポンス:**
```json
{
  "problem_id": "YEAR#2024AUTUMN#ESSAY#Q1",
  "title": "DXを推進するための組織変革について",
  "year_term": "2024秋",
  "exam_type": "IS",
  "problem_content": "問題本文...",
  "problem_question": {
    "設問ア": "あなたが携わった...",
    "設問イ": "設問アで述べた...",
    "設問ウ": "設問イで述べた..."
  },
  "word_count_limits": {
    "設問ア": { "min": 600, "max": 800 },
    "設問イ": { "min": 700, "max": 1000 },
    "設問ウ": { "min": 600, "max": 800 }
  }
}
```

**エラーレスポンス:**
| ステータス | 説明 |
|-----------|------|
| 404 | 問題が見つかりません |
| 500 | 内部エラー |

---

### GET /api/exams/partial/list

試験一覧をHTMLパーシャルとして取得します（htmx用）。

**クエリパラメータ:**
| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|----------|------|
| exam_type | string | No | IS | 試験区分 |

**レスポンス:** HTML（カードリスト）

---

### POST /api/answers

回答を保存します。

**リクエストボディ:**
```json
{
  "exam_type": "IS",
  "problem_id": "YEAR#2024AUTUMN#ESSAY#Q1",
  "answers": {
    "設問ア": "私が携わったプロジェクトは...",
    "設問イ": "上記の課題に対して...",
    "設問ウ": "実施した結果..."
  },
  "metadata": {
    "word_counts": {
      "設問ア": 650,
      "設問イ": 850,
      "設問ウ": 720
    }
  }
}
```

**レスポンス:**
```json
{
  "submission_id": "550e8400-e29b-41d4-a716-446655440000",
  "submitted_at": "2024-12-27T10:30:00Z",
  "message": "回答を保存しました"
}
```

---

### GET /api/answers/{submission_id}

保存された回答を取得します。

**パスパラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| submission_id | string | 提出ID |

**レスポンス:**
```json
{
  "submission_id": "550e8400-e29b-41d4-a716-446655440000",
  "exam_type": "IS",
  "problem_id": "YEAR#2024AUTUMN#ESSAY#Q1",
  "answers": {
    "設問ア": "...",
    "設問イ": "...",
    "設問ウ": "..."
  },
  "submitted_at": "2024-12-27T10:30:00Z",
  "status": "submitted"
}
```

---

### POST /api/scoring

AI採点を実行します。

**注意:** 採点処理は最大90秒かかる場合があります。

**リクエストボディ:**
```json
{
  "submission_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**レスポンス:**
```json
{
  "submission_id": "550e8400-e29b-41d4-a716-446655440000",
  "aggregate_score": 72.5,
  "final_rank": "B",
  "passed": true,
  "question_breakdown": {
    "設問ア": {
      "level": "B",
      "question_score": 75,
      "word_count": 650,
      "criteria_scores": [
        { "criterion": "充足度", "weight": 0.15, "points": 80, "comment": "..." },
        { "criterion": "具体性", "weight": 0.15, "points": 70, "comment": "..." },
        { "criterion": "妥当性", "weight": 0.15, "points": 75, "comment": "..." },
        { "criterion": "一貫性", "weight": 0.10, "points": 80, "comment": "..." },
        { "criterion": "主張", "weight": 0.15, "points": 70, "comment": "..." },
        { "criterion": "洞察力-行動力", "weight": 0.10, "points": 75, "comment": "..." },
        { "criterion": "独創性-先見性", "weight": 0.10, "points": 65, "comment": "..." },
        { "criterion": "表現力", "weight": 0.10, "points": 80, "comment": "..." }
      ]
    },
    "設問イ": { ... },
    "設問ウ": { ... }
  }
}
```

**エラーレスポンス:**
| ステータス | 説明 |
|-----------|------|
| 404 | 回答が見つかりません |
| 500 | 採点処理エラー |

---

### GET /api/scoring/{submission_id}

採点結果を取得します。

**パスパラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| submission_id | string | 提出ID |

**レスポンス:** POST /api/scoring と同じ形式

**エラーレスポンス:**
| ステータス | 説明 |
|-----------|------|
| 404 | 採点結果が見つかりません |

---

### GET /health

ヘルスチェック用エンドポイントです（ALB用）。

**レスポンス:**
```json
{
  "status": "healthy"
}
```

---

## 採点評価観点

| 観点 | 重み | 説明 |
|------|------|------|
| 充足度 | 0.15 | 設問の要求を満たしているか |
| 具体性 | 0.15 | 具体的な事例・数値が含まれているか |
| 妥当性 | 0.15 | 論理的に妥当な内容か |
| 一貫性 | 0.10 | 論文全体で一貫性があるか |
| 主張 | 0.15 | 明確な主張があるか |
| 洞察力-行動力 | 0.10 | 深い洞察と行動が示されているか |
| 独創性-先見性 | 0.10 | 独自の視点があるか |
| 表現力 | 0.10 | 分かりやすい表現か |

---

## 文字数制限

| 設問 | 最小 | 最大 |
|------|------|------|
| 設問ア | 600字 | 800字 |
| 設問イ | 700字 | 1000字 |
| 設問ウ | 600字 | 800字 |

---

## ランク判定基準

| ランク | スコア範囲 | 合格判定 |
|--------|-----------|---------|
| A | 80点以上 | 合格 |
| B | 60-79点 | 合格 |
| C | 40-59点 | 不合格 |
| D | 40点未満 | 不合格 |

---

## 関連ドキュメント

- [アーキテクチャ](./ARCHITECTURE.md)
- [採点API詳細](./SCORING_API.md)
- [デプロイ手順](./DEPLOYMENT_GUIDE.md)
