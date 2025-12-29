import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from typing import Optional
import json

from config import get_settings
from models.interview import InterviewSession, ChatMessage, Role, DesignProposal

settings = get_settings()

class InterviewService:
    _bedrock_runtime = None
    _dynamodb_resource = None
    _table = None

    def __init__(self):
        if InterviewService._dynamodb_resource is None:
            InterviewService._dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
            InterviewService._table = InterviewService._dynamodb_resource.Table(settings.dynamodb_interview_session_table)
        
        if InterviewService._bedrock_runtime is None:
            InterviewService._bedrock_runtime = boto3.client("bedrock-runtime", region_name=settings.aws_region)

        self.dynamodb = InterviewService._dynamodb_resource
        self.table = InterviewService._table
        self.bedrock_runtime = InterviewService._bedrock_runtime

    def get_session(self, user_id: str, exam_id: str) -> Optional[InterviewSession]:
        try:
            response = self.table.get_item(
                Key={
                    "user_id": user_id,
                    "exam_id": exam_id
                }
            )
            item = response.get("Item")
            if not item:
                return None
            
            return InterviewSession(**item)
        except Exception as e:
            print(f"Error fetching session: {e}")
            return None

    def create_session(self, user_id: str, exam_id: str) -> InterviewSession:
        # Initial greeting
        initial_message = ChatMessage(
            role=Role.ASSISTANT,
            content="こんにちは！Scribo AIインタビューへようこそ。\nまずは、この論文で取り組みたいテーマや、想定している業務背景について教えていただけますか？"
        )

        session = InterviewSession(
            user_id=user_id,
            exam_id=exam_id,
            history=[initial_message],
            status="active"
        )
        self.save_session(session)
        return session

    def save_session(self, session: InterviewSession):
        # Convert to dict using Pydantic's model_dump(mode='json') to handle datetime serialization
        item = session.model_dump(mode='json')
        # Ensure updated_at is current
        item["updated_at"] = datetime.now().isoformat()
        
        self.table.put_item(Item=item)

    def add_message(self, user_id: str, exam_id: str, message: ChatMessage) -> InterviewSession:
        session = self.get_session(user_id, exam_id)
        if not session:
            session = self.create_session(user_id, exam_id)
        
        session.history.append(message)
        session.updated_at = datetime.now()
        self.save_session(session)
        return session

    def update_proposal(self, user_id: str, exam_id: str, proposal: DesignProposal) -> InterviewSession:
        session = self.get_session(user_id, exam_id)
        if not session:
            raise ValueError("Session not found")
            
        session.current_proposal = proposal
        session.updated_at = datetime.now()
        self.save_session(session)
        return session

    def generate_stream(self, user_id: str, exam_id: str, message_text: str):
        """
        ユーザーメッセージを受け取り、Bedrock (Claude) からのストリーミング応答を生成するジェネレータ。
        完了時にセッション履歴を更新する。
        """
        # 1. セッション取得・作成
        session = self.get_session(user_id, exam_id)
        if not session:
            session = self.create_session(user_id, exam_id)

        # 2. ユーザーメッセージ追加・保存
        user_message = ChatMessage(role=Role.USER, content=message_text)
        session.history.append(user_message)
        self.save_session(session)

        # 3. プロンプト構築
        system_prompt = """
あなたはIPA（情報処理推進機構）のITストラテジスト試験の論文対策を支援するAIメンターです。
ユーザー（受験者）との対話を通じて、合格レベルの論文設計（骨子）を作成することが目標です。

以下のステップで対話を進めてください：
1. **テーマ設定**: どのような業務、どのような課題、どのようなITソリューションを扱うかを確認する。
2. **状況把握**: 企業の概要、立場、具体的な課題の背景を深掘りする。
3. **施策検討**: 課題解決のためのIT戦略、導入プロセス、リスク対策などを具体化する。
4. **評価**: 施策の成果、残された課題、今後の展望を整理する。

**振る舞いのルール**:
- 一度に多くの質問をせず、1つずつ丁寧に掘り下げてください。
- ユーザーの回答が曖昧な場合は、具体例を挙げたり、選択肢を提示したりして誘導してください。
- 常に「ITストラテジスト」としての視点（経営への貢献、リーダーシップ）を意識させてください。
- 励ましつつも、論理的な矛盾や具体性不足には鋭く指摘してください。
"""

        messages = []
        for msg in session.history:
            # Systemロールはmessages配列に含めず、APIのsystemパラメータに渡す
            if msg.role == Role.SYSTEM:
                continue
            role = "user" if msg.role == Role.USER else "assistant"
            messages.append({"role": role, "content": msg.content})

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": messages
        })

        # 4. Bedrock呼び出し (ストリーミング)
        try:
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=settings.bedrock_model_id,
                body=body
            )
        except Exception as e:
            print(f"Bedrock invocation failed: {e}")
            yield f"エラーが発生しました: {str(e)}"
            return

        stream = response.get('body')
        full_response_text = ""

        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_json = json.loads(chunk.get('bytes').decode())
                    if chunk_json['type'] == 'content_block_delta':
                         text_delta = chunk_json['delta']['text']
                         full_response_text += text_delta
                         yield text_delta
        
        # 5. AI応答の保存
        ai_message = ChatMessage(role=Role.ASSISTANT, content=full_response_text)
        session.history.append(ai_message)
        self.save_session(session)

    def generate_design_proposal(self, user_id: str, exam_id: str) -> DesignProposal:
        session = self.get_session(user_id, exam_id)
        if not session:
            raise ValueError("Session not found")

        # Construct prompt from history
        conversation_text = ""
        for msg in session.history:
            role_label = "User" if msg.role == Role.USER else "Assistant"
            conversation_text += f"{role_label}: {msg.content}\n"

        system_prompt = """
        あなたはITストラテジスト試験の論文設計を支援するAIアシスタントです。
        これまでの会話履歴に基づいて、論文の設計書（Design Proposal）を作成してください。
        
        出力は以下のJSON形式のみとしてください。余計な説明は不要です。
        
        {
            "theme": "論文のテーマ",
            "breakdown": {
                "A": "設問アの概要",
                "B": "設問イの概要",
                "C": "設問ウの概要"
            },
            "structure": [
                {
                    "chapter": "第1章",
                    "title": "章のタイトル",
                    "sections": ["節1", "節2"]
                },
                ...
            ],
            "module_map": {
                "chapter1": ["module_id1", "module_id2"]
            },
            "reasoning": "この設計にした理由の簡単な説明"
        }
        """

        user_message = f"""
        以下の会話履歴に基づいて、論文設計書をJSON形式で出力してください。
        
        --- 会話履歴 ---
        {conversation_text}
        ----------------
        """

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.5
        })

        try:
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=settings.bedrock_model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            content_text = response_body.get("content")[0].get("text")
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
                
            proposal_data = json.loads(content_text)
            proposal = DesignProposal(**proposal_data)
            
            # Save to session
            self.update_proposal(user_id, exam_id, proposal)
            
            return proposal
            
        except Exception as e:
            print(f"Error generating design proposal: {e}")
            raise e
