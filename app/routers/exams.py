"""
試験データ API ルーター
既存DynamoDB (scribo-ipa) から試験一覧・問題詳細を取得
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import boto3
from boto3.dynamodb.conditions import Key

from config import get_settings

router = APIRouter()
settings = get_settings()

# DynamoDB クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
exam_table = dynamodb.Table(settings.dynamodb_exam_table)


@router.get("")
async def get_exams(exam_type: str = Query(default="IS", description="試験区分 (IS/PM/SA)")):
    """
    試験一覧を取得
    
    Args:
        exam_type: 試験区分 (IS: ITストラテジスト, PM: プロジェクトマネージャ, SA: システムアーキテクト)
    
    Returns:
        試験一覧
    """
    try:
        response = exam_table.query(
            KeyConditionExpression=Key("PK").eq(f"EXAM#{exam_type}")
        )
        
        items = response.get("Items", [])
        
        # レスポンス形式を整形
        exams = []
        for item in items:
            exams.append({
                "problem_id": item.get("SK"),
                "title": item.get("title", ""),
                "year_term": item.get("year_term", ""),
                "exam_type": exam_type,
                "question_id": item.get("question_id", ""),
            })
        
        # 年度降順でソート
        exams.sort(key=lambda x: x.get("year_term", ""), reverse=True)
        
        return {"exams": exams, "exam_type": exam_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"試験一覧の取得に失敗しました: {str(e)}")


@router.get("/detail")
async def get_problem_detail(
    exam_type: str = Query(..., description="試験区分"),
    problem_id: str = Query(..., description="問題ID")
):
    """
    問題詳細を取得
    
    Args:
        exam_type: 試験区分
        problem_id: 問題ID
    
    Returns:
        問題詳細データ
    """
    try:
        response = exam_table.get_item(
            Key={
                "PK": f"EXAM#{exam_type}",
                "SK": problem_id
            }
        )
        
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="問題が見つかりません")
        
        # 問題データを整形
        problem_data = {
            "exam_type": exam_type,
            "problem_id": problem_id,
            "title": item.get("title", ""),
            "year_term": item.get("year_term", ""),
            "problem_content": item.get("problem_content", ""),
            "problem_question": item.get("problem_question", {}),
            "time_limit_minutes": item.get("time_limit_minutes", 120),
            "word_count_limits": item.get("word_count_limits", {}),
        }
        
        return problem_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"問題詳細の取得に失敗しました: {str(e)}")


@router.get("/partial/list", response_class=HTMLResponse)
async def get_exams_partial(exam_type: str = Query(default="IS")):
    """
    試験一覧のHTMLパーシャル（htmx用）
    """
    from fastapi.templating import Jinja2Templates
    from starlette.requests import Request
    
    templates = Jinja2Templates(directory="templates")
    
    try:
        response = exam_table.query(
            KeyConditionExpression=Key("PK").eq(f"EXAM#{exam_type}")
        )
        
        items = response.get("Items", [])
        exams = []
        for item in items:
            exams.append({
                "problem_id": item.get("SK"),
                "title": item.get("title", ""),
                "year_term": item.get("year_term", ""),
                "exam_type": exam_type,
            })
        
        exams.sort(key=lambda x: x.get("year_term", ""), reverse=True)
        
        # HTMLパーシャルを返す
        # URLエンコードが必要（SKに#が含まれる）
        from urllib.parse import quote
        
        html_content = ""
        for exam in exams:
            # problem_idをURLエンコード
            encoded_problem_id = quote(exam["problem_id"], safe="")
            html_content += f'''
            <a href="/exam/{exam["exam_type"]}/{encoded_problem_id}" 
               class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow cursor-pointer">
                <div class="card-body">
                    <h3 class="card-title text-base">{exam["title"]}</h3>
                    <p class="text-sm text-base-content/70">{exam["year_term"]}</p>
                </div>
            </a>
            '''
        
        if not exams:
            html_content = '<p class="text-center text-base-content/50 py-8">該当する試験がありません</p>'
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(
            content=f'<p class="text-error">エラー: {str(e)}</p>',
            status_code=500
        )
