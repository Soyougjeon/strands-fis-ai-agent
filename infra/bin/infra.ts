#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { NetworkStack } from "../lib/network-stack";
import { DataStack } from "../lib/data-stack";
import { ComputeStack } from "../lib/compute-stack";

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || "us-east-1",
};

const projectName = "strands-fis";

// Stack 1: VPC + Security Groups
const network = new NetworkStack(app, `${projectName}-network`, {
  env,
  projectName,
});

// Stack 2: Aurora PG + Neptune + OpenSearch + DynamoDB
const data = new DataStack(app, `${projectName}-data`, {
  env,
  projectName,
  vpc: network.vpc,
  dbSecurityGroup: network.dbSecurityGroup,
  neptuneSecurityGroup: network.neptuneSecurityGroup,
});

// Stack 3: EC2 (Docker Compose) + IAM
new ComputeStack(app, `${projectName}-compute`, {
  env,
  projectName,
  vpc: network.vpc,
  ec2SecurityGroup: network.ec2SecurityGroup,
  auroraEndpoint: data.auroraEndpoint,
  auroraPort: data.auroraPort,
  auroraDbName: data.auroraDbName,
  neptuneEndpoint: data.neptuneEndpoint,
  neptunePort: data.neptunePort,
  opensearchEndpoint: data.opensearchEndpoint,
  dynamoTableName: data.dynamoTableName,
});
