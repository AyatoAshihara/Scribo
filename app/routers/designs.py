"""
論文設計 (Design) 管理 API ルーター
DynamoDB (DesignsTable) に設計図を保存・取得
"""

from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

from config import get_settings

router = APIRouter()
settings = get_settings()

# DynamoDB クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
designs_table = dynamodb.Table(settings.dynamodb_designs_table)

# 仮のユーザーID
DEMO_USER_ID = "demo-user"


# =============================================================================
# データモデル
# =============================================================================

class DesignBase(BaseModel):
    theme: str = Field(default="", description="論文のテーマ・骨子")
    breakdown: Dict[str, Any] = Field(default={}, description="設問分解データ")
    structure: List[Dict[str, Any]] = Field(default=[], description="章構成データ")
    module_map: Dict[str, List[str]] = Field(default={}, description="章ごとのモジュール割当")

class DesignCreate(DesignBase):
    exam_id: str = Field(..., description="対象の問題ID")

class DesignUpdate(DesignBase):
    pass

class DesignResponse(DesignBase):
    user_id: str
    exam_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# =============================================================================
# API エンドポイント
# =============================================================================

@router.get("/", response_model=List[DesignResponse])
async def list_designs():
    """ユーザーの設計図一覧を取得"""
    try:
        response = designs_table.query(
            KeyConditionExpression=Key('user_id').eq(DEMO_USER_ID)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error listing designs: {e}")
        raise HTTPException(status_code=500, detail="設計図一覧の取得に失敗しました")


@router.get("/{exam_id}", response_model=DesignResponse)
async def get_design(exam_id: str = Path(..., description="問題ID")):
    """設計図を取得"""
    try:
        response = designs_table.get_item(
            Key={
                'user_id': DEMO_USER_ID,
                'exam_id': exam_id
            }
        )
        item = response.get('Item')
        
        if not item:
            # 存在しない場合は空の設計図を返す（フロントエンドで新規作成扱い）
            return {
                "user_id": DEMO_USER_ID,
                "exam_id": exam_id,
                "theme": "",
                "breakdown": {},
                "structure": [],
                "module_map": {},
                "created_at": "",
                "updated_at": ""
            }
            
        return item
    except Exception as e:
        print(f"Error getting design: {e}")
        raise HTTPException(status_code=500, detail="設計図の取得に失敗しました")


@router.post("", response_model=DesignResponse)
async def save_design(design: DesignCreate):
    """設計図を保存（作成・更新）"""
    try:
        now = datetime.now().isoformat()
        
        # 既存データの確認（作成日時維持のため）
        try:
            existing_response = designs_table.get_item(
                Key={'user_id': DEMO_USER_ID, 'exam_id': design.exam_id}
            )
            existing_item = existing_response.get('Item')
            created_at = existing_item['created_at'] if existing_item else now
        except:
            created_at = now

        item = {
            "user_id": DEMO_USER_ID,
            "exam_id": design.exam_id,
            "theme": design.theme,
            "breakdown": design.breakdown,
            "structure": design.structure,
            "module_map": design.module_map,
            "created_at": created_at,
            "updated_at": now
        }
        
        designs_table.put_item(Item=item)
        return item
    except Exception as e:
        print(f"Error saving design: {e}")
        raise HTTPException(status_code=500, detail="設計図の保存に失敗しました")
