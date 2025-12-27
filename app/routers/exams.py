"""
試験データ API ルーター
既存DynamoDB (scribo-ipa) から試験一覧・問題詳細を取得
S3から問題本文を取得
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import boto3
from boto3.dynamodb.conditions import Key
import json

from config import get_settings

router = APIRouter()
settings = get_settings()

# AWS クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
exam_table = dynamodb.Table(settings.dynamodb_exam_table)
s3_client = boto3.client("s3", region_name=settings.aws_region)

# S3問題データのキャッシュ（アプリ起動中のみ）
_s3_problem_cache: dict = {}


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
        problem_id: 問題ID (例: YEAR#2025SPRING#ESSAY#Q1)
    
    Returns:
        問題詳細データ
    """
    try:
        # DynamoDBからメタデータを取得
        response = exam_table.get_item(
            Key={
                "PK": f"EXAM#{exam_type}",
                "SK": problem_id
            }
        )
        
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="問題が見つかりません")
        
        # S3 URIから問題本文を取得
        s3_uri = item.get("s3_uri", "")
        problem_content = ""
        problem_question = {}
        word_count_limits = {}
        
        if s3_uri:
            # S3 URIをパース (例: s3://scribo-essay-evaluator/ST/is_essay.json)
            s3_parts = s3_uri.replace("s3://", "").split("/", 1)
            if len(s3_parts) == 2:
                bucket_name = s3_parts[0]
                object_key = s3_parts[1]
                
                # キャッシュを確認
                cache_key = f"{bucket_name}/{object_key}"
                if cache_key not in _s3_problem_cache:
                    try:
                        s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                        s3_data = json.loads(s3_response["Body"].read().decode("utf-8"))
                        _s3_problem_cache[cache_key] = s3_data
                    except Exception as e:
                        print(f"S3からのデータ取得エラー: {e}")
                        _s3_problem_cache[cache_key] = []
                
                s3_problems = _s3_problem_cache.get(cache_key, [])
                
                # DynamoDBのSKをS3のquestion_idに変換
                # SK: YEAR#2025SPRING#ESSAY#Q1 → S3 question_id: IS#YEAR#2025SPRING#ESSAY#Q1
                s3_question_id = f"{exam_type}#{problem_id}"
                
                # 該当する問題を検索
                for problem in s3_problems:
                    if problem.get("question_id") == s3_question_id:
                        problem_content = problem.get("problemContent", "")
                        problem_question = problem.get("problemQuestion", {})
                        break
        
        # 文字数制限のデフォルト値
        if not word_count_limits:
            word_count_limits = {
                "設問ア": {"min": 600, "max": 800},
                "設問イ": {"min": 700, "max": 1000},
                "設問ウ": {"min": 600, "max": 800}
            }
        
        # 問題データを整形
        problem_data = {
            "exam_type": exam_type,
            "problem_id": problem_id,
            "title": item.get("title", ""),
            "year_term": item.get("year_term", ""),
            "problem_content": problem_content,
            "problem_question": problem_question,
            "time_limit_minutes": item.get("time_limit_minutes", 120),
            "word_count_limits": word_count_limits,
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
