import { APIGatewayProxyHandler } from 'aws-lambda';
import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb';

const bedrock = new BedrockRuntimeClient({ region: process.env.AWS_REGION });
const dynamo = new DynamoDBClient({ region: process.env.AWS_REGION });
const docClient = DynamoDBDocumentClient.from(dynamo);

const TABLE_NAME = process.env.TABLE_NAME!;
const MODEL_ID = process.env.MODEL_ID || 'anthropic.claude-3-5-sonnet-20240620-v1:0';
const MODEL_PRICING = {
  inputPer1KTokensUsd: 0.003,
  outputPer1KTokensUsd: 0.015,
};
const MAX_IDEMPOTENCY_RETRIES = 2;
const IDEMPOTENCY_BACKOFF_MS = 150;

interface ScoringRequest {
  exam_type: string;
  problem_id: string;
  submission_id: string;
  submitted_at: string;
  answers: { [key: string]: string };
  instruction_compliance?: {
    followed: boolean;
    violations: string[];
  };
  metadata?: any;
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const fetchCachedResult = async (submissionId: string) => {
  for (let attempt = 1; attempt <= MAX_IDEMPOTENCY_RETRIES; attempt++) {
    try {
      const getResult = await docClient.send(new GetCommand({
        TableName: TABLE_NAME,
        Key: { submission_id: submissionId },
      }));

      return {
        cachedResult: getResult.Item?.result,
        healthy: true,
      };
    } catch (error) {
      console.warn('Idempotency lookup failed', { submissionId, attempt, error });
      if (attempt === MAX_IDEMPOTENCY_RETRIES) {
        return { cachedResult: undefined, healthy: false };
      }
      await sleep(IDEMPOTENCY_BACKOFF_MS * attempt);
    }
  }

  return { cachedResult: undefined, healthy: false };
};

const extractModelJson = (text: string) => {
  const trimmed = text.trim();
  try {
    return JSON.parse(trimmed);
  } catch (_) {
    const start = trimmed.indexOf('{');
    const end = trimmed.lastIndexOf('}');
    if (start === -1 || end === -1 || end <= start) {
      return null;
    }
    try {
      return JSON.parse(trimmed.slice(start, end + 1));
    } catch (innerError) {
      console.error('Secondary JSON parse failed', innerError);
      return null;
    }
  }
};

const buildResponse = (statusCode: number, body: unknown) => ({
  statusCode,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  },
  body: JSON.stringify(body),
});

export const handler: APIGatewayProxyHandler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));

  if (!event.body) {
    return buildResponse(400, { message: 'Missing body' });
  }

  let request: ScoringRequest;
  try {
    request = JSON.parse(event.body);
  } catch (e) {
    return buildResponse(400, { message: 'Invalid JSON' });
  }

  const { submission_id, answers, problem_id } = request;

  if (!submission_id || !answers) {
    return buildResponse(400, { message: 'Missing required fields' });
  }

  // 1. Check Idempotency with graceful fallback when DynamoDB is unhealthy
  const { cachedResult, healthy: cacheHealthy } = await fetchCachedResult(submission_id);
  if (!cacheHealthy) {
    console.warn('Proceeding without idempotency cache due to repeated DynamoDB errors');
  }

  if (cachedResult) {
    console.log('Returning cached result for:', submission_id);
    return buildResponse(200, cachedResult);
  }

  // 2. Call Bedrock
  const prompt = `
You are an expert grader for the IPA IT Strategist Examination (午後II 論述式).
Your task is to score the following essay answers based on 8 specific criteria.

Problem ID: ${problem_id}

Answers:
${Object.entries(answers).map(([k, v]) => `[${k}]\n${v}`).join('\n\n')}

Criteria (Total 100 points per question):
1. 充足度 (Weight: 20)
2. 論述の具体性 (Weight: 15)
3. 内容の妥当性 (Weight: 15)
4. 論理の一貫性 (Weight: 15)
5. 見識に基づく主張 (Weight: 10)
6. 洞察力・行動力 (Weight: 10)
7. 独創性・先見性 (Weight: 5)
8. 表現力・文章作成能力 (Weight: 10)

Output Format:
Return a JSON object strictly following this structure. Do not include any markdown formatting or explanation outside the JSON.

{
  "question_breakdown": {
    "設問ア": {
      "criteria_scores": [
        { "criterion": "充足度", "weight": 20, "points": number, "comment": "string" },
        ... (all 8 criteria)
      ]
    },
    "設問イ": { ... },
    "設問ウ": { ... }
  },
  "feedback": {
    "strengths": ["string"],
    "improvements": ["string"],
    "notes": "string"
  }
}

Ensure the "points" for each criterion are between 0 and "weight".
Evaluate strictly but fairly.
`;

  try {
    const llmStart = Date.now();
    const bedrockResponse = await bedrock.send(new InvokeModelCommand({
      modelId: MODEL_ID,
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify({
        anthropic_version: 'bedrock-2023-05-31',
        max_tokens: 4096,
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: prompt,
              }
            ]
          }
        ]
      }),
    }));

    const responseBody = JSON.parse(new TextDecoder().decode(bedrockResponse.body));
    const textBlocks = Array.isArray(responseBody.content)
      ? responseBody.content
          .filter((block: any) => block.type === 'text' && typeof block.text === 'string')
          .map((block: any) => block.text)
          .join('\n')
          .trim()
      : '';

    const usage = responseBody.usage || {};
    const inputTokens = usage.input_tokens ?? usage.inputTokens ?? 0;
    const outputTokens = usage.output_tokens ?? usage.outputTokens ?? 0;
    const estimatedCostUsd = parseFloat(((inputTokens / 1000) * MODEL_PRICING.inputPer1KTokensUsd
      + (outputTokens / 1000) * MODEL_PRICING.outputPer1KTokensUsd).toFixed(6));
    console.log('Bedrock usage metrics', {
      submission_id,
      inputTokens,
      outputTokens,
      estimatedCostUsd,
    });

    if (!textBlocks) {
      console.error('Empty content array from model', responseBody);
      return buildResponse(502, { message: 'Model returned empty response' });
    }

    const llmResult = extractModelJson(textBlocks);
    if (!llmResult) {
      console.error('Unable to parse structured JSON from model output', textBlocks);
      return buildResponse(502, { message: 'Model output was not valid JSON' });
    }

    // 3. Calculate Aggregates
    // Helper to calculate question score and level
    const calculateQuestionStats = (breakdown: any) => {
      const scores = breakdown.criteria_scores;
      const total = scores.reduce((sum: number, c: any) => sum + c.points, 0);
      let level = 'D';
      if (total >= 70) level = 'A';
      else if (total >= 60) level = 'B';
      else if (total >= 50) level = 'C';
      
      return { ...breakdown, question_score: total, level };
    };

    const processedBreakdown: any = {};
    let weightedSum = 0;
    const weights = { "設問ア": 4, "設問イ": 8, "設問ウ": 6 };
    let totalWeight = 0;

    for (const key of Object.keys(llmResult.question_breakdown)) {
      const stats = calculateQuestionStats(llmResult.question_breakdown[key]);
      // Add word count from request if available, or estimate? 
      // Request has metadata.word_counts. We'll just pass through or use 0.
      stats.word_count = request.metadata?.word_counts?.[key] || 0;
      
      processedBreakdown[key] = stats;

      if (key in weights) {
        weightedSum += stats.question_score * (weights as any)[key];
        totalWeight += (weights as any)[key];
      }
    }

    const aggregateScore = totalWeight > 0 ? weightedSum / totalWeight : 0;
    const finalRank = aggregateScore >= 70 ? 'A' : aggregateScore >= 60 ? 'B' : aggregateScore >= 50 ? 'C' : 'D';

    const finalResult = {
      submission_id,
      problem_id,
      instruction_compliance: request.instruction_compliance || { followed: true, violations: [] },
      question_breakdown: processedBreakdown,
      aggregate_score: parseFloat(aggregateScore.toFixed(2)),
      final_rank: finalRank,
      passed: finalRank === 'A',
      feedback: llmResult.feedback,
      model_metadata: {
        engine: MODEL_ID,
        latency_ms: Date.now() - llmStart,
        confidence: 0.8, // Placeholder
        token_usage: {
          input_tokens: inputTokens,
          output_tokens: outputTokens,
          estimated_cost_usd: estimatedCostUsd,
          pricing_rates_per_1k: {
            input: MODEL_PRICING.inputPer1KTokensUsd,
            output: MODEL_PRICING.outputPer1KTokensUsd,
          },
        },
      }
    };

    // 4. Save to DynamoDB
    await docClient.send(new PutCommand({
      TableName: TABLE_NAME,
      Item: {
        submission_id,
        problem_id,
        created_at: new Date().toISOString(),
        result: finalResult,
        // Store raw input/output if needed for debugging
      }
    }));

    return buildResponse(200, finalResult);

  } catch (error) {
    console.error('Scoring Error:', error);
    return buildResponse(500, { message: 'Internal Server Error (Scoring)', error: String(error) });
  }
};
