import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as rds from "aws-cdk-lib/aws-rds";
import * as neptune from "aws-cdk-lib/aws-neptune";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as opensearch from "aws-cdk-lib/aws-opensearchserverless";
import { Construct } from "constructs";

interface DataStackProps extends cdk.StackProps {
  projectName: string;
  vpc: ec2.IVpc;
  dbSecurityGroup: ec2.SecurityGroup;
  neptuneSecurityGroup: ec2.SecurityGroup;
}

export class DataStack extends cdk.Stack {
  public readonly auroraEndpoint: string;
  public readonly auroraPort: string;
  public readonly auroraDbName: string;
  public readonly neptuneEndpoint: string;
  public readonly neptunePort: string;
  public readonly opensearchEndpoint: string;
  public readonly dynamoTableName: string;

  constructor(scope: Construct, id: string, props: DataStackProps) {
    super(scope, id, props);

    // ===== Aurora PostgreSQL =====
    const dbName = "fis";
    const auroraCluster = new rds.DatabaseCluster(this, "Aurora", {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_8,
      }),
      writer: rds.ClusterInstance.serverlessV2("Writer", {
        scaleWithWriter: true,
      }),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.dbSecurityGroup],
      defaultDatabaseName: dbName,
      credentials: rds.Credentials.fromGeneratedSecret("postgres", {
        secretName: `${props.projectName}/aurora-credentials`,
      }),
      serverlessV2MinCapacity: 0.5,
      serverlessV2MaxCapacity: 4,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.auroraEndpoint = auroraCluster.clusterEndpoint.hostname;
    this.auroraPort = auroraCluster.clusterEndpoint.port.toString();
    this.auroraDbName = dbName;

    // ===== Neptune =====
    const neptuneSubnetGroup = new neptune.CfnDBSubnetGroup(
      this,
      "NeptuneSubnetGroup",
      {
        dbSubnetGroupDescription: "Neptune subnet group",
        dbSubnetGroupName: `${props.projectName}-neptune-subnets`,
        subnetIds: props.vpc.selectSubnets({
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        }).subnetIds,
      }
    );

    const neptuneCluster = new neptune.CfnDBCluster(this, "Neptune", {
      dbClusterIdentifier: `${props.projectName}-neptune`,
      engineVersion: "1.3.2.1",
      dbSubnetGroupName: neptuneSubnetGroup.dbSubnetGroupName,
      vpcSecurityGroupIds: [props.neptuneSecurityGroup.securityGroupId],
      iamAuthEnabled: true,
      deletionProtection: false,
      serverlessScalingConfiguration: {
        minCapacity: 1,
        maxCapacity: 8,
      },
    });
    neptuneCluster.addDependency(neptuneSubnetGroup);

    this.neptuneEndpoint = neptuneCluster.attrEndpoint;
    this.neptunePort = neptuneCluster.attrPort;

    // ===== OpenSearch Serverless =====
    // Encryption policy (required for collections)
    const encPolicy = new opensearch.CfnSecurityPolicy(
      this,
      "OsEncPolicy",
      {
        name: `${props.projectName}-enc`,
        type: "encryption",
        policy: JSON.stringify({
          Rules: [
            {
              ResourceType: "collection",
              Resource: [`collection/${props.projectName}-*`],
            },
          ],
          AWSOwnedKey: true,
        }),
      }
    );

    // Network policy (public access for PoC)
    const netPolicy = new opensearch.CfnSecurityPolicy(
      this,
      "OsNetPolicy",
      {
        name: `${props.projectName}-net`,
        type: "network",
        policy: JSON.stringify([
          {
            Rules: [
              {
                ResourceType: "collection",
                Resource: [`collection/${props.projectName}-*`],
              },
              {
                ResourceType: "dashboard",
                Resource: [`collection/${props.projectName}-*`],
              },
            ],
            AllowFromPublic: true,
          },
        ]),
      }
    );

    // Collection for RAG + GraphRAG indices
    const osCollection = new opensearch.CfnCollection(this, "OsCollection", {
      name: `${props.projectName}-vectors`,
      type: "VECTORSEARCH",
      description: "RAG and GraphRAG vector indices",
    });
    osCollection.addDependency(encPolicy);
    osCollection.addDependency(netPolicy);

    this.opensearchEndpoint = osCollection.attrCollectionEndpoint;

    // ===== DynamoDB =====
    const table = new dynamodb.Table(this, "ConversationTurns", {
      tableName: "conversation_turns",
      partitionKey: { name: "session_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "turn_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.dynamoTableName = table.tableName;

    // ===== Outputs =====
    new cdk.CfnOutput(this, "AuroraEndpoint", {
      value: this.auroraEndpoint,
    });
    new cdk.CfnOutput(this, "AuroraSecretArn", {
      value: auroraCluster.secret!.secretArn,
    });
    new cdk.CfnOutput(this, "NeptuneEndpoint", {
      value: this.neptuneEndpoint,
    });
    new cdk.CfnOutput(this, "OpenSearchEndpoint", {
      value: this.opensearchEndpoint,
    });
    new cdk.CfnOutput(this, "DynamoTableName", {
      value: this.dynamoTableName,
    });
  }
}
