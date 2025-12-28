"""
回答保存 API ルーター
DynamoDB (SubmissionTable) に回答を保存
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, Field
from typing import Dict, Optional, Literal
from datetime import datetime
import uuid
import re
import boto3

from config import get_settings

router = APIRouter()
settings = get_settings()

# DynamoDB クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
submission_table = dynamodb.Table(settings.dynamodb_submission_table)


class AnswerSubmission(BaseModel):
    """回答送信リクエスト"""
    exam_type: Literal["IS", "PM", "SA", "ST"] = Field(..., description="試験区分")
    problem_id: str = Field(..., min_length=1, max_length=100, description="問題ID")
    answers: Dict[str, str]  # {"設問ア": "...", "設問イ": "...", "設問ウ": "..."}
    metadata: Optional[Dict] = None
    
    @field_validator('problem_id')
    @classmethod
    def validate_problem_id(cls, v: str) -> str:
        """問題IDの形式を検証"""
        if not re.match(r'^YEAR#\d{4}(SPRING|FALL)#ESSAY#Q\d$', v):
            raise ValueError('問題IDの形式が不正です')
        return v
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v: Dict[str, str]) -> Dict[str, str]:
        """回答の検証（キーと文字数制限）"""
        allowed_keys = {'設問ア', '設問イ', '設問ウ'}
        for key, value in v.items():
            if key not in allowed_keys:
                raise ValueError(f'無効な設問キー: {key}')
            if len(value) > 5000:
                raise ValueError(f'{key}の文字数が上限(5000文字)を超えています')
        return v


class AnswerResponse(BaseModel):
    """回答送信レスポンス"""
    submission_id: str
    submitted_at: str
    message: str


@router.post("", response_model=AnswerResponse)
async def submit_answer(submission: AnswerSubmission):
    """
    回答を保存
    
    Args:
        submission: 回答データ
    
    Returns:
        保存結果（submission_id含む）
    """
    try:
        submission_id = str(uuid.uuid4())
        submitted_at = datetime.utcnow().isoformat() + "Z"
        
        # DynamoDBに保存（キーはsubmission_idのみ）
        item = {
            "submission_id": submission_id,
            "exam_type": submission.exam_type,
            "problem_id": submission.problem_id,
            "answers": submission.answers,
            "submitted_at": submitted_at,
            "status": "submitted",
        }
        
        if submission.metadata:
            item["metadata"] = submission.metadata
        
        submission_table.put_item(Item=item)
        
        return AnswerResponse(
            submission_id=submission_id,
            submitted_at=submitted_at,
            message="回答を保存しました"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答の保存に失敗しました: {str(e)}")


@router.get("/{submission_id}")
async def get_answer(submission_id: str):
    """
    保存済み回答を取得
    
    Args:
        submission_id: 提出ID
    
    Returns:
        回答データ
    """
    try:
        response = submission_table.get_item(
            Key={
                "submission_id": submission_id
            }
        )
        
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="回答が見つかりません")
        
        return {
            "submission_id": item.get("submission_id"),
            "exam_type": item.get("exam_type"),
            "problem_id": item.get("problem_id"),
            "answers": item.get("answers", {}),
            "submitted_at": item.get("submitted_at"),
            "status": item.get("status"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答の取得に失敗しました: {str(e)}")
