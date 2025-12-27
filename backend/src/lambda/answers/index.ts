import { APIGatewayProxyHandler } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';

const dynamo = new DynamoDBClient({ region: process.env.AWS_REGION });
const docClient = DynamoDBDocumentClient.from(dynamo);
const TABLE_NAME = process.env.TABLE_NAME ?? '';

type AnswerMap = Record<string, string>;

interface AnswerSubmissionPayload {
  submission_id?: string;
  exam_type?: string;
  problem_id?: string;
  submitted_at?: string;
  answers?: AnswerMap;
  metadata?: Record<string, unknown>;
}

const buildResponse = (statusCode: number, body: unknown) => ({
  statusCode,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  },
  body: JSON.stringify(body),
});

export const handler: APIGatewayProxyHandler = async (event) => {
  if (!event.body) {
    return buildResponse(400, { message: 'Missing request body' });
  }

  let payload: AnswerSubmissionPayload;
  try {
    payload = JSON.parse(event.body);
  } catch (error) {
    return buildResponse(400, { message: 'Invalid JSON payload', error: String(error) });
  }

  const {
    submission_id,
    exam_type,
    problem_id,
    answers,
    submitted_at,
    metadata = {},
  } = payload;

  if (!submission_id || !exam_type || !problem_id || !answers) {
    return buildResponse(400, { message: 'submission_id, exam_type, problem_id, answers are required' });
  }

  if (!TABLE_NAME) {
    return buildResponse(500, { message: 'TABLE_NAME is not configured' });
  }

  const nowIso = new Date().toISOString();

  try {
    await docClient.send(new PutCommand({
      TableName: TABLE_NAME,
      Item: {
        submission_id,
        entity_type: 'answer_draft',
        exam_type,
        problem_id,
        answers,
        submitted_at: submitted_at ?? nowIso,
        stored_at: nowIso,
        metadata,
      },
    }));

    return buildResponse(200, {
      submission_id,
      stored_at: nowIso,
      status: 'saved',
    });
  } catch (error) {
    console.error('Failed to store answer', error);
    return buildResponse(500, { message: 'Failed to store answer', error: String(error) });
  }
};
