"""
E2Eテスト: 採点API
実際のDynamoDB + Bedrockを使用してテスト

注意: このテストはBedrock APIを呼び出すため、コストが発生します。
手動トリガーまたは週次実行を推奨します。
"""

import pytest
import uuid
import time

# conftest.py からインポート
from tests.conftest import validate_scoring_response


class TestScoringE2E:
    """採点API E2Eテスト（実DynamoDB + 実Bedrock使用）"""
    
    @pytest.mark.e2e
    def test_scoring_high_quality_answer(self, client, sample_answers_high_score, valid_problem_id):
        """
        高品質な回答が適切に採点されること
        
        検証項目:
        - 採点が成功すること（200レスポンス）
        - aggregate_score が 50-100 の範囲内
        - final_rank が A または B
        - 全設問に8観点のスコアとコメントが存在
        """
        # 1. 回答を保存
        submit_payload = {
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_high_score,
            "metadata": {"test": True, "test_type": "high_quality"}
        }
        
        submit_response = client.post("/api/answers", json=submit_payload)
        print(f"\n[DEBUG] Submit status: {submit_response.status_code}")
        print(f"[DEBUG] Submit body: {submit_response.text}")
        assert submit_response.status_code == 200
        
        submission_id = submit_response.json()["submission_id"]
        
        # 2. 採点を実行
        scoring_payload = {"submission_id": submission_id}
        
        scoring_response = client.post("/api/scoring", json=scoring_payload)
        
        assert scoring_response.status_code == 200, f"採点失敗: {scoring_response.text}"
        
        scoring_data = scoring_response.json()
        
        # 3. 採点結果の検証
        validation = validate_scoring_response(scoring_data)
        assert validation["valid"], f"採点結果が不正: {validation['errors']}"
        
        # 4. 高品質回答としての期待値確認（temperature=0.0で安定化）
        assert scoring_data["aggregate_score"] >= 75, \
            f"高品質回答（IPA模範解答レベル）のスコアが低すぎます: {scoring_data['aggregate_score']}"
        
        assert scoring_data["final_rank"] == "A", \
            f"高品質回答（IPA模範解答レベル）はランクAであるべき: {scoring_data['final_rank']}"
        
        print(f"\n✅ 高品質回答の採点結果:")
        print(f"   スコア: {scoring_data['aggregate_score']}")
        print(f"   ランク: {scoring_data['final_rank']}")
        print(f"   合格: {scoring_data['passed']}")
    
    @pytest.mark.e2e
    def test_scoring_low_quality_answer(self, client, sample_answers_low_score, valid_problem_id):
        """
        低品質な回答が適切に採点されること
        
        検証項目:
        - 採点が成功すること（200レスポンス）
        - aggregate_score が 0-70 の範囲内（高品質より低い）
        - 全設問に8観点のスコアとコメントが存在
        """
        # 1. 回答を保存
        submit_payload = {
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_low_score,
            "metadata": {"test": True, "test_type": "low_quality"}
        }
        
        submit_response = client.post("/api/answers", json=submit_payload)
        assert submit_response.status_code == 200
        
        submission_id = submit_response.json()["submission_id"]
        
        # 2. 採点を実行
        scoring_payload = {"submission_id": submission_id}
        
        scoring_response = client.post("/api/scoring", json=scoring_payload)
        
        assert scoring_response.status_code == 200, f"採点失敗: {scoring_response.text}"
        
        scoring_data = scoring_response.json()
        
        # 3. 採点結果の検証
        validation = validate_scoring_response(scoring_data)
        assert validation["valid"], f"採点結果が不正: {validation['errors']}"
        
        # 4. 低品質回答としての期待値確認
        assert scoring_data["aggregate_score"] <= 70, \
            f"低品質回答のスコアが高すぎます: {scoring_data['aggregate_score']}"
        
        print(f"\n✅ 低品質回答の採点結果:")
        print(f"   スコア: {scoring_data['aggregate_score']}")
        print(f"   ランク: {scoring_data['final_rank']}")
        print(f"   合格: {scoring_data['passed']}")
    
    @pytest.mark.e2e
    def test_scoring_result_persisted(self, client, sample_answers_high_score, valid_problem_id):
        """
        採点結果がDynamoDBに永続化されること
        
        フロー:
        1. 回答を保存
        2. 採点を実行
        3. GET /api/scoring/{submission_id} で結果を取得
        4. 採点結果が一致することを確認
        """
        # 1. 回答を保存
        submit_payload = {
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_high_score
        }
        
        submit_response = client.post("/api/answers", json=submit_payload)
        submission_id = submit_response.json()["submission_id"]
        
        # 2. 採点を実行
        scoring_response = client.post("/api/scoring", json={"submission_id": submission_id})
        assert scoring_response.status_code == 200
        
        original_scoring = scoring_response.json()
        
        # 3. 採点結果を取得
        get_response = client.get(f"/api/scoring/{submission_id}")
        
        assert get_response.status_code == 200, f"採点結果取得失敗: {get_response.text}"
        
        retrieved_scoring = get_response.json()
        
        # 4. 結果が一致することを確認
        assert retrieved_scoring["submission_id"] == original_scoring["submission_id"]
        assert retrieved_scoring["aggregate_score"] == original_scoring["aggregate_score"]
        assert retrieved_scoring["final_rank"] == original_scoring["final_rank"]
        assert retrieved_scoring["passed"] == original_scoring["passed"]
    
    @pytest.mark.e2e
    def test_scoring_nonexistent_submission_returns_404(self, client):
        """
        存在しない回答の採点を試みると404が返ること
        """
        fake_id = str(uuid.uuid4())
        
        response = client.post("/api/scoring", json={"submission_id": fake_id})
        
        assert response.status_code == 404
    
    @pytest.mark.e2e
    def test_scoring_response_has_all_criteria_comments(self, client, sample_answers_high_score, valid_problem_id):
        """
        採点結果の全観点にコメントが存在すること
        """
        # 回答を保存
        submit_response = client.post("/api/answers", json={
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_high_score
        })
        submission_id = submit_response.json()["submission_id"]
        
        # 採点を実行
        scoring_response = client.post("/api/scoring", json={"submission_id": submission_id})
        scoring_data = scoring_response.json()
        
        # 全設問の全観点にコメントがあることを確認
        for question in ["設問ア", "設問イ", "設問ウ"]:
            breakdown = scoring_data["question_breakdown"].get(question, {})
            criteria_scores = breakdown.get("criteria_scores", [])
            
            assert len(criteria_scores) >= 8, \
                f"{question}の観点数が不足: {len(criteria_scores)}"
            
            for cs in criteria_scores:
                assert cs.get("comment"), \
                    f"{question}の{cs.get('criterion', '?')}にコメントがありません"
                
                # コメントが空文字列でないことも確認
                assert len(cs["comment"].strip()) > 0, \
                    f"{question}の{cs['criterion']}のコメントが空です"
        
        print("\n✅ 全設問・全観点にコメントが存在することを確認しました")


class TestScoringQualityDifference:
    """採点品質の差異テスト"""
    
    @pytest.mark.e2e
    def test_high_quality_scores_higher_than_low_quality(
        self, client, sample_answers_high_score, sample_answers_low_score, valid_problem_id
    ):
        """
        高品質回答が低品質回答より高いスコアを得ること
        
        これはAI採点の基本的な妥当性を検証するテスト
        """
        # 高品質回答を採点
        high_submit = client.post("/api/answers", json={
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_high_score
        })
        high_scoring = client.post("/api/scoring", json={
            "submission_id": high_submit.json()["submission_id"]
        })
        high_score = high_scoring.json()["aggregate_score"]
        
        # 低品質回答を採点
        low_submit = client.post("/api/answers", json={
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_low_score
        })
        low_scoring = client.post("/api/scoring", json={
            "submission_id": low_submit.json()["submission_id"]
        })
        low_score = low_scoring.json()["aggregate_score"]
        
        # 高品質 > 低品質 であることを確認
        assert high_score > low_score, \
            f"高品質回答({high_score})が低品質回答({low_score})より低いスコアです"
        
        print(f"\n✅ スコア差異テスト合格:")
        print(f"   高品質: {high_score}")
        print(f"   低品質: {low_score}")
        print(f"   差分: {high_score - low_score}")
