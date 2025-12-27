import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecr from 'aws-cdk-lib/aws-ecr';

/**
 * Scribo ECR リポジトリスタック（先にデプロイ）
 */
export class ScriboEcrStack extends cdk.Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.repository = new ecr.Repository(this, 'ScriboRepository', {
      repositoryName: 'scribo-app',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
      lifecycleRules: [
        {
          maxImageCount: 5,
          description: '最新5イメージのみ保持',
        },
      ],
    });

    new cdk.CfnOutput(this, 'EcrRepositoryUri', {
      value: this.repository.repositoryUri,
      description: 'ECR Repository URI',
      exportName: 'ScriboEcrUri',
    });

    new cdk.CfnOutput(this, 'EcrRepositoryName', {
      value: this.repository.repositoryName,
      description: 'ECR Repository Name',
      exportName: 'ScriboEcrName',
    });
  }
}
