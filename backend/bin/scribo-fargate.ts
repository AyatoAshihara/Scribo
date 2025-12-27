#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ScriboEcrStack } from '../lib/scribo-ecr-stack';
import { ScriboFargateStack } from '../lib/scribo-fargate-stack';
import { ScriboGitHubOidcStack } from '../lib/scribo-github-oidc-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1',
};

// Step 0: GitHub OIDC認証用IAMロール
new ScriboGitHubOidcStack(app, 'ScriboGitHubOidcStack', {
  env,
  description: 'GitHub Actions OIDC IAM Role for Scribo',
});

// Step 1: ECRリポジトリを作成（先にデプロイ）
const ecrStack = new ScriboEcrStack(app, 'ScriboEcrStack', {
  env,
  description: 'Scribo ECR Repository',
});

// Step 2: Fargateスタック（イメージプッシュ後にデプロイ）
const fargateStack = new ScriboFargateStack(app, 'ScriboFargateStack', {
  env,
  description: 'Scribo FastAPI + htmx application on ECS Fargate',
  repository: ecrStack.repository,
});

// 依存関係を設定
fargateStack.addDependency(ecrStack);
