import json
import boto3
from boto3.dynamodb.conditions import Key
import os

# DynamoDBテーブル名を環境変数で指定
TABLE_NAME = os.environ.get('TABLE_NAME', 'scribo-ipa')
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    event : {
        "exam_type": "IS",
        "limit": 20,
        "last_evaluated_key": {...} # ページネーション用
    }
    """

    # クエリパラメータからexam_typeを取得
    if 'queryStringParameters' in event and event['queryStringParameters']:
        exam_type = event['queryStringParameters'].get('exam_type')
    else:
        exam_type = None

    # exam_typeが指定されていない場合
    if not exam_type:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': json.dumps({'error': 'exam_type is required'})
        }

    # DynamoDBのキー値
    pk_value = f'EXAM#{exam_type}'
    
    limit = int(event.get('limit', 20)) if isinstance(event.get('limit'), (int, str)) else 20
    last_evaluated_key = event.get('last_evaluated_key', None)

    query_params = {
        'KeyConditionExpression': Key('PK').eq(pk_value),
        'ProjectionExpression': 'PK, SK, exam_type, title, year_term, question_id',
        'Limit': limit,
    }

    if last_evaluated_key:
        query_params['ExclusiveStartKey'] = last_evaluated_key

    response = table.query(**query_params)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
        'body': json.dumps({
            'items': response.get('Items', []),
            'last_evaluated_key': response.get('LastEvaluatedKey', None),
        }, ensure_ascii=False)
    }
