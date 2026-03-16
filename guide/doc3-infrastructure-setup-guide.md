# Doc 3: Infrastructure Setup Guide

## 1. AWS 서비스 구성 요약

| 서비스 | 리소스 | 스펙 |
|--------|--------|------|
| VPC | 1개 | 2 AZ, Public+Private Subnet, NAT GW 1개 |
| EC2 | t3.medium | Public Subnet, EIP, 30GB gp3 |
| Aurora PostgreSQL | Serverless v2 | 0.5~4 ACU, Private Subnet |
| Neptune DB | Serverless | 1~8 NCU, Private Subnet |
| OpenSearch Serverless | VECTORSEARCH | Public access (PoC) |
| DynamoDB | On-Demand | conversation_turns 테이블 |
| Bedrock | Claude Sonnet + Titan Embed v2 | IAM 접근 |
| Secrets Manager | 1개 시크릿 | Aurora PG 자격증명 |

## 2. CDK 스택 구조

3개 스택을 순서대로 배포한다:

```
NetworkStack → DataStack → ComputeStack
```

### Stack 1: NetworkStack (`infra/lib/network-stack.ts`)

생성 리소스:
- VPC (2 AZ, Public + Private Subnet, NAT GW)
- EC2 Security Group: Inbound 80(HTTP), 22(SSH)
- Aurora Security Group: Inbound 5432 from EC2 SG
- Neptune Security Group: Inbound 8182 from EC2 SG

### Stack 2: DataStack (`infra/lib/data-stack.ts`)

생성 리소스:
- Aurora PostgreSQL Serverless v2 (DB명: `fis`, 자격증명 자동 생성 → Secrets Manager)
- Neptune DB Serverless (OpenCypher, IAM Auth)
- OpenSearch Serverless Collection (VECTORSEARCH 타입)
  - Encryption Policy + Network Policy 자동 생성
- DynamoDB Table (`conversation_turns`, PK: session_id, SK: turn_id)

### Stack 3: ComputeStack (`infra/lib/compute-stack.ts`)

생성 리소스:
- EC2 Instance (t3.medium, Amazon Linux 2023)
- IAM Role (Bedrock, DynamoDB, Neptune, AOSS, Secrets Manager 권한)
- Elastic IP
- UserData (Docker 설치, git clone, .env 생성, docker-compose up)

## 3. 보안그룹 규칙

| Source | Destination | Port | 용도 |
|--------|-------------|------|------|
| 0.0.0.0/0 | EC2 SG | 80 | HTTP (Nginx) |
| 0.0.0.0/0 | EC2 SG | 22 | SSH |
| EC2 SG | Aurora SG | 5432 | PostgreSQL |
| EC2 SG | Neptune SG | 8182 | Neptune |
| EC2 SG | AOSS | 443 | OpenSearch (IAM) |

## 4. IAM 권한

EC2 인스턴스 역할에 필요한 권한:

```json
{
  "bedrock:InvokeModel": "*",
  "bedrock:InvokeModelWithResponseStream": "*",
  "dynamodb:PutItem/GetItem/Query/Scan/DeleteItem/BatchWriteItem": "arn:...:table/conversation_turns",
  "neptune-db:connect": "*",
  "neptune-db:ReadDataViaQuery": "*",
  "aoss:APIAccessAll": "*",
  "secretsmanager:GetSecretValue": "arn:...:secret:{project}/aurora-credentials*"
}
```

추가로 `AmazonSSMManagedInstanceCore` 관리형 정책 (Session Manager 접근용).

## 5. 환경변수 (.env)

| 키 | 설명 | 예시 |
|----|------|------|
| DB_HOST | Aurora Writer Endpoint | `xxx.cluster-xxx.us-east-1.rds.amazonaws.com` |
| DB_PORT | Aurora 포트 | `5432` |
| DB_NAME | 데이터베이스명 | `fis` |
| DB_USER | DB 사용자 | `postgres` |
| DB_PASSWORD | DB 비밀번호 | Secrets Manager에서 조회 |
| NEPTUNE_ENDPOINT | Neptune Writer Endpoint | `xxx.cluster-xxx.us-east-1.neptune.amazonaws.com` |
| NEPTUNE_PORT | Neptune 포트 | `8182` |
| OPENSEARCH_ENDPOINT | AOSS Collection Endpoint | `https://xxx.us-east-1.aoss.amazonaws.com` |
| AWS_REGION | AWS 리전 | `us-east-1` |
| LLM_MODEL_ID | Bedrock LLM 모델 | `us.anthropic.claude-sonnet-4-6-v1:0` |
| EMBEDDING_MODEL_ID | Bedrock 임베딩 모델 | `amazon.titan-embed-text-v2:0` |
| DYNAMODB_TABLE | DynamoDB 테이블명 | `conversation_turns` |
| EXAMPLE_QUERIES_PATH | 예시 쿼리 JSON 경로 | `./pipeline/data/mock/example_queries.json` |

## 6. 배포 순서

```bash
# 1. CDK 배포
cd infra
npm install
cdk deploy strands-fis-network
cdk deploy strands-fis-data
cdk deploy strands-fis-compute

# 2. 출력값 확인
# - AuroraEndpoint, NeptuneEndpoint, OpenSearchEndpoint
# - PublicIp, SshCommand

# 3. EC2 접속 후 확인
ssh -i strands-fis-key.pem ec2-user@<PublicIp>
docker-compose ps
curl http://localhost:8000/api/health
```

## 7. 커스터마이징 시 변경 포인트

| 항목 | 파일 | 변경 내용 |
|------|------|----------|
| 프로젝트명 | `infra/bin/infra.ts` | `projectName` 변수 |
| 리전 | `infra/bin/infra.ts` | `region` 변수 |
| EC2 스펙 | `infra/lib/compute-stack.ts` | `instanceType` |
| Aurora 스펙 | `infra/lib/data-stack.ts` | `serverlessV2MinCapacity/MaxCapacity` |
| Neptune 스펙 | `infra/lib/data-stack.ts` | `minCapacity/maxCapacity` |
| Key Pair | `infra/lib/compute-stack.ts` | `keyPairName` (사전 생성 필요) |
| Basic Auth 계정 | `infra/lib/compute-stack.ts` | UserData 내 `htpasswd` 명령 |
| Git 저장소 | `infra/lib/compute-stack.ts` | UserData 내 `git clone` URL |
