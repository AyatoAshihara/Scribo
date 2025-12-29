"""
E2Eテスト: AIインタビュー・設計書生成
実際のDynamoDBとBedrockを使用してテスト
"""

import pytest
import uuid
import time

class TestInterviewE2E:
    """インタビューAPI E2Eテスト（実DynamoDB/Bedrock使用）"""
    
    @pytest.mark.e2e
    def test_interview_flow_and_generation(self, client):
        """
        インタビューセッション作成〜チャット〜設計書生成のフロー検証
        
        フロー:
        1. GET /api/interview/sessions/{exam_id} でセッション作成
        2. POST /api/interview/chat/{exam_id} でチャット送信（履歴蓄積）
        3. POST /api/interview/generate/{exam_id} で設計書生成
        4. 生成された設計書の構造検証
        """
        # テスト用のユニークなID
        exam_id = f"test-e2e-{uuid.uuid4()}"
        
        # 1. セッション作成
        session_res = client.get(f"/api/interview/sessions/{exam_id}")
        assert session_res.status_code == 200
        session_data = session_res.json()
        assert session_data["exam_id"] == exam_id
        assert len(session_data["history"]) >= 1 # 初期メッセージがあるはず
        
        # 2. チャット送信
        # Bedrockが文脈を理解できるよう、具体的な内容を送る
        chat_payload = {
            "message": "物流業界の2024年問題について、配送ルート最適化の観点で論文を書きたいです。具体的な課題はドライバー不足と長時間労働です。"
        }
        chat_res = client.post(f"/api/interview/chat/{exam_id}", json=chat_payload)
        assert chat_res.status_code == 200
        # ストリーミングレスポンスなので、コンテンツの検証は簡易的に行う
        # (実際のストリーム消費はTestClientでは少し特殊だが、status 200なら接続OK)
        
        # 履歴が保存されるまで少し待つ（DynamoDBの整合性考慮）
        time.sleep(2)
        
        # 履歴が更新されたか確認
        session_res_2 = client.get(f"/api/interview/sessions/{exam_id}")
        session_data_2 = session_res_2.json()
        # 初期メッセージ + ユーザーメッセージ + AI応答 = 3以上
        assert len(session_data_2["history"]) >= 3
        
        # 3. 設計書生成
        # Bedrock呼び出しを含むため時間がかかる
        generate_res = client.post(f"/api/interview/generate/{exam_id}")
        assert generate_res.status_code == 200
        
        proposal = generate_res.json()
        
        # 4. 構造検証
        assert "theme" in proposal
        assert len(proposal["theme"]) > 0
        
        assert "breakdown" in proposal
        assert "A" in proposal["breakdown"]
        assert "B" in proposal["breakdown"]
        assert "C" in proposal["breakdown"]
        
        assert "structure" in proposal
        assert isinstance(proposal["structure"], list)
        assert len(proposal["structure"]) > 0
        
        assert "module_map" in proposal
        
        # 生成されたテーマが文脈（物流）に関連しているか簡易チェック
        assert "物流" in proposal["theme"] or "配送" in proposal["theme"] or "2024" in proposal["theme"]
