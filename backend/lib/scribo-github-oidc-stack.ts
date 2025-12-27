import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';

/**
 * GitHub Actions OIDC 認証用 IAM ロール
 */
export class ScriboGitHubOidcStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // GitHub OIDC プロバイダー（既存の場合はインポート）
    const githubOidcProvider = new iam.OpenIdConnectProvider(this, 'GitHubOidcProvider', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com'],
      thumbprints: ['6938fd4d98bab03faadb97b34396831e3780aea1'],
    });

    // GitHub Actions 用 IAM ロール
    const deployRole = new iam.Role(this, 'ScriboGitHubActionsRole', {
      roleName: 'scribo-github-actions-role',
      assumedBy: new iam.FederatedPrincipal(
        githubOidcProvider.openIdConnectProviderArn,
        {
          StringEquals: {
            'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
          },
          StringLike: {
            // あなたのGitHubリポジトリに変更してください
            'token.actions.githubusercontent.com:sub': 'repo:aashi-ihsaa/Scribo:*',
          },
        },
        'sts:AssumeRoleWithWebIdentity'
      ),
      description: 'Role for GitHub Actions to deploy Scribo application',
      maxSessionDuration: cdk.Duration.hours(1),
    });

    // ECR 権限
    deployRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ecr:GetAuthorizationToken',
      ],
      resources: ['*'],
    }));

    deployRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ecr:BatchCheckLayerAvailability',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
        'ecr:PutImage',
        'ecr:InitiateLayerUpload',
        'ecr:UploadLayerPart',
        'ecr:CompleteLayerUpload',
      ],
      resources: ['arn:aws:ecr:ap-northeast-1:*:repository/scribo-app'],
    }));

    // ECS 権限
    deployRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ecs:DescribeServices',
        'ecs:DescribeTaskDefinition',
        'ecs:DescribeTasks',
        'ecs:ListTasks',
        'ecs:RegisterTaskDefinition',
        'ecs:UpdateService',
      ],
      resources: ['*'],
    }));

    // IAM PassRole 権限（タスク定義更新時に必要）
    deployRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['iam:PassRole'],
      resources: ['*'],
      conditions: {
        StringEquals: {
          'iam:PassedToService': 'ecs-tasks.amazonaws.com',
        },
      },
    }));

    // CloudFormation 権限（CDKデプロイ用）
    deployRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cloudformation:DescribeStacks',
        'cloudformation:CreateStack',
        'cloudformation:UpdateStack',
        'cloudformation:DeleteStack',
        'cloudformation:CreateChangeSet',
        'cloudformation:ExecuteChangeSet',
        'cloudformation:DescribeChangeSet',
        'cloudformation:GetTemplate',
      ],
      resources: ['arn:aws:cloudformation:ap-northeast-1:*:stack/Scribo*/*'],
    }));

    new cdk.CfnOutput(this, 'GitHubActionsRoleArn', {
      value: deployRole.roleArn,
      description: 'IAM Role ARN for GitHub Actions',
      exportName: 'ScriboGitHubActionsRoleArn',
    });
  }
}
