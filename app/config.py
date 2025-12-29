"""
Scribo アプリケーション設定
環境変数から設定を読み込む
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # AWS設定
    aws_region: str = "ap-northeast-1"
    
    # DynamoDB テーブル名
    dynamodb_exam_table: str = "scribo-ipa"
    dynamodb_submission_table: str = "BackendStack-SubmissionTable33F44FF8-18BO8KQ7XEI4V"
    dynamodb_modules_table: str = "ModulesTable"
    dynamodb_designs_table: str = "DesignsTable"
    dynamodb_interview_session_table: str = "InterviewSessionsTable"
    
    # Bedrock モデル設定
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # アプリケーション設定
    app_name: str = "Scribo"
    app_description: str = "IPA午後Ⅱ論述式試験 学習支援アプリケーション"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを返す"""
    return Settings()
