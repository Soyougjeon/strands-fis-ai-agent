# Functional Design Plan - Unit 1: Mock Data Pipeline

## Plan Steps

- [x] Step 1: ETF Mock 데이터 도메인 모델 정의 (기존 스키마 참조)
- [x] Step 2: 채권(Bond) 도메인 모델 상세 설계 (신규)
- [x] Step 3: 펀드(Fund) 도메인 모델 상세 설계 (신규)
- [x] Step 4: Mock CSV 생성 비즈니스 로직 (데이터 생성 규칙)
- [x] Step 5: Mock MD 파일 생성 비즈니스 로직 (GraphRAG/RAG용)
- [x] Step 6: 예시 질문 생성 로직 (3 도메인 x 4 쿼리방식)
- [x] Step 7: DB 적재 로직 (CSV -> Aurora PG)
- [x] Step 8: GraphRAG 인덱싱 로직 (MD -> Neptune 멀티테넌시)
- [x] Step 9: RAG 인덱싱 로직 (MD -> OpenSearch 벡터)
- [x] Step 10: 파이프라인 실행 순서 및 오류 처리

## Clarifying Questions

### Q1: 채권(Bond) Mock 데이터 상세
[Answer]: A - 국내 국채/회사채 중심 (한국어, KRW)

### Q2: 펀드(Fund) Mock 데이터 상세
[Answer]: A - 주식형/혼합형/채권형 등 일반 공모펀드

### Q3: Mock 데이터 건수
[Answer]: A - 소규모: ETF 30개, 채권 30개, 펀드 30개

### Q4: MD 파일 내용 및 길이
[Answer]: B - 상품별 1개 MD + 도메인 개요 MD (풍부한 컨텍스트)

### Q5: 기존 ETF 스키마 활용 방식
[Answer]: C - ETF 기존 유지 (tiger_etf), 채권/펀드 별도 스키마 (bond, fund)

### 추가 요구사항
- 각 도메인(ETF/Bond/Fund) x 4가지 쿼리 방식(Text2SQL/RAG/GraphRAG/OpenCypher)별 예시 질문 생성
- UI 사이드바 예시 쿼리 및 테스트용으로 활용
