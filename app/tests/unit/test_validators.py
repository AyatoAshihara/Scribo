"""
単体テスト: バリデーション機能
AnswerSubmission モデルの入力検証をテスト
"""

import pytest
from pydantic import ValidationError

from routers.answers import AnswerSubmission


class TestAnswerSubmissionValidation:
    """AnswerSubmission バリデーションテスト"""
    
    # =========================================================================
    # 正常系テスト
    # =========================================================================
    
    @pytest.mark.unit
    def test_valid_submission(self, sample_answers_high_score, valid_problem_id):
        """正常な回答データが受け入れられること"""
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers=sample_answers_high_score
        )
        
        assert submission.exam_type == "IS"
        assert submission.problem_id == valid_problem_id
        assert len(submission.answers) == 3
    
    @pytest.mark.unit
    @pytest.mark.parametrize("exam_type", ["IS", "PM", "SA", "ST"])
    def test_valid_exam_types(self, exam_type, valid_problem_id):
        """すべての有効な試験区分が受け入れられること"""
        submission = AnswerSubmission(
            exam_type=exam_type,
            problem_id=valid_problem_id,
            answers={"設問ア": "テスト回答"}
        )
        
        assert submission.exam_type == exam_type
    
    @pytest.mark.unit
    @pytest.mark.parametrize("problem_id", [
        "YEAR#2024SPRING#ESSAY#Q1",
        "YEAR#2024FALL#ESSAY#Q2",
        "YEAR#2023SPRING#ESSAY#Q3",
    ])
    def test_valid_problem_id_formats(self, problem_id):
        """有効な問題IDフォーマットが受け入れられること"""
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=problem_id,
            answers={"設問ア": "テスト回答"}
        )
        
        assert submission.problem_id == problem_id
    
    # =========================================================================
    # 異常系テスト: exam_type
    # =========================================================================
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_exam_type", ["XX", "is", "pm", "", "IT"])
    def test_invalid_exam_type_rejected(self, invalid_exam_type, valid_problem_id):
        """無効な試験区分が拒否されること"""
        with pytest.raises(ValidationError) as exc_info:
            AnswerSubmission(
                exam_type=invalid_exam_type,
                problem_id=valid_problem_id,
                answers={"設問ア": "テスト回答"}
            )
        
        assert "exam_type" in str(exc_info.value)
    
    # =========================================================================
    # 異常系テスト: problem_id
    # =========================================================================
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_problem_id", [
        "invalid-format",
        "YEAR#2024#ESSAY#Q1",  # SPRING/FALL がない
        "2024SPRING#ESSAY#Q1",  # YEAR# がない
        "YEAR#2024SPRING#Q1",  # ESSAY# がない
        "",
    ])
    def test_invalid_problem_id_rejected(self, invalid_problem_id):
        """無効な問題IDフォーマットが拒否されること"""
        with pytest.raises(ValidationError) as exc_info:
            AnswerSubmission(
                exam_type="IS",
                problem_id=invalid_problem_id,
                answers={"設問ア": "テスト回答"}
            )
        
        assert "problem_id" in str(exc_info.value)
    
    # =========================================================================
    # 異常系テスト: answers
    # =========================================================================
    
    @pytest.mark.unit
    def test_invalid_answer_key_rejected(self, valid_problem_id):
        """無効な設問キーが拒否されること"""
        with pytest.raises(ValidationError) as exc_info:
            AnswerSubmission(
                exam_type="IS",
                problem_id=valid_problem_id,
                answers={"設問エ": "無効な設問"}  # 設問エは存在しない
            )
        
        assert "設問" in str(exc_info.value) or "answers" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_answer_exceeds_max_length_rejected(self, valid_problem_id):
        """5000文字を超える回答が拒否されること"""
        long_answer = "あ" * 5001
        
        with pytest.raises(ValidationError) as exc_info:
            AnswerSubmission(
                exam_type="IS",
                problem_id=valid_problem_id,
                answers={"設問ア": long_answer}
            )
        
        assert "5000" in str(exc_info.value) or "上限" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_answer_at_max_length_accepted(self, valid_problem_id):
        """5000文字ちょうどの回答が受け入れられること"""
        max_answer = "あ" * 5000
        
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers={"設問ア": max_answer}
        )
        
        assert len(submission.answers["設問ア"]) == 5000
    
    # =========================================================================
    # 境界値テスト
    # =========================================================================
    
    @pytest.mark.unit
    def test_empty_answers_accepted(self, valid_problem_id):
        """空の回答辞書が受け入れられること（送信時の部分保存用）"""
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers={}
        )
        
        assert submission.answers == {}
    
    @pytest.mark.unit
    def test_all_questions_answered(self, valid_problem_id, sample_answers_high_score):
        """3設問すべてに回答がある場合"""
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers=sample_answers_high_score
        )
        
        assert "設問ア" in submission.answers
        assert "設問イ" in submission.answers
        assert "設問ウ" in submission.answers


class TestAnswerSubmissionMetadata:
    """AnswerSubmission メタデータテスト"""
    
    @pytest.mark.unit
    def test_metadata_optional(self, valid_problem_id):
        """metadataがオプショナルであること"""
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers={"設問ア": "テスト"}
        )
        
        assert submission.metadata is None
    
    @pytest.mark.unit
    def test_metadata_accepted(self, valid_problem_id):
        """metadataが正しく保存されること"""
        metadata = {
            "timer_seconds_used": 3600,
            "client_version": "web-1.0.0"
        }
        
        submission = AnswerSubmission(
            exam_type="IS",
            problem_id=valid_problem_id,
            answers={"設問ア": "テスト"},
            metadata=metadata
        )
        
        assert submission.metadata == metadata
