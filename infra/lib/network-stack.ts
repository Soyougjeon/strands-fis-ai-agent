import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

interface NetworkStackProps extends cdk.StackProps {
  projectName: string;
}

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly ec2SecurityGroup: ec2.SecurityGroup;
  public readonly dbSecurityGroup: ec2.SecurityGroup;
  public readonly neptuneSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    // VPC with 2 AZs, public + private subnets
    this.vpc = new ec2.Vpc(this, "Vpc", {
      vpcName: `${props.projectName}-vpc`,
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });

    // EC2 Security Group (public, HTTP + SSH)
    this.ec2SecurityGroup = new ec2.SecurityGroup(this, "Ec2Sg", {
      vpc: this.vpc,
      securityGroupName: `${props.projectName}-ec2-sg`,
      description: "EC2 instance for Strands FIS",
      allowAllOutbound: true,
    });
    this.ec2SecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      "HTTP"
    );
    this.ec2SecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(22),
      "SSH"
    );

    // Aurora Security Group (private, from EC2 only)
    this.dbSecurityGroup = new ec2.SecurityGroup(this, "DbSg", {
      vpc: this.vpc,
      securityGroupName: `${props.projectName}-aurora-sg`,
      description: "Aurora PostgreSQL",
    });
    this.dbSecurityGroup.addIngressRule(
      this.ec2SecurityGroup,
      ec2.Port.tcp(5432),
      "PostgreSQL from EC2"
    );

    // Neptune Security Group (private, from EC2 only)
    this.neptuneSecurityGroup = new ec2.SecurityGroup(this, "NeptuneSg", {
      vpc: this.vpc,
      securityGroupName: `${props.projectName}-neptune-sg`,
      description: "Neptune DB",
    });
    this.neptuneSecurityGroup.addIngressRule(
      this.ec2SecurityGroup,
      ec2.Port.tcp(8182),
      "Neptune from EC2"
    );

    // Outputs
    new cdk.CfnOutput(this, "VpcId", { value: this.vpc.vpcId });
  }
}
