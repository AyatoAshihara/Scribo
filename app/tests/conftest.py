"""
Scribo テスト共通フィクスチャ
"""

import pytest
from fastapi.testclient import TestClient

from main import app


# =============================================================================
# TestClient フィクスチャ
# =============================================================================

@pytest.fixture
def client():
    """FastAPI TestClient"""
    with TestClient(app) as c:
        yield c


# =============================================================================
# サンプル回答データ フィクスチャ
# =============================================================================

@pytest.fixture
def sample_answers_high_score():
    """高得点が期待されるサンプル回答"""
    return {
        "設問ア": """私が携わったITストラテジー策定プロジェクトについて述べる。

1. プロジェクトの背景と目的
私は大手製造業A社（従業員5,000名、売上高2,000億円）の情報システム部門に所属するITストラテジストとして、2023年度の中期IT戦略策定プロジェクトに参画した。A社は創業50年の歴史を持つが、基幹システムの老朽化とDX推進の遅れが経営課題となっていた。

2. 策定したIT戦略の概要
私は以下の3つの柱からなるIT戦略を策定した。
（1）基幹システムの刷新：15年稼働したオンプレミスERPをクラウドERPへ移行し、TCOを30%削減
（2）データ活用基盤の構築：全社データレイクを構築し、経営ダッシュボードで意思決定を迅速化
（3）DX人材育成：3年間で100名のDX人材を育成する教育プログラムを実施

3. 私の役割と責任
私はIT戦略策定の責任者として、経営層へのプレゼンテーション、各事業部との調整、投資対効果の算定を担当した。特に、5年間で総額50億円の投資計画について、ROI 150%の達成見込みを示し、取締役会の承認を得た。""",
        
        "設問イ": """IT戦略策定において、私が特に工夫した点と直面した課題について述べる。

1. 経営戦略との整合性確保
最大の工夫は、経営戦略との整合性を徹底的に確保したことである。私は経営企画部と週次で会議を開催し、中期経営計画の各施策とIT戦略のマッピングを作成した。具体的には、「海外売上比率40%達成」という経営目標に対し、グローバルERP統合による海外拠点のリアルタイム可視化を提案した。

2. ステークホルダーマネジメント
各事業部の要望は多岐にわたり、優先順位付けが困難だった。私は以下の方法で解決した。
（1）事業インパクト×実現可能性のマトリクスで客観評価
（2）各事業部長への個別ヒアリング（計20回実施）
（3）経営会議でのオープンな議論の場の設定

3. 投資対効果の可視化
CFOからの厳しい指摘を受け、投資対効果の算定方法を見直した。従来の定性的な効果だけでなく、業務時間削減効果を時給換算で定量化し、年間3億円のコスト削減効果を明示した。これにより、投資承認のハードルを越えることができた。

4. リスク管理
クラウド移行に伴うセキュリティリスクについて、外部専門家を交えたリスクアセスメントを実施し、対策コストを含めた現実的な計画を策定した。""",
        
        "設問ウ": """IT戦略の実行と評価、および今後の改善について述べる。

1. 実行フェーズでの成果
策定したIT戦略は2024年4月より実行フェーズに移行した。初年度の成果として以下を達成した。
（1）クラウドERP移行：第1フェーズ（会計・人事）を予定通り完了、稼働率99.9%を達成
（2）データレイク構築：基盤構築完了、営業データの可視化により受注予測精度が15%向上
（3）DX人材育成：初年度30名が認定資格を取得、社内コミュニティが自発的に発足

2. 評価と反省点
KPIモニタリングの結果、当初計画と乖離が生じた項目もあった。特に、現場のチェンジマネジメントに想定以上の工数を要した。これは、私の計画段階でのユーザー教育期間の見積もりが甘かったことが原因である。

3. 今後の改善
この経験を踏まえ、次期計画では以下の改善を行う。
（1）チェンジマネジメント専任チームの設置
（2）現場キーマンを早期に巻き込むアンバサダー制度の導入
（3）アジャイル型のIT戦略見直しサイクル（四半期ごと）の導入

4. ITストラテジストとしての学び
本プロジェクトを通じ、IT戦略は策定して終わりではなく、実行・評価・改善のサイクルを回し続けることの重要性を学んだ。今後も経営とITの橋渡し役として、企業価値向上に貢献していく所存である。"""
    }


@pytest.fixture
def sample_answers_low_score():
    """低得点が想定されるサンプル回答（文字数不足・具体性欠如）"""
    return {
        "設問ア": """私はIT戦略を策定しました。会社のシステムが古かったので、新しくすることにしました。クラウドを使うことにしました。""",
        
        "設問イ": """工夫した点は、みんなの意見を聞いたことです。会議をたくさんしました。難しかったですが、がんばりました。""",
        
        "設問ウ": """結果は良かったです。システムが新しくなりました。今後も頑張りたいと思います。"""
    }


@pytest.fixture
def valid_exam_type():
    """有効な試験区分"""
    return "IS"


@pytest.fixture
def valid_problem_id():
    """有効な問題ID"""
    return "YEAR#2024SPRING#ESSAY#Q1"


@pytest.fixture
def invalid_problem_id():
    """無効な問題ID"""
    return "invalid-format"


# =============================================================================
# 採点結果検証用ヘルパー
# =============================================================================

REQUIRED_CRITERIA = [
    "充足度",
    "具体性",
    "妥当性", 
    "一貫性",
    "主張",
    "洞察力",
    "独創性",
    "表現力",
]


def validate_scoring_response(response_data: dict) -> dict:
    """
    採点結果の妥当性を検証
    
    Returns:
        検証結果（errors があれば失敗）
    """
    errors = []
    
    # 必須フィールドの存在確認
    required_fields = ["submission_id", "aggregate_score", "final_rank", "passed", "question_breakdown"]
    for field in required_fields:
        if field not in response_data:
            errors.append(f"必須フィールド '{field}' が存在しません")
    
    # aggregate_score の範囲確認
    score = response_data.get("aggregate_score", -1)
    if not (0 <= score <= 100):
        errors.append(f"aggregate_score ({score}) が範囲外です（0-100）")
    
    # final_rank の値確認
    rank = response_data.get("final_rank", "")
    if rank not in ["A", "B", "C", "D"]:
        errors.append(f"final_rank ({rank}) が不正です（A/B/C/D）")
    
    # 各設問の検証
    breakdown = response_data.get("question_breakdown", {})
    for question in ["設問ア", "設問イ", "設問ウ"]:
        if question not in breakdown:
            errors.append(f"{question} が question_breakdown に存在しません")
            continue
        
        q_data = breakdown[question]
        
        # question_score の確認
        q_score = q_data.get("question_score", -1)
        if not (0 <= q_score <= 100):
            errors.append(f"{question} の question_score ({q_score}) が範囲外です")
        
        # criteria_scores の確認
        criteria = q_data.get("criteria_scores", [])
        if len(criteria) < 8:
            errors.append(f"{question} の criteria_scores が8観点未満です（{len(criteria)}個）")
        
        # 各観点にコメントが存在するか
        for cs in criteria:
            if not cs.get("comment"):
                errors.append(f"{question} の {cs.get('criterion', '?')} にコメントがありません")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
