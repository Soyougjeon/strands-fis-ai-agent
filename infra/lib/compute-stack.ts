import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";

interface ComputeStackProps extends cdk.StackProps {
  projectName: string;
  vpc: ec2.IVpc;
  ec2SecurityGroup: ec2.SecurityGroup;
  auroraEndpoint: string;
  auroraPort: string;
  auroraDbName: string;
  neptuneEndpoint: string;
  neptunePort: string;
  opensearchEndpoint: string;
  dynamoTableName: string;
}

export class ComputeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    // IAM Role for EC2
    const role = new iam.Role(this, "Ec2Role", {
      roleName: `${props.projectName}-ec2-role`,
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore"),
      ],
    });

    // Bedrock access
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // DynamoDB access
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DeleteItem",
          "dynamodb:BatchWriteItem",
        ],
        resources: [
          `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.dynamoTableName}`,
        ],
      })
    );

    // Neptune access
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ["neptune-db:connect", "neptune-db:ReadDataViaQuery"],
        resources: ["*"],
      })
    );

    // OpenSearch Serverless access
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ["aoss:APIAccessAll"],
        resources: ["*"],
      })
    );

    // Secrets Manager (Aurora credentials)
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ["secretsmanager:GetSecretValue"],
        resources: [
          `arn:aws:secretsmanager:${this.region}:${this.account}:secret:${props.projectName}/aurora-credentials*`,
        ],
      })
    );

    // Key Pair - use existing or create manually
    const keyPairName = `${props.projectName}-key`;

    // EC2 Instance
    const instance = new ec2.Instance(this, "AppServer", {
      instanceName: `${props.projectName}-server`,
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MEDIUM
      ),
      machineImage: ec2.MachineImage.latestAmazonLinux2023(),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroup: props.ec2SecurityGroup,
      role,
      keyPair: ec2.KeyPair.fromKeyPairName(this, "KeyPair", keyPairName),
      blockDevices: [
        {
          deviceName: "/dev/xvda",
          volume: ec2.BlockDeviceVolume.ebs(30, {
            volumeType: ec2.EbsDeviceVolumeType.GP3,
          }),
        },
      ],
    });

    // UserData - install Docker, clone repo, configure, start
    instance.addUserData(`#!/bin/bash
set -euxo pipefail

# Install Docker
yum update -y
yum install -y docker git
systemctl enable --now docker
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install htpasswd
yum install -y httpd-tools

# Clone repository
cd /opt
git clone https://github.com/Soyougjeon/strands-fis.git || true
cd strands-fis

# Retrieve Aurora secret
SECRET_ARN=$(aws secretsmanager list-secrets --region ${this.region} \
  --filter Key=name,Values=${props.projectName}/aurora-credentials \
  --query 'SecretList[0].ARN' --output text)

DB_SECRET=$(aws secretsmanager get-secret-value --secret-id $SECRET_ARN \
  --region ${this.region} --query SecretString --output text)

DB_USER=$(echo $DB_SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])")
DB_PASS=$(echo $DB_SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")

# Create .env
cat > .env << ENVEOF
DB_HOST=${props.auroraEndpoint}
DB_PORT=${props.auroraPort}
DB_NAME=${props.auroraDbName}
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
NEPTUNE_ENDPOINT=${props.neptuneEndpoint}
NEPTUNE_PORT=${props.neptunePort}
OPENSEARCH_ENDPOINT=${props.opensearchEndpoint}
AWS_REGION=${this.region}
LLM_MODEL_ID=us.anthropic.claude-sonnet-4-6-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
DYNAMODB_TABLE=${props.dynamoTableName}
EXAMPLE_QUERIES_PATH=./pipeline/data/mock/example_queries.json
ENVEOF

# Create Basic Auth users
htpasswd -cb nginx/.htpasswd tester1 StrandsFIS2025!
htpasswd -b nginx/.htpasswd tester2 StrandsFIS2025!
htpasswd -b nginx/.htpasswd tester3 StrandsFIS2025!
htpasswd -b nginx/.htpasswd tester4 StrandsFIS2025!
htpasswd -b nginx/.htpasswd tester5 StrandsFIS2025!

# Run Pipeline first (generate local files, skip AWS indexing for now)
docker build -t strands-backend .
docker run --rm --env-file .env -v $(pwd)/pipeline/data:/app/pipeline/data \
  strands-backend python -m pipeline.main generate-csv
docker run --rm --env-file .env -v $(pwd)/pipeline/data:/app/pipeline/data \
  strands-backend python -m pipeline.main generate-md
docker run --rm --env-file .env -v $(pwd)/pipeline/data:/app/pipeline/data \
  strands-backend python -m pipeline.main generate-queries

# Start services
docker-compose up -d --build

echo "Strands FIS deployment complete!"
`);

    // Elastic IP for stable address
    const eip = new ec2.CfnEIP(this, "Eip", {
      instanceId: instance.instanceId,
    });

    // Outputs
    new cdk.CfnOutput(this, "InstanceId", {
      value: instance.instanceId,
    });
    new cdk.CfnOutput(this, "PublicIp", {
      value: eip.attrPublicIp,
    });
    new cdk.CfnOutput(this, "AppUrl", {
      value: `http://${eip.attrPublicIp}`,
    });
    new cdk.CfnOutput(this, "SshCommand", {
      value: `ssh -i ${keyPairName}.pem ec2-user@${eip.attrPublicIp}`,
    });
  }
}
