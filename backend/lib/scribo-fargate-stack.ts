import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';

export interface ScriboFargateStackProps extends cdk.StackProps {
  repository: ecr.IRepository;
}

/**
 * Scribo FastAPI + htmx アプリケーション
 * ECS Fargate (Spot) + ALB 構成
 */
export class ScriboFargateStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ScriboFargateStackProps) {
    super(scope, id, props);

    const { repository } = props;

    // ==========================================================================
    // 1. 既存リソースの参照
    // ==========================================================================
    
    // 既存DynamoDBテーブルをインポート
    const examTable = dynamodb.Table.fromTableName(this, 'ExamTable', 'scribo-ipa');
    const submissionTable = dynamodb.Table.fromTableName(this, 'SubmissionTable', 'BackendStack-SubmissionTable33F44FF8-18BO8KQ7XEI4V');
    
    // 新規テーブル作成: 準備モジュール管理
    const modulesTable = new dynamodb.Table(this, 'ModulesTable', {
      tableName: 'ModulesTable',
      partitionKey: { name: 'user_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'module_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // 開発環境用。本番ではRETAIN推奨
    });

    // 既存テーブルをインポート: 論文設計図管理
    const designsTable = dynamodb.Table.fromTableName(this, 'DesignsTable', 'DesignsTable');

    // 新規テーブル作成: AIインタビューセッション管理
    const interviewSessionsTable = new dynamodb.Table(this, 'InterviewSessionsTable', {
      tableName: 'InterviewSessionsTable',
      partitionKey: { name: 'user_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'exam_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    
    // 既存S3バケットをインポート（問題データ格納）
    const essayBucket = s3.Bucket.fromBucketName(this, 'EssayBucket', 'scribo-essay-evaluator');

    // ==========================================================================
    // 2. VPC
    // ==========================================================================
    
    const vpc = new ec2.Vpc(this, 'ScriboVpc', {
      maxAzs: 2,
      natGateways: 1, // コスト削減のため1つに制限
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // ==========================================================================
    // 3. ECS クラスター
    // ==========================================================================
    
    const cluster = new ecs.Cluster(this, 'ScriboCluster', {
      vpc,
      clusterName: 'scribo-cluster',
      containerInsights: true, // CloudWatch Container Insights有効化
    });

    // ==========================================================================
    // 5. タスク定義
    // ==========================================================================
    
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'ScriboTaskDef', {
      memoryLimitMiB: 1024,
      cpu: 512,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    // DynamoDB アクセス権限
    examTable.grantReadData(taskDefinition.taskRole);
    submissionTable.grantReadWriteData(taskDefinition.taskRole);
    modulesTable.grantReadWriteData(taskDefinition.taskRole);
    designsTable.grantReadWriteData(taskDefinition.taskRole);
    interviewSessionsTable.grantReadWriteData(taskDefinition.taskRole);

    // S3 アクセス権限（問題データ読み取り）
    essayBucket.grantRead(taskDefinition.taskRole);

    // Bedrock アクセス権限
    taskDefinition.taskRole.addToPrincipalPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: ['*'],
    }));

    // CloudWatch Logs
    const logGroup = new logs.LogGroup(this, 'ScriboLogGroup', {
      logGroupName: '/ecs/scribo-app',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // コンテナ定義
    const container = taskDefinition.addContainer('ScriboContainer', {
      image: ecs.ContainerImage.fromEcrRepository(repository, 'latest'),
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: 'scribo',
      }),
      environment: {
        AWS_REGION: this.region,
        DYNAMODB_EXAM_TABLE: 'scribo-ipa',
        DYNAMODB_SUBMISSION_TABLE: 'SubmissionTable',
        DYNAMODB_INTERVIEW_SESSION_TABLE: 'InterviewSessionsTable',
        BEDROCK_MODEL_ID: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
      },
      healthCheck: {
        command: ['CMD-SHELL', 'curl -f http://localhost:8000/health || exit 1'],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    container.addPortMappings({
      containerPort: 8000,
      protocol: ecs.Protocol.TCP,
    });

    // ==========================================================================
    // 6. ALB (Application Load Balancer)
    // ==========================================================================
    
    const alb = new elbv2.ApplicationLoadBalancer(this, 'ScriboAlb', {
      vpc,
      internetFacing: true,
      loadBalancerName: 'scribo-alb',
    });

    // ALBアイドルタイムアウトを120秒に延長（Bedrock採点用）
    alb.setAttribute('idle_timeout.timeout_seconds', '120');

    const listener = alb.addListener('HttpListener', {
      port: 80,
      open: true,
    });

    // ==========================================================================
    // 7. Fargate サービス (Spot)
    // ==========================================================================
    
    const service = new ecs.FargateService(this, 'ScriboService', {
      cluster,
      taskDefinition,
      desiredCount: 1,
      serviceName: 'scribo-service',
      assignPublicIp: false,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      // Fargate Spot を使用（コスト最大70%削減）
      capacityProviderStrategies: [
        {
          capacityProvider: 'FARGATE_SPOT',
          weight: 2,
        },
        {
          capacityProvider: 'FARGATE',
          weight: 1,
        },
      ],
      circuitBreaker: {
        rollback: true,
      },
    });

    // ターゲットグループ
    const targetGroup = listener.addTargets('ScriboTargets', {
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [service],
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
      },
      deregistrationDelay: cdk.Duration.seconds(30),
    });

    // ==========================================================================
    // 8. セキュリティグループ設定
    // ==========================================================================
    
    // ALBからのみECSへのアクセスを許可
    service.connections.allowFrom(
      alb,
      ec2.Port.tcp(8000),
      'Allow from ALB'
    );

    // ==========================================================================
    // 9. 出力
    // ==========================================================================
    
    new cdk.CfnOutput(this, 'AlbDnsName', {
      value: alb.loadBalancerDnsName,
      description: 'ALB DNS Name (HTTP)',
      exportName: 'ScriboAlbDnsName',
    });

    new cdk.CfnOutput(this, 'ClusterName', {
      value: cluster.clusterName,
      description: 'ECS Cluster Name',
      exportName: 'ScriboClusterName',
    });

    new cdk.CfnOutput(this, 'ServiceName', {
      value: service.serviceName,
      description: 'ECS Service Name',
      exportName: 'ScriboServiceName',
    });
  }
}
