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
async def get_exams_partial(
    exam_type: str = Query(default="IS"),
    mode: str = Query(default="normal", description="表示モード (normal/select_design)")
):
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
            
            if mode == "select_design":
                # 設計選択モード: シンプルなリスト形式で選択しやすいUI
                html_content += f'''
                <a href="/design/{exam["exam_type"]}/{encoded_problem_id}" 
                   class="flex items-center justify-between p-4 bg-base-100 border border-base-200 rounded-xl hover:bg-primary-container hover:border-primary transition-colors group">
                    <div>
                        <div class="font-bold text-base-content group-hover:text-on-primary-container">{exam["title"]}</div>
                        <div class="text-xs text-base-content/60 group-hover:text-on-primary-container/80">{exam["year_term"]}</div>
                    </div>
                    <span class="material-symbols-rounded text-primary group-hover:text-on-primary-container">arrow_forward</span>
                </a>
                '''
            else:
                # 通常モード: カード形式
                html_content += f'''
                <div class="card-modern block">
                    <div class="card-body p-5">
                        <h3 class="card-title text-base font-semibold text-base-content">{exam["title"]}</h3>
                        <p class="text-sm text-base-content/70 mb-4">{exam["year_term"]}</p>
                        
                        <div class="flex gap-2 mt-auto">
                            <a href="/exam/{exam["exam_type"]}/{encoded_problem_id}" class="btn btn-sm btn-outline flex-1">
                                <span class="material-symbols-rounded text-sm">edit_note</span>
                                解答
                            </a>
                            <a href="/design/{exam["exam_type"]}/{encoded_problem_id}" class="btn btn-sm btn-primary flex-1">
                                <span class="material-symbols-rounded text-sm">architecture</span>
                                設計
                            </a>
                        </div>
                    </div>
                </div>
                '''
        
        if not exams:
            html_content = '<p class="text-center text-base-content/50 py-8">該当する試験がありません</p>'
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(
            content=f'<p class="text-error">エラー: {str(e)}</p>',
            status_code=500
        )
