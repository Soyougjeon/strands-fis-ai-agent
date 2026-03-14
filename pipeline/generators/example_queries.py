import json
import os

from pipeline.config import Config

EXAMPLE_QUERIES = {
    "etf": {
        "text2sql": [
            {"question": "AUM 상위 10개 ETF를 보여줘", "description": "순자산 기준 상위 ETF 목록"},
            {"question": "반도체 섹터 ETF의 최근 1년 수익률 비교", "description": "카테고리별 수익률 비교"},
            {"question": "총보수율이 0.1% 이하인 ETF 목록", "description": "저비용 ETF 필터링"},
            {"question": "해외주식 ETF 중 환헤지 상품은?", "description": "환헤지 여부 필터"},
            {"question": "2024년 이후 상장된 ETF는?", "description": "최근 상장 ETF 조회"},
        ],
        "rag": [
            {"question": "TIGER S&P500 ETF의 투자 전략은?", "description": "ETF 투자 전략 문서 검색"},
            {"question": "반도체 ETF의 위험 요소를 설명해줘", "description": "위험 요소 비정형 검색"},
            {"question": "환헤지 전략이 있는 ETF의 장단점은?", "description": "환헤지 특성 설명"},
            {"question": "배당형 ETF의 분배금 정책은 어떻게 되나요?", "description": "분배금 관련 문서 검색"},
        ],
        "graphrag": [
            {"question": "반도체 섹터 ETF들이 공통으로 보유한 종목은?", "description": "ETF 간 공통 보유종목 관계 탐색"},
            {"question": "삼성전자를 보유한 ETF들의 관계를 보여줘", "description": "종목 중심 ETF 연결 관계"},
            {"question": "해외주식 ETF와 관련된 위험 요소들의 연결 관계는?", "description": "위험 요소 네트워크 탐색"},
        ],
        "opencypher": [
            {"question": "TIGER S&P500에서 2홉 내 연결된 엔티티를 보여줘", "description": "ETF 중심 그래프 탐색"},
            {"question": "반도체 섹터에 속한 모든 ETF와 보유종목 그래프", "description": "섹터별 네트워크 시각화"},
            {"question": "미래에셋자산운용이 관리하는 ETF 네트워크", "description": "운용사 중심 관계 그래프"},
        ],
    },
    "bond": {
        "text2sql": [
            {"question": "AAA 등급 채권 목록과 수익률", "description": "신용등급별 채권 조회"},
            {"question": "만기 3년 이내 회사채 중 쿠폰 금리 상위 5개", "description": "만기/금리 기준 필터"},
            {"question": "발행금액 1000억 이상 국채 목록", "description": "발행 규모 필터"},
            {"question": "최근 90일간 가장 큰 수익률 변동을 보인 채권은?", "description": "변동성 분석"},
        ],
        "rag": [
            {"question": "한국전력 채권의 투자 위험은?", "description": "특정 발행사 채권 위험 분석"},
            {"question": "BBB 등급 회사채 투자 시 주의사항은?", "description": "하위 등급 투자 가이드"},
            {"question": "고정금리 vs 변동금리 채권의 차이점은?", "description": "금리 유형 비교 설명"},
        ],
        "graphrag": [
            {"question": "삼성전자가 발행한 채권들과 관련 신용등급의 관계는?", "description": "발행사-채권-등급 관계"},
            {"question": "AA등급 발행사들의 채권 네트워크를 보여줘", "description": "등급별 발행사 네트워크"},
        ],
        "opencypher": [
            {"question": "국채 발행자와 연결된 모든 채권의 그래프", "description": "국채 네트워크 시각화"},
            {"question": "신용등급 AA+ 이상인 발행사의 2홉 관계", "description": "고등급 발행사 그래프 탐색"},
        ],
    },
    "fund": {
        "text2sql": [
            {"question": "주식형 펀드 중 1년 수익률 상위 10개", "description": "유형별 성과 상위 펀드"},
            {"question": "총보수 1% 이하 채권형 펀드 목록", "description": "저비용 채권형 펀드 필터"},
            {"question": "순자산 1000억 이상 혼합형 펀드", "description": "대형 혼합형 펀드 조회"},
            {"question": "벤치마크 대비 초과수익을 낸 펀드는?", "description": "BM 대비 성과 분석"},
        ],
        "rag": [
            {"question": "미래에셋 성장주 펀드의 운용 전략은?", "description": "특정 펀드 전략 검색"},
            {"question": "채권형 펀드의 위험등급별 특성은?", "description": "위험등급 설명 검색"},
            {"question": "가치주 vs 성장주 펀드의 차이점은?", "description": "투자 스타일 비교"},
        ],
        "graphrag": [
            {"question": "삼성전자를 보유한 펀드들의 관계 네트워크", "description": "종목 중심 펀드 연결"},
            {"question": "KB자산운용의 펀드들이 공통으로 투자하는 종목은?", "description": "운용사별 공통 투자 종목"},
        ],
        "opencypher": [
            {"question": "주식형 펀드에서 가장 많이 보유된 종목 Top 5와 연결 관계", "description": "인기 종목 네트워크"},
            {"question": "미래에셋자산운용이 관리하는 펀드의 전체 네트워크", "description": "운용사 중심 그래프"},
        ],
    },
}


def generate_example_queries():
    out_dir = Config.DATA_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "example_queries.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(EXAMPLE_QUERIES, f, ensure_ascii=False, indent=2)
    total = sum(
        len(qs) for domain in EXAMPLE_QUERIES.values() for qs in domain.values()
    )
    print(f"Example queries generated: {total} questions -> {path}")
    return EXAMPLE_QUERIES
