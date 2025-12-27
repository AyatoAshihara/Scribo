import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'scribo-ipa')
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client('s3')

cors_headers = {
    'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Credentials': 'true'
}

def lambda_handler(event, context):
    # OPTIONS request is handled by API Gateway, but if it reaches here:
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }

    if not event.get('queryStringParameters'):
         return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Missing query parameters'})
        }

    exam_type = event['queryStringParameters'].get('exam_type')
    problem_id = event['queryStringParameters'].get('problem_id')

    if not exam_type or not problem_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'exam_type and problem_id are required'})
        }

    pk = f'EXAM#{exam_type}'
    sk = problem_id

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(pk) &
                               boto3.dynamodb.conditions.Key('SK').eq(sk)
    )

    items = response.get('Items', [])
    item = items[0] if items else None

    if not item:
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Question not found'})
        }

    # S3からJSONを取得
    try:
        bucket, key = parse_s3_uri(item['s3_uri'])
        s3_obj = s3.get_object(Bucket=bucket, Key=key)
        content = s3_obj['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching from S3: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Failed to retrieve question content'})
        }

    # JSONをパース
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Invalid JSON format'})
        }
    
    key = f"{exam_type}#{problem_id}"

    # 配列を想定してquestion_idでフィルタ
    matched = None
    if isinstance(data, list):
        for item in data:
            if item.get('question_id') == key:
                matched = item
                break
    elif isinstance(data, dict):
        if data.get('question_id') == key:
            matched = data

    if not matched:
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Question not found'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps(matched, ensure_ascii=False),
        'headers': {
            'Content-Type': 'application/json; charset=utf-8',
            **cors_headers
        }
    }

def parse_s3_uri(uri: str):
    """s3://bucket/keyを(buket, key)に分解"""
    uri = uri.replace('s3://', '')
    parts = uri.split('/', 1)
    return parts[0], parts[1]