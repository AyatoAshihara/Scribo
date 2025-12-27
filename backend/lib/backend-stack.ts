import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as path from 'path';

interface BackendStackProps extends cdk.StackProps {
  userPoolId: string;
}

export class BackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    // 1. DynamoDB Table
    const table = new dynamodb.Table(this, 'SubmissionTable', {
      partitionKey: { name: 'submission_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test, NOT for production
    });

    // 2. Lambda Functions
    const scoringFunction = new nodejs.NodejsFunction(this, 'ScoringFunction', {
      runtime: lambda.Runtime.NODEJS_20_X,
      entry: path.join(__dirname, '../src/lambda/scoring/index.ts'),
      handler: 'handler',
      environment: {
        TABLE_NAME: table.tableName,
        MODEL_ID: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
      },
      timeout: cdk.Duration.seconds(90), // LLM calls can be slow
      bundling: {
        minify: true,
        sourceMap: true,
      }
    });

    const answerSaveFunction = new nodejs.NodejsFunction(this, 'AnswerSaveFunction', {
      runtime: lambda.Runtime.NODEJS_20_X,
      entry: path.join(__dirname, '../src/lambda/answers/index.ts'),
      handler: 'handler',
      environment: {
        TABLE_NAME: table.tableName,
      },
      timeout: cdk.Duration.seconds(10),
      bundling: {
        minify: true,
        sourceMap: true,
      }
    });

    // Import existing DynamoDB table for exams
    const examTable = dynamodb.Table.fromTableName(this, 'ExamTable', 'scribo-ipa');

    // List Exams Function (Python)
    const listExamsFunction = new lambda.Function(this, 'ListExamsFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../src/lambda/exams/get_by_type')),
      environment: {
        TABLE_NAME: examTable.tableName,
        ALLOWED_ORIGIN: '*',
      },
      timeout: cdk.Duration.seconds(10),
    });

    // Get Exam Detail Function (Python)
    const getExamDetailFunction = new lambda.Function(this, 'GetExamDetailFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../src/lambda/exams/get_problem')),
      environment: {
        TABLE_NAME: examTable.tableName,
        ALLOWED_ORIGIN: '*',
      },
      timeout: cdk.Duration.seconds(10),
    });

    // Grant permissions
    table.grantReadWriteData(scoringFunction);
    table.grantReadWriteData(answerSaveFunction);
    examTable.grantReadData(listExamsFunction);
    examTable.grantReadData(getExamDetailFunction);
    
    // Grant S3 read access to GetExamDetailFunction (for fetching problem JSON)
    getExamDetailFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject'],
      resources: ['*'], // Restrict this if bucket name is known
    }));

    // Grant Bedrock access
    // Note: In a real production environment, restrict resources to the specific model ARN.
    scoringFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'], 
    }));

    // 3. API Gateway
    const api = new apigateway.RestApi(this, 'ScoringApi', {
      restApiName: 'Scribo Scoring Service',
    });

    api.addGatewayResponse('GatewayResponseDefault4XX', {
      type: apigateway.ResponseType.DEFAULT_4XX,
      responseHeaders: {
        'Access-Control-Allow-Origin': "'*'",
        'Access-Control-Allow-Headers': "'Content-Type,Authorization'",
      },
    });

    api.addGatewayResponse('GatewayResponseDefault5XX', {
      type: apigateway.ResponseType.DEFAULT_5XX,
      responseHeaders: {
        'Access-Control-Allow-Origin': "'*'",
        'Access-Control-Allow-Headers': "'Content-Type,Authorization'",
      },
    });

    const userPool = cognito.UserPool.fromUserPoolId(this, 'ScriboUserPool', props.userPoolId);
    const cognitoAuthorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'ScriboApiAuthorizer', {
      cognitoUserPools: [userPool],
    });

    const scoringIntegration = new apigateway.LambdaIntegration(scoringFunction);
    const scoringResource = api.root.addResource('scoring');
    scoringResource.addMethod('POST', scoringIntegration, {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    scoringResource.addCorsPreflight({
      allowOrigins: apigateway.Cors.ALL_ORIGINS,
      allowMethods: apigateway.Cors.ALL_METHODS,
      allowHeaders: ['Content-Type', 'Authorization'],
    });

    const answersIntegration = new apigateway.LambdaIntegration(answerSaveFunction);
    const answersResource = api.root.addResource('answers');
    answersResource.addMethod('POST', answersIntegration, {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    answersResource.addCorsPreflight({
      allowOrigins: apigateway.Cors.ALL_ORIGINS,
      allowMethods: apigateway.Cors.ALL_METHODS,
      allowHeaders: ['Content-Type', 'Authorization'],
    });

    // API Gateway integration for Exams
    const examsResource = api.root.addResource('exams');
    
    // GET /exams
    examsResource.addMethod('GET', new apigateway.LambdaIntegration(listExamsFunction), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    examsResource.addCorsPreflight({
      allowOrigins: apigateway.Cors.ALL_ORIGINS,
      allowMethods: apigateway.Cors.ALL_METHODS,
      allowHeaders: ['Content-Type', 'Authorization'],
    });

    // GET /exams/detail
    const examsDetailResource = examsResource.addResource('detail');
    examsDetailResource.addMethod('GET', new apigateway.LambdaIntegration(getExamDetailFunction), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    examsDetailResource.addCorsPreflight({
      allowOrigins: apigateway.Cors.ALL_ORIGINS,
      allowMethods: apigateway.Cors.ALL_METHODS,
      allowHeaders: ['Content-Type', 'Authorization'],
    });
    
    // Output the API URL
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'The URL of the Scoring API',
    });
  }
}

