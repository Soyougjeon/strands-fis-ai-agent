"""Visualization API routes - graph and chart data endpoints."""

import logging
from urllib.parse import urlencode

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests as http_requests
from fastapi import APIRouter, HTTPException, Query

from backend.config import Config
from backend.services.conversation import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualize", tags=["visualize"])


@router.get("/graph/{session_id}/{turn_id}")
async def get_graph(session_id: str, turn_id: str):
    """Get graph data for a specific turn."""
    service = ConversationService()
    session = service.get_session(session_id)

    for turn in session.get("turns", []):
        if turn.get("turn_id") == turn_id:
            exec_data = turn.get("agent_process", {}).get("query_execution", {})
            graph_data = exec_data.get("graph_data")
            if graph_data:
                return graph_data
            raise HTTPException(status_code=404, detail="해당 턴에 그래프 데이터가 없습니다.")

    raise HTTPException(status_code=404, detail="턴을 찾을 수 없습니다.")


@router.get("/entity-graph/{tenant}")
async def get_entity_graph(tenant: str, search: str = Query(default="", description="Entity search keyword")):
    """Load entity graph data from Neptune for a tenant. With search, finds entity neighborhood."""
    tenant_map = {"ETF": "etf", "Bond": "bond", "Fund": "fund"}
    t = tenant_map.get(tenant)
    if not t:
        raise HTTPException(status_code=400, detail=f"Invalid tenant: {tenant}")

    try:
        url = f"https://{Config.NEPTUNE_ENDPOINT}:{Config.NEPTUNE_PORT}/openCypher"

        if search.strip():
            # Search mode: find the entity and its 1-hop + 2-hop neighborhood
            safe_search = search.strip().replace("'", "\\'")
            cypher = (
                f"MATCH (center:`__Entity__{t}__`)-[r1:`__RELATION__`]->(neighbor:`__Entity__{t}__`) "
                f"WHERE center.value CONTAINS '{safe_search}' "
                f"RETURN center.value AS source, center.class AS source_class, "
                f"r1.value AS relation, "
                f"neighbor.value AS target, neighbor.class AS target_class "
                f"LIMIT 100 "
                f"UNION "
                f"MATCH (other:`__Entity__{t}__`)-[r2:`__RELATION__`]->(center:`__Entity__{t}__`) "
                f"WHERE center.value CONTAINS '{safe_search}' "
                f"RETURN other.value AS source, other.class AS source_class, "
                f"r2.value AS relation, "
                f"center.value AS target, center.class AS target_class "
                f"LIMIT 100"
            )
        else:
            # Default: random sample of domain graph
            cypher = (
                f"MATCH (e:`__Entity__{t}__`)-[r:`__RELATION__`]->(f:`__Entity__{t}__`) "
                f"RETURN e.value AS source, e.class AS source_class, "
                f"r.value AS relation, "
                f"f.value AS target, f.class AS target_class LIMIT 200"
            )
        body = urlencode({"query": cypher})

        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        req = AWSRequest(
            method="POST", url=url, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        SigV4Auth(creds, "neptune-db", Config.AWS_REGION).add_auth(req)

        resp = http_requests.post(url, data=body, headers=dict(req.headers), timeout=30)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        nodes = {}
        edges = []
        for rec in results:
            src = str(rec.get("source", ""))
            tgt = str(rec.get("target", ""))
            rel = str(rec.get("relation", ""))
            src_class = str(rec.get("source_class", "Entity"))
            tgt_class = str(rec.get("target_class", "Entity"))
            if src and src not in nodes:
                nodes[src] = {"id": src, "label": src, "type": src_class, "properties": {}}
            if tgt and tgt not in nodes:
                nodes[tgt] = {"id": tgt, "label": tgt, "type": tgt_class, "properties": {}}
            if src and tgt:
                edges.append({"source": src, "target": tgt, "label": rel, "properties": {}})

        return {"nodes": list(nodes.values()), "edges": edges}
    except Exception as e:
        logger.error(f"Graph network load error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph")
async def get_knowledge_graph(
    tenant: str = Query(description="Tenant ID (etfgrag, bondgrag, fundgrag)"),
    mode: str = Query(default="sources", description="Query mode: sources, entities, entity-paths, schema"),
    entity1: str = Query(default="", description="Entity 1 for path search"),
    entity2: str = Query(default="", description="Entity 2 for path search"),
    depth: int = Query(default=2, ge=1, le=3, description="Path depth (1-3)"),
):
    """Query graphrag-toolkit Knowledge Graph using toolkit's visualization Cypher patterns."""
    valid_tenants = {"etfgrag", "bondgrag", "fundgrag"}
    if tenant not in valid_tenants:
        raise HTTPException(status_code=400, detail=f"Invalid tenant: {tenant}. Use: {valid_tenants}")

    try:
        from graphrag_toolkit.lexical_graph.tenant_id import TenantId
        tid = TenantId(tenant)
        # format_label returns backtick-wrapped labels; strip them since Cypher f-strings add their own
        label_entity = tid.format_label("__Entity__").strip("`")
        label_source = tid.format_label("__Source__").strip("`")

        if mode == "schema":
            label_cls = tid.format_label("__SYS_Class__").strip("`")
            cypher = (
                f"MATCH (n:`{label_cls}`) "
                f"WITH n, n.count AS score ORDER BY score DESC LIMIT 100 "
                f"CALL {{ WITH n MATCH p=(n)-[r]->(x) WITH p, r.count AS score ORDER BY score DESC LIMIT 10 RETURN p }} "
                f"RETURN DISTINCT p"
            )
        elif mode == "entity-paths":
            if not entity1.strip():
                raise HTTPException(status_code=400, detail="entity1 is required for entity-paths mode")
            safe_e1 = entity1.strip().lower().replace("'", "\\'")
            if entity2.strip():
                safe_e2 = entity2.strip().lower().replace("'", "\\'")
                cypher = (
                    f"MATCH p=(e1:`{label_entity}`)-[:`__RELATION__`*1..{depth}]-(e2:`{label_entity}`) "
                    f"WHERE e1.search_str starts with '{safe_e1}' "
                    f"AND e2.search_str starts with '{safe_e2}' "
                    f"AND e1 <> e2 "
                    f"RETURN p LIMIT 1000"
                )
            else:
                cypher = (
                    f"MATCH p=(e1:`{label_entity}`)-[:`__RELATION__`*1..{depth}]-() "
                    f"WHERE e1.search_str starts with '{safe_e1}' "
                    f"RETURN p LIMIT 1000"
                )
        elif mode == "sources":
            # Toolkit: get_sources_query (exact pattern)
            cypher = (
                f"MATCH p=(source:`{label_source}`)<-[:`__EXTRACTED_FROM__`]-()"
                f"<-[:`__MENTIONED_IN__`]-()<-[:`__BELONGS_TO__`]-()"
                f"<-[:`__SUPPORTS__`]-()<-[:`__SUBJECT__`|`__OBJECT__`]-() "
                f"RETURN p LIMIT 1000"
            )
        else:
            # entities mode (default) - toolkit's Entity + RELATION graph
            cypher = (
                f"MATCH p=(:`{label_entity}`)-[:`__RELATION__`]-() "
                f"RETURN p LIMIT 1000"
            )

        url = f"https://{Config.NEPTUNE_ENDPOINT}:{Config.NEPTUNE_PORT}/openCypher"
        body = urlencode({"query": cypher})

        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        req = AWSRequest(
            method="POST", url=url, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        SigV4Auth(creds, "neptune-db", Config.AWS_REGION).add_auth(req)
        resp = http_requests.post(url, data=body, headers=dict(req.headers), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        # Path queries return 'p' with full path data; tabular queries return columns
        nodes = {}
        edges = []

        if mode in ("entities", "entity-paths", "sources", "schema"):
            # Parse path results
            for rec in results:
                path = rec.get("p", [])
                if not isinstance(path, list):
                    continue
                prev_node_id = None
                for elem in path:
                    etype = elem.get("~entityType", "")
                    if etype == "node":
                        nid = elem.get("~id", "")
                        props = elem.get("~properties", {})
                        label = props.get("value") or props.get("source") or props.get("topic") or nid
                        ntype = props.get("class", "Entity")
                        labels = elem.get("~labels", [])
                        # Clean up toolkit labels
                        for l in labels:
                            if l.startswith("__Entity__"):
                                ntype = props.get("class", "Entity")
                            elif "Source" in l:
                                ntype = "Source"
                            elif "Chunk" in l:
                                ntype = "Chunk"
                            elif "Topic" in l:
                                ntype = "Topic"
                            elif "Statement" in l:
                                ntype = "Statement"
                            elif "Fact" in l:
                                ntype = "Fact"
                            elif "SYS_Class" in l:
                                ntype = label
                        if nid not in nodes:
                            nodes[nid] = {"id": nid, "label": str(label), "type": ntype, "properties": {}}
                        prev_node_id = nid
                    elif etype == "relationship":
                        rid = elem.get("~id", "")
                        rtype = elem.get("~type", "").lower().replace("__", "")
                        props = elem.get("~properties", {})
                        rvalue = props.get("value", rtype)
                        src = elem.get("~start", "")
                        tgt = elem.get("~end", "")
                        if src and tgt:
                            edges.append({"source": src, "target": tgt, "label": str(rvalue), "properties": {}})
        else:
            # Tabular results (entities mode)
            for rec in results:
                src = str(rec.get("source", ""))
                tgt = str(rec.get("target", ""))
                rel = str(rec.get("relation", ""))
                src_cls = str(rec.get("source_class", "Entity"))
                tgt_cls = str(rec.get("target_class", "Entity"))
                if src and src not in nodes:
                    nodes[src] = {"id": src, "label": src, "type": src_cls, "properties": {}}
                if tgt and tgt not in nodes:
                    nodes[tgt] = {"id": tgt, "label": tgt, "type": tgt_cls, "properties": {}}
                if src and tgt:
                    edges.append({"source": src, "target": tgt, "label": rel, "properties": {}})

        return {"nodes": list(nodes.values()), "edges": edges}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge graph query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart/{session_id}/{turn_id}")
async def get_chart(session_id: str, turn_id: str):
    """Get chart data for a specific turn."""
    service = ConversationService()
    session = service.get_session(session_id)

    for turn in session.get("turns", []):
        if turn.get("turn_id") == turn_id:
            exec_data = turn.get("agent_process", {}).get("query_execution", {})
            chart_data = exec_data.get("chart_data")
            if chart_data:
                return chart_data
            raise HTTPException(status_code=404, detail="해당 턴에 차트 데이터가 없습니다.")

    raise HTTPException(status_code=404, detail="턴을 찾을 수 없습니다.")
