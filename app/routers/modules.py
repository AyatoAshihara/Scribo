"""
準備モジュール (Assets) 管理 API ルーター
DynamoDB (ModulesTable) にモジュールを保存・取得
"""

from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import boto3
from boto3.dynamodb.conditions import Key
import uuid
from datetime import datetime
import json

from config import get_settings

router = APIRouter()
settings = get_settings()

# DynamoDB クライアント
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
modules_table = dynamodb.Table(settings.dynamodb_modules_table)
# Bedrock Runtime クライアント
bedrock_runtime = boto3.client("bedrock-runtime", region_name=settings.aws_region)

# 仮のユーザーID（認証実装まで固定）
DEMO_USER_ID = "demo-user"


# =============================================================================
# データモデル
# =============================================================================

class ModuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="モジュールタイトル")
    category: str = Field(..., description="カテゴリ (背景/課題/解決策/効果/その他)")
    content: str = Field(..., min_length=1, max_length=2000, description="モジュール内容")
    tags: List[str] = Field(default=[], description="タグリスト")

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    tags: Optional[List[str]] = None

class ModuleResponse(ModuleBase):
    module_id: str
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="リライト対象のテキスト")
    category: str = Field(..., description="カテゴリ (背景/課題/解決策/効果)")


# =============================================================================
# テンプレートデータ
# =============================================================================

TEMPLATE_MODULES = [
    {
        "title": "A社（中堅物流企業）の事業概要",
        "category": "背景",
        "content": "A社は売上高500億円の中堅物流企業である。主要顧客は大手EC事業者であり、多品種少量の配送ニーズが急増している。しかし、倉庫内作業は人手に頼る部分が多く、労働力不足が深刻な課題となっている。経営戦略として「デジタル技術を活用した業務効率化と配送品質の向上」を掲げている。",
        "tags": ["物流", "人手不足", "DX"]
    },
    {
        "title": "レガシーシステムによるデータ連携の遅延",
        "category": "課題",
        "content": "現行の在庫管理システムは20年前に構築されたオンプレミスのレガシーシステムであり、配送管理システムとのデータ連携がバッチ処理（1日1回）で行われている。このため、リアルタイムな在庫状況が把握できず、受注時の欠品や過剰在庫が発生している。また、システム保守の属人化も進んでおり、改修に多大な時間とコストを要している。",
        "tags": ["レガシーシステム", "データ連携", "リアルタイム性"]
    },
    {
        "title": "クラウドERP導入とAPI連携基盤の構築",
        "category": "解決策",
        "content": "レガシーシステムを刷新し、クラウドベースのERPパッケージを導入することを提案した。同時に、各システム間を疎結合に連携させるためのAPI連携基盤を構築し、在庫情報のリアルタイム更新を実現するアーキテクチャを採用した。移行においては、業務への影響を最小限に抑えるため、段階的な移行計画（ストラングラーパターン）を策定した。",
        "tags": ["クラウド移行", "ERP", "API連携", "段階的移行"]
    },
    {
        "title": "在庫回転率の向上と顧客満足度の改善",
        "category": "効果",
        "content": "新システムの導入により、在庫情報のリアルタイム可視化が実現し、在庫回転率が従来比で15%向上した。また、欠品による機会損失が大幅に減少し、顧客からのクレーム件数も30%削減された。さらに、システム保守コストも20%削減され、IT部門のリソースを戦略的なDX推進にシフトすることが可能となった。",
        "tags": ["KPI達成", "コスト削減", "顧客満足度"]
    }
]


# =============================================================================
# API エンドポイント
# =============================================================================

@router.get("", response_model=List[ModuleResponse])
async def list_modules():
    """モジュール一覧を取得"""
    try:
        response = modules_table.query(
            KeyConditionExpression=Key('user_id').eq(DEMO_USER_ID)
        )
        items = response.get('Items', [])
        # 作成日時の降順でソート
        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return items
    except Exception as e:
        print(f"Error listing modules: {e}")
        raise HTTPException(status_code=500, detail="モジュールの取得に失敗しました")


@router.post("", response_model=ModuleResponse)
async def create_module(module: ModuleCreate):
    """新規モジュールを作成"""
    try:
        now = datetime.now().isoformat()
        module_id = str(uuid.uuid4())
        
        item = {
            "user_id": DEMO_USER_ID,
            "module_id": module_id,
            "title": module.title,
            "category": module.category,
            "content": module.content,
            "tags": module.tags,
            "created_at": now,
            "updated_at": now
        }
        
        modules_table.put_item(Item=item)
        return item
    except Exception as e:
        print(f"Error creating module: {e}")
        raise HTTPException(status_code=500, detail="モジュールの作成に失敗しました")


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(module_id: str = Path(..., description="モジュールID")):
    """モジュール詳細を取得"""
    try:
        response = modules_table.get_item(
            Key={
                'user_id': DEMO_USER_ID,
                'module_id': module_id
            }
        )
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="モジュールが見つかりません")
        return item
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting module: {e}")
        raise HTTPException(status_code=500, detail="モジュールの取得に失敗しました")


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_update: ModuleUpdate,
    module_id: str = Path(..., description="モジュールID")
):
    """モジュールを更新"""
    try:
        # 既存アイテムの確認
        existing = await get_module(module_id)
        
        # 更新式の構築
        update_expression = "set updated_at = :updated_at"
        expression_attribute_values = {
            ":updated_at": datetime.now().isoformat()
        }
        expression_attribute_names = {}
        
        if module_update.title is not None:
            update_expression += ", #t = :title"
            expression_attribute_names["#t"] = "title"
            expression_attribute_values[":title"] = module_update.title
            
        if module_update.category is not None:
            update_expression += ", category = :category"
            expression_attribute_values[":category"] = module_update.category
            
        if module_update.content is not None:
            update_expression += ", content = :content"
            expression_attribute_values[":content"] = module_update.content
            
        if module_update.tags is not None:
            update_expression += ", tags = :tags"
            expression_attribute_values[":tags"] = module_update.tags

        response = modules_table.update_item(
            Key={
                'user_id': DEMO_USER_ID,
                'module_id': module_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )
        
        return response.get('Attributes')
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating module: {e}")
        raise HTTPException(status_code=500, detail="モジュールの更新に失敗しました")


@router.delete("/{module_id}")
async def delete_module(module_id: str = Path(..., description="モジュールID")):
    """モジュールを削除"""
    try:
        modules_table.delete_item(
            Key={
                'user_id': DEMO_USER_ID,
                'module_id': module_id
            }
        )
        return {"message": "Module deleted successfully"}
    except Exception as e:
        print(f"Error deleting module: {e}")
        raise HTTPException(status_code=500, detail="モジュールの削除に失敗しました")


@router.post("/seed", response_model=List[ModuleResponse])
async def seed_modules():
    """テンプレートデータを投入（デモ用）"""
    try:
        created_items = []
        now = datetime.now().isoformat()
        
        for tmpl in TEMPLATE_MODULES:
            module_id = str(uuid.uuid4())
            item = {
                "user_id": DEMO_USER_ID,
                "module_id": module_id,
                "title": tmpl["title"],
                "category": tmpl["category"],
                "content": tmpl["content"],
                "tags": tmpl["tags"],
                "created_at": now,
                "updated_at": now
            }
            modules_table.put_item(Item=item)
            created_items.append(item)
            
        return created_items
    except Exception as e:
        print(f"Error seeding modules: {e}")
        raise HTTPException(status_code=500, detail="テンプレートデータの投入に失敗しました")


@router.post("/rewrite")
async def rewrite_content(request: RewriteRequest):
    """AIによるリライティング（論文調への変換）"""
    try:
        prompt = f"""
あなたはITストラテジスト試験の合格論文を書くプロフェッショナルです。
以下のテキストを、ITストラテジスト試験の論文としてふさわしい表現にリライトしてください。

【要件】
1. 「だ・である」調で統一すること。
2. 具体的かつ定量的な表現を用いること（数値や固有名詞を補完するプレースホルダーを含めても良い）。
3. 論理的で説得力のある文章にすること。
4. カテゴリ「{request.category}」に適した文脈で書くこと。
5. 出力はリライト後のテキストのみとすること。

【元のテキスト】
{request.text}
"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        response = bedrock_runtime.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        rewritten_text = response_body['content'][0]['text']
        
        return {"rewritten_text": rewritten_text.strip()}
        
    except Exception as e:
        print(f"Error rewriting content: {e}")
        raise HTTPException(status_code=500, detail="AIリライティングに失敗しました")
