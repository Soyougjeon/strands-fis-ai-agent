"""Text2SQL Tool - Few-shot prompted SQL generation + Aurora PG execution."""

import json
import re
import time

import boto3
from sqlalchemy import create_engine, text

from backend.agent.prompts import FEW_SHOT_MAP, SCHEMA_MAP, TEXT2SQL_PROMPT_TEMPLATE
from backend.config import Config
from backend.services.token_tracker import calculate_cost
from backend.services.visualization import detect_chart_data


FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


class Text2SQLTool:
    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        self.model_id = Config.LLM_MODEL_ID
        self.engine = create_engine(Config.DB_URL, pool_pre_ping=True)

    async def execute(self, message: str, intent: str) -> dict:
        """Generate SQL from natural language and execute against Aurora PG."""
        result = {"query_step": None, "execution": {}}

        # Step 1: Generate SQL via LLM
        schema = SCHEMA_MAP.get(intent, "")
        few_shot = FEW_SHOT_MAP.get(intent, "")
        prompt = TEXT2SQL_PROMPT_TEMPLATE.format(
            schema=schema, few_shot=few_shot, question=message,
        )

        start = time.time()
        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        latency = time.time() - start

        output = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        tokens_in = usage.get("inputTokens", 0)
        tokens_out = usage.get("outputTokens", 0)
        cost = calculate_cost("claude-sonnet", tokens_in, tokens_out)

        # Extract SQL from response (may be wrapped in ```sql blocks)
        sql = self._extract_sql(output)

        result["query_step"] = {
            "query_type": "sql",
            "query": sql,
            "latency": round(latency, 3),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": round(cost, 6),
        }

        # Step 2: Validate SQL
        if not self._validate_sql(sql):
            result["execution"] = {
                "result_summary": "SQL 안전성 검증 실패: 읽기 전용 쿼리만 허용됩니다.",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": 0,
            }
            return result

        # Ensure LIMIT exists
        sql = self._ensure_limit(sql)

        # Step 3: Execute SQL
        start = time.time()
        try:
            rows, columns = self._execute_sql(sql)
            exec_latency = time.time() - start

            raw_data = [dict(zip(columns, row)) for row in rows]
            summary = f"{len(raw_data)}건 조회 완료. 컬럼: {', '.join(columns)}"

            chart_data = detect_chart_data(raw_data, columns)

            result["execution"] = {
                "result_summary": summary,
                "raw_data": raw_data,
                "graph_data": None,
                "chart_data": chart_data,
                "latency": round(exec_latency, 3),
            }
        except Exception as e:
            exec_latency = time.time() - start
            result["execution"] = {
                "result_summary": f"SQL 실행 오류: {str(e)}",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": round(exec_latency, 3),
            }

        return result

    def _extract_sql(self, text: str) -> str:
        """Extract SQL from LLM response, handling ```sql blocks."""
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"```\s*(SELECT.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        sql_lines = []
        for line in lines:
            if line.upper().startswith(("SELECT", "WITH")) or sql_lines:
                sql_lines.append(line)
        return "\n".join(sql_lines) if sql_lines else text.strip()

    def _validate_sql(self, sql: str) -> bool:
        """Validate SQL is read-only (SELECT only)."""
        if FORBIDDEN_SQL_PATTERN.search(sql):
            return False
        cleaned = re.sub(r"'[^']*'", "", sql)
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        if FORBIDDEN_SQL_PATTERN.search(cleaned):
            return False
        return True

    def _ensure_limit(self, sql: str) -> str:
        """Add LIMIT if not present."""
        if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            sql = sql.rstrip(";").strip() + f" LIMIT {Config.SQL_MAX_ROWS}"
        return sql

    def _execute_sql(self, sql: str) -> tuple[list, list]:
        """Execute SQL against Aurora PG with timeout."""
        with self.engine.connect() as conn:
            conn.execute(text(f"SET statement_timeout = '{Config.SQL_TIMEOUT_SECONDS}s'"))
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchmany(Config.SQL_MAX_ROWS)
            return rows, columns
