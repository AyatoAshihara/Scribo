"""
AI採点 API ルーター
Amazon Bedrock (Claude) で論文を採点
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
import json
import boto3
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings

# ロガー設定
logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# レート制限
limiter = Limiter(key_func=get_remote_address)

# AWS クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
submission_table = dynamodb.Table(settings.dynamodb_submission_table)
bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)


class ScoringRequest(BaseModel):
    """採点リクエスト"""
    submission_id: str


class CriteriaScore(BaseModel):
    """評価観点別スコア"""
    criterion: str
    weight: float
    points: int
    comment: Optional[str] = None


class QuestionBreakdown(BaseModel):
    """設問別評価"""
    level: str
    question_score: int
    word_count: int
    criteria_scores: List[CriteriaScore]


class ScoringResponse(BaseModel):
    """採点レスポンス"""
    submission_id: str
    aggregate_score: float
    final_rank: str
    passed: bool
    question_breakdown: Dict[str, QuestionBreakdown]


# 採点プロンプトテンプレート
SCORING_PROMPT = """あなたはIPA情報処理技術者試験の午後Ⅱ論述式問題の採点者です。
以下の回答を評価してください。

## 評価観点（各0-100点）
1. 充足度 (weight: 0.15) - 設問の要求を満たしているか
2. 具体性 (weight: 0.15) - 具体的な事例・数値が含まれているか
3. 妥当性 (weight: 0.15) - 論理的に妥当な内容か
4. 一貫性 (weight: 0.10) - 論文全体で一貫性があるか
5. 主張 (weight: 0.15) - 明確な主張があるか
6. 洞察力-行動力 (weight: 0.10) - 深い洞察と行動が示されているか
7. 独創性-先見性 (weight: 0.10) - 独自の視点があるか
8. 表現力 (weight: 0.10) - 分かりやすい表現か

## 回答内容
{answers}

## 出力形式
JSON形式で以下の構造で出力してください：
{{
  "question_breakdown": {{
    "設問ア": {{
      "level": "A/B/C/D",
      "question_score": 0-100,
      "criteria_scores": [
        {{"criterion": "充足度", "weight": 0.15, "points": 0-100, "comment": "..."}},
        ...
      ]
    }},
    "設問イ": {{ ... }},
    "設問ウ": {{ ... }}
  }},
  "aggregate_score": 0-100,
  "final_rank": "A/B/C/D",
  "feedback": "全体的なフィードバック"
}}
"""


@router.post("", response_model=ScoringResponse)
@limiter.limit("5/minute")  # 1分間に5回まで（Bedrockコスト保護）
async def score_submission(request: Request, scoring_request: ScoringRequest):
    """
    回答を採点
    
    Args:
        request: FastAPI Request（レート制限用）
        scoring_request: 採点リクエスト（submission_id）
    
    Returns:
        採点結果
    """
    try:
        # 回答を取得
        response = submission_table.get_item(
            Key={
                "submission_id": scoring_request.submission_id
            }
        )
        
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="回答が見つかりません")
        
        answers = item.get("answers", {})
        
        # 回答を文字列化
        answers_text = ""
        for question, answer in answers.items():
            word_count = len(answer.replace(" ", "").replace("\n", ""))
            answers_text += f"\n### {question}（{word_count}文字）\n{answer}\n"
        
        # Bedrock で採点
        prompt = SCORING_PROMPT.format(answers=answers_text)
        
        bedrock_response = bedrock.invoke_model(
            modelId=settings.bedrock_model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        response_body = json.loads(bedrock_response["body"].read())
        content = response_body["content"][0]["text"]
        
        # JSONを抽出してパース
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            raise HTTPException(status_code=500, detail="採点結果のパースに失敗しました")
        
        scoring_result = json.loads(content[json_start:json_end])
        
        # 文字数を追加
        question_breakdown = scoring_result.get("question_breakdown", {})
        for question, breakdown in question_breakdown.items():
            answer_text = answers.get(question, "")
            breakdown["word_count"] = len(answer_text.replace(" ", "").replace("\n", ""))
        
        # Float を Decimal に変換（DynamoDB用）
        def convert_floats(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(i) for i in obj]
            return obj
        
        breakdown_for_db = convert_floats(question_breakdown)
        aggregate_score = Decimal(str(scoring_result.get("aggregate_score", 0)))
        
        # 結果をDynamoDBの既存レコードに追加保存
        submission_table.update_item(
            Key={"submission_id": scoring_request.submission_id},
            UpdateExpression="SET aggregate_score = :score, final_rank = :rank, passed = :passed, question_breakdown = :breakdown, scored_at = :scored_at, #st = :status",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":score": aggregate_score,
                ":rank": scoring_result.get("final_rank", "D"),
                ":passed": scoring_result.get("final_rank", "D") == "A",
                ":breakdown": breakdown_for_db,
                ":scored_at": datetime.utcnow().isoformat() + "Z",
                ":status": "scored"
            }
        )
        
        return ScoringResponse(
            submission_id=scoring_request.submission_id,
            aggregate_score=scoring_result.get("aggregate_score", 0),
            final_rank=scoring_result.get("final_rank", "D"),
            passed=scoring_result.get("final_rank", "D") == "A",
            question_breakdown=question_breakdown,
        )
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"採点結果のJSON解析エラー: {str(e)}")
        raise HTTPException(status_code=500, detail="採点結果の解析に失敗しました")
    except Exception as e:
        logger.error(f"採点処理エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="採点処理に失敗しました。しばらくしてから再度お試しください。")


@router.get("/{submission_id}")
async def get_scoring_result(submission_id: str):
    """
    採点結果を取得
    
    Args:
        submission_id: 提出ID
    
    Returns:
        採点結果
    """
    try:
        response = submission_table.get_item(
            Key={
                "submission_id": submission_id
            }
        )
        
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="採点結果が見つかりません")
        
        # 採点済みかチェック
        if item.get("status") != "scored":
            raise HTTPException(status_code=404, detail="採点結果が見つかりません")
        
        return {
            "submission_id": item.get("submission_id"),
            "aggregate_score": float(item.get("aggregate_score", 0)),
            "final_rank": item.get("final_rank"),
            "passed": item.get("passed"),
            "question_breakdown": item.get("question_breakdown", {}),
            "scored_at": item.get("scored_at"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"採点結果取得エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="採点結果の取得に失敗しました")
