# Technology Stack

## Programming Languages
| Language | Version | Usage |
|----------|---------|-------|
| Python | 3.11+ | 전체 애플리케이션 (스크래핑, GraphRAG, CLI) |

## Frameworks
| Framework | Version | Purpose |
|-----------|---------|---------|
| SQLAlchemy | 2.0+ | ORM, 데이터베이스 추상화, 세션 관리 |
| Pydantic Settings | 2.0+ | 다중 소스 설정 관리 (env > .env > yaml) |
| Click | 8.1+ | CLI 프레임워크 (명령 그룹, 옵션) |
| LlamaIndex | latest | 문서 로딩, 청크 분할, LLM 파이프라인 |
| graphrag-toolkit | 3.16.1 | AWS GraphRAG (LexicalGraph, 인덱싱, 질의) |
| Alembic | 1.13+ | 데이터베이스 마이그레이션 |

## Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| httpx | 0.27+ | HTTP 클라이언트 (웹 스크래핑) |
| beautifulsoup4 | 4.12+ | HTML DOM 파싱 |
| lxml | latest | HTML 파서 백엔드 |
| xlrd | 2.0+ | XLS 엑셀 파싱 (보유종목) |
| PyMuPDF (fitz) | 1.24+ | PDF 텍스트 추출 |
| tenacity | 8.2+ | 재시도 로직 (exponential backoff) |
| Rich | 13.0+ | 콘솔 출력 포매팅 |
| PyYAML | 6.0+ | YAML 설정 파일 파싱 |
| boto3 | 1.34+ | AWS SDK (Bedrock, Neptune, OpenSearch, Secrets Manager) |

## Infrastructure (AWS)
| Service | Purpose |
|---------|---------|
| Aurora PostgreSQL | ETF 구조화 데이터 저장 (Writer/Reader 분리) |
| Neptune Database | Knowledge Graph 저장 (OpenCypher) |
| OpenSearch Serverless (AOSS) | 벡터 임베딩 저장 및 유사도 검색 |
| Amazon Bedrock | LLM (Claude Sonnet) + Embeddings (Titan v2) |
| AWS Secrets Manager | 데이터베이스 자격 증명 관리 |
| AWS IAM | Neptune/OpenSearch 인증 |

## AI/ML Models
| Model | Provider | Purpose |
|-------|----------|---------|
| Claude 3.7 Sonnet | Anthropic (Bedrock) | Entity/Relationship 추출 + 응답 생성 |
| Claude 4.5 Sonnet | Anthropic (Bedrock) | 실험용 대안 LLM |
| Claude 4 | Anthropic (Bedrock) | 실험용 대안 LLM |
| Haiku 4.5 | Anthropic (Bedrock) | 경량 실험용 LLM |
| Titan Embed Text v2 | AWS (Bedrock) | 1024차원 텍스트 임베딩 |
| Cohere Embed | Cohere (Bedrock) | 실험용 대안 임베딩 |

## Build Tools
| Tool | Version | Purpose |
|------|---------|---------|
| pip/setuptools | latest | Python 패키지 빌드 |
| Docker Compose | latest | 로컬 개발 환경 (PostgreSQL) |

## Testing Tools
| Tool | Version | Purpose |
|------|---------|---------|
| pytest | latest | 단위 테스트 실행 |
| Custom Evaluator | - | GraphRAG 품질 평가 (keyword hit + LLM-as-Judge) |
