import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

let bedrockSendMock: jest.Mock;
let docClientSendMock: jest.Mock;
const QUESTION_KEY = '設問ア';

jest.mock('@aws-sdk/client-bedrock-runtime', () => {
  bedrockSendMock = jest.fn();
  return {
    BedrockRuntimeClient: jest.fn().mockImplementation(() => ({
      send: bedrockSendMock,
    })),
    InvokeModelCommand: jest.fn().mockImplementation((input) => input),
  };
});

jest.mock('@aws-sdk/lib-dynamodb', () => {
  docClientSendMock = jest.fn();
  return {
    DynamoDBDocumentClient: {
      from: jest.fn().mockReturnValue({
        send: docClientSendMock,
      }),
    },
    GetCommand: jest.fn().mockImplementation((input) => input),
    PutCommand: jest.fn().mockImplementation((input) => input),
  };
});

jest.mock('@aws-sdk/client-dynamodb', () => {
  return {
    DynamoDBClient: jest.fn().mockImplementation(() => ({})),
  };
});

const { handler } = require('../src/lambda/scoring/index');

describe('scoring lambda e2e (mocked)', () => {
  beforeAll(() => {
    process.env.TABLE_NAME = 'mock-table';
    process.env.AWS_REGION = 'ap-northeast-1';
  });

  beforeEach(() => {
    jest.clearAllMocks();

    docClientSendMock.mockResolvedValueOnce({ Item: undefined });
    docClientSendMock.mockResolvedValueOnce({});

    const mockPayload = {
      question_breakdown: {
        [QUESTION_KEY]: {
          criteria_scores: [
            { criterion: '充足度', weight: 20, points: 18, comment: 'solid' },
            { criterion: '論述の具体性', weight: 15, points: 12, comment: 'ok' },
            { criterion: '内容の妥当性', weight: 15, points: 13, comment: 'reasonable' },
            { criterion: '論理の一貫性', weight: 15, points: 12, comment: 'coherent' },
            { criterion: '見識に基づく主張', weight: 10, points: 8, comment: 'fair' },
            { criterion: '洞察力・行動力', weight: 10, points: 7, comment: 'needs more' },
            { criterion: '独創性・先見性', weight: 5, points: 4, comment: 'good' },
            { criterion: '表現力・文章作成能力', weight: 10, points: 8, comment: 'clear' },
          ],
        },
      },
      feedback: {
        strengths: ['構成が明瞭'],
        improvements: ['事例を増やす'],
        notes: '全体的に良好',
      },
    };

    bedrockSendMock.mockResolvedValue({
      body: new TextEncoder().encode(
        JSON.stringify({
          content: [
            {
              type: 'text',
              text: JSON.stringify(mockPayload),
            },
          ],
        })
      ),
    });
  });

  it('returns scored response and persists result', async () => {
    const event: Partial<APIGatewayProxyEvent> = {
      body: JSON.stringify({
        submission_id: 'sub-123',
        exam_type: 'IS',
        problem_id: 'is-2024-a',
        submitted_at: new Date().toISOString(),
        answers: {
          [QUESTION_KEY]: '回答内容',
        },
      }),
    };

    const result = await handler(event as APIGatewayProxyEvent, {} as any, () => {}) as APIGatewayProxyResult;

    expect(result.statusCode).toBe(200);
    const parsed = JSON.parse(result.body);
    expect(parsed.submission_id).toBe('sub-123');
    expect(parsed.final_rank).toBeDefined();
    expect(bedrockSendMock).toHaveBeenCalledTimes(1);
    expect(docClientSendMock).toHaveBeenCalledTimes(2);
  });
});
