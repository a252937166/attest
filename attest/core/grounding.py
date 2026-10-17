"""Tavily grounding: live documentation for external references named by the specification stage."""

from __future__ import annotations

from ..http import HttpError, TransportError, request_json

BASE = "https://api.tavily.com"


class Tavily:
    def __init__(self, api_key: str, max_queries: int = 3, max_results: int = 3):
        self._key = api_key
        self.max_queries = max_queries
        self.max_results = max_results
        self.calls = 0

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def usage(self) -> dict | None:
        try:
            _, body, _ = request_json("GET", BASE + "/usage", self._headers(), timeout=30)
            return body
        except (HttpError, TransportError):
            return None

    def search(self, query: str) -> list[dict]:
        self.calls += 1
        _, body, _ = request_json("POST", BASE + "/search", self._headers(),
                                  {"query": query, "max_results": self.max_results, "search_depth": "basic", "include_answer": False},
                                  timeout=40)
        return [{"title": r.get("title"), "url": r.get("url"), "excerpt": (r.get("content") or "")[:600], "score": r.get("score")}
                for r in (body or {}).get("results", [])]


def ground(queries: list[str], tavily: Tavily | None) -> dict:
    record = {"provider": "tavily", "requested_queries": list(queries or []), "queries": [], "sources": [], "calls": 0,
              "usage_before": None, "usage_after": None, "skipped": None}
    if not queries:
        record["skipped"] = "specification named no external references"
        return record
    if tavily is None:
        record["skipped"] = "no Tavily client configured"
        return record
    record["usage_before"] = tavily.usage()
    for query in queries[: tavily.max_queries]:
        try:
            results = tavily.search(query)
        except (HttpError, TransportError) as error:
            record["queries"].append({"query": query, "error": str(error)[:200]})
            continue
        record["queries"].append({"query": query, "results": len(results)})
        for r in results:
            record["sources"].append({"query": query, **r})
    record["calls"] = tavily.calls
    record["usage_after"] = tavily.usage()
    return record


def sources_text(record: dict | None, limit: int = 6000) -> str:
    if not record or not record.get("sources"):
        return ""
    lines = ["GROUNDING SOURCES (retrieved live with Tavily; cite URLs in docstrings or comments where they justify a decision):"]
    for s in record["sources"]:
        lines.append(f"- [{s.get('title')}]({s.get('url')}) for query '{s.get('query')}': {s.get('excerpt', '')[:400]}")
    text = "\n".join(lines)
    return text if len(text) <= limit else text[:limit] + "\n...[sources truncated]..."
