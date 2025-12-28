"""
E2Eテスト: 回答保存・取得API
実際のDynamoDBを使用してテスト
"""

import pytest
import uuid


class TestAnswersE2E:
    """回答API E2Eテスト（実DynamoDB使用）"""
    
    @pytest.mark.e2e
    def test_submit_and_retrieve_answer(self, client, sample_answers_high_score, valid_problem_id):
        """
        回答を保存し、その後取得できること
        
        フロー:
        1. POST /api/answers で回答を保存
        2. GET /api/answers/{submission_id} で回答を取得
        3. 保存した内容と取得した内容が一致することを確認
        """
        # 1. 回答を保存
        submit_payload = {
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": sample_answers_high_score,
            "metadata": {
                "test": True,
                "test_id": str(uuid.uuid4())
            }
        }
        
        submit_response = client.post("/api/answers", json=submit_payload)
        
        assert submit_response.status_code == 200, f"保存失敗: {submit_response.text}"
        
        submit_data = submit_response.json()
        assert "submission_id" in submit_data
        assert "submitted_at" in submit_data
        
        submission_id = submit_data["submission_id"]
        
        # 2. 回答を取得
        get_response = client.get(f"/api/answers/{submission_id}")
        
        assert get_response.status_code == 200, f"取得失敗: {get_response.text}"
        
        get_data = get_response.json()
        
        # 3. 内容を検証
        assert get_data["submission_id"] == submission_id
        assert get_data["exam_type"] == "IS"
        assert get_data["problem_id"] == valid_problem_id
        assert get_data["answers"] == sample_answers_high_score
        assert get_data["status"] == "submitted"
    
    @pytest.mark.e2e
    def test_retrieve_nonexistent_answer_returns_404(self, client):
        """
        存在しない回答を取得しようとすると404が返ること
        """
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/answers/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.e2e
    def test_submit_answer_with_all_exam_types(self, client, valid_problem_id):
        """
        すべての試験区分で回答が保存できること
        """
        exam_types = ["IS", "PM", "SA", "ST"]
        
        for exam_type in exam_types:
            payload = {
                "exam_type": exam_type,
                "problem_id": valid_problem_id,
                "answers": {"設問ア": f"{exam_type}のテスト回答"}
            }
            
            response = client.post("/api/answers", json=payload)
            
            assert response.status_code == 200, f"{exam_type}の保存に失敗: {response.text}"
    
    @pytest.mark.e2e
    def test_submit_partial_answers(self, client, valid_problem_id):
        """
        一部の設問のみの回答が保存できること（途中保存対応）
        """
        payload = {
            "exam_type": "IS",
            "problem_id": valid_problem_id,
            "answers": {"設問ア": "設問アのみの回答"}  # 設問イ・ウは未回答
        }
        
        response = client.post("/api/answers", json=payload)
        
        assert response.status_code == 200
        
        # 取得して確認
        submission_id = response.json()["submission_id"]
        get_response = client.get(f"/api/answers/{submission_id}")
        
        assert get_response.status_code == 200
        assert "設問ア" in get_response.json()["answers"]
        assert "設問イ" not in get_response.json()["answers"]
