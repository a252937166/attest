"""Tavily grounding: live documentation for external references named by the specification stage.

Tavily is a separate paid service (API credits, one per basic search request that reaches it); its use is recorded in the run's
grounding record (`calls`, the account's usage before and after), never folded into the inference ledger. A search whose
connection failed before any byte of it was written consumed nothing and is sent again (bounded, revision 8); a search whose
answer was lost is not.

Revision 9 (20 Oct 2026): a search whose outcome is uncertain (its answer was lost after it was sent, or Tavily answered HTTP 5xx) ends
the grounding stage at once: no further search and no usage read are sent, the record carries `uncertain`, and the pipeline stops the
run for reconciliation. An HTTP 4xx answer is a definite refusal and the next query is still tried.

Revision 10 (20 Oct 2026): answers are checked before use. A search answer that cannot be read (`search_problem`, or a body the HTTP
layer could not decode) reached Tavily, so it is uncertain like a lost answer and ends grounding the same way; a usage answer that
cannot be read sets `malformed` (no search is sent when it is the first read) and the pipeline stops the run (`malformed_response`)."""

from __future__ import annotations

import time

from ..http import (NOT_SENT_BACKOFF_S, NOT_SENT_RETRIES, READ_BACKOFF_S, READ_RETRIES, HttpError, MalformedResponse, TransportError, backoff, is_number,
                    kind_of, post_outcome, request_json)
from ..ledger import utcnow

BASE = "https://api.tavily.com"


class Tavily:
    def __init__(self, api_key: str, max_queries: int = 3, max_results: int = 3):
        self._key = api_key
        self.max_queries = max_queries
        self.max_results = max_results
        self.calls = 0  # search requests that reached Tavily (each may consume an API credit)
        self.not_sent = 0  # search attempts that failed before any byte was written (no credit)
        self._sleep = time.sleep

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def usage(self) -> dict | None:
        """The account's usage (advisory). A malformed answer raises MalformedResponse (revision 10: `ground` stops the run); any other
        failure gives None (unknown)."""
        for retry in range(READ_RETRIES + 1):
            try:
                _, body, _ = request_json("GET", BASE + "/usage", self._headers(), timeout=30)
                return body
            except MalformedResponse:
                raise
            except HttpError:
                return None
            except TransportError:
                if retry == READ_RETRIES:
                    return None
                self._sleep(backoff(READ_BACKOFF_S, retry))
        return None

    def search(self, query: str) -> list[dict]:
        payload = {"query": query, "max_results": self.max_results, "search_depth": "basic", "include_answer": False}
        for retry in range(NOT_SENT_RETRIES + 1):
            try:
                _, body, _ = request_json("POST", BASE + "/search", self._headers(), payload, timeout=40)
            except TransportError as error:
                if error.request_sent:
                    self.calls += 1  # it may have reached Tavily and consumed a credit
                    raise
                self.not_sent += 1
                if retry == NOT_SENT_RETRIES:
                    raise
                self._sleep(backoff(NOT_SENT_BACKOFF_S, retry))
                continue
            except HttpError:
                self.calls += 1
                raise
            self.calls += 1
            problem = search_problem(body)
            if problem:
                # it reached Tavily (a credit may be spent) and the answer cannot be read: uncertain, the run stops (revision 10)
                raise MalformedResponse(problem, status=200)
            return [{"title": r.get("title"), "url": r.get("url"), "excerpt": (r.get("content") or "")[:600], "score": r.get("score")}
                    for r in body["results"]]
        return []


def search_problem(body) -> str | None:
    """Why a search answer cannot be read, or None (revision 10): an object whose `results` is an array of objects with string-or-null
    title, url and content and a numeric-or-null score."""
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        return f"the search answer's results are {kind_of(results)}, not an array" if isinstance(body, dict) else f"the search answer is {kind_of(body)}"
    for item in results:
        if not isinstance(item, dict):
            return f"a search result is {kind_of(item)}, not an object"
        for key in ("title", "url", "content"):
            if item.get(key) is not None and not isinstance(item[key], str):
                return f"a search result's {key} is {kind_of(item[key])}, not a string"
        if item.get("score") is not None and not is_number(item["score"]):
            return "a search result's score is not a number"
    return None


def ground(queries: list[str], tavily: Tavily | None) -> dict:
    record = {"provider": "tavily", "requested_queries": list(queries or []), "queries": [], "sources": [], "calls": 0,
              "usage_before": None, "usage_after": None, "skipped": None}
    if not queries:
        record["skipped"] = "specification named no external references"
        return record
    if tavily is None:
        record["skipped"] = "no Tavily client configured"
        return record
    record["uncertain"] = None
    record["malformed"] = None
    try:
        record["usage_before"] = tavily.usage()
    except MalformedResponse as error:  # revision 10: an unreadable answer stops the run before any search is sent
        record["malformed"] = {"read": "/usage", "problem": error.problem, "when": "before the searches"}
        record["calls"], record["not_sent"] = tavily.calls, tavily.not_sent
        return record
    for index, query in enumerate(queries[: tavily.max_queries]):
        started = utcnow()
        try:
            results = tavily.search(query)
        except (HttpError, TransportError) as error:
            outcome = post_outcome(error)
            record["queries"].append({"query": query, "error": str(error)[:200], "outcome": outcome})
            if outcome == "uncertain":
                # it may have reached Tavily and consumed a credit: nothing further is sent (no search, no usage read) and the run stops
                record["uncertain"] = {"query_index": index, "started_at_utc": started, "phase": getattr(error, "phase", None),
                                       "http_status": getattr(error, "status", None)}
                break
            continue
        record["queries"].append({"query": query, "results": len(results)})
        for r in results:
            record["sources"].append({"query": query, **r})
    record["calls"] = tavily.calls
    record["not_sent"] = tavily.not_sent
    record["billing"] = "Tavily API credits (one per basic search request that reached Tavily); separate from inference and Sandboxes"
    if not record["uncertain"]:
        try:
            record["usage_after"] = tavily.usage()
        except MalformedResponse as error:
            record["malformed"] = {"read": "/usage", "problem": error.problem, "when": "after the searches"}
    return record


def sources_text(record: dict | None, limit: int = 6000) -> str:
    if not record or not record.get("sources"):
        return ""
    lines = ["GROUNDING SOURCES (retrieved live with Tavily; cite URLs in docstrings or comments where they justify a decision):"]
    for s in record["sources"]:
        lines.append(f"- [{s.get('title')}]({s.get('url')}) for query '{s.get('query')}': {s.get('excerpt', '')[:400]}")
    text = "\n".join(lines)
    return text if len(text) <= limit else text[:limit] + "\n...[sources truncated]..."
