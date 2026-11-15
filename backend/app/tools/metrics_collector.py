import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

METRICS_DIR = Path(__file__).resolve().parent.parent / "metrics"
METRICS_FILE = METRICS_DIR / "metrics.jsonl"


class MetricsCollector:
    """
    Collects performance, latency, tokens, retries, and execution metrics for a pipeline run.
    """

    def __init__(self, run_id: str, prompt: str):
        self.run_id = run_id
        self.prompt = prompt
        self.start_time = time.perf_counter()
        self.per_agent_latency: Dict[str, float] = {
            "intent": 0.0,
            "planner": 0.0,
            "architect": 0.0,
            "coder": 0.0,
            "reviewer": 0.0,
            "runner": 0.0,
        }
        self.llm_calls: int = 0
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.total_tokens: int = 0
        self.retries_used: int = 0
        self.reviewer_issues_per_attempt: List[Dict[str, Any]] = []
        self.execution_success: bool = False
        self.files_generated: int = 0
        self.total_latency_ms: float = 0.0

    @contextmanager
    def measure(self, agent_name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            self.per_agent_latency[agent_name] = round(
                self.per_agent_latency.get(agent_name, 0.0) + elapsed_ms, 2
            )

    def record_agent_latency(self, agent_name: str, duration_ms: float):
        self.per_agent_latency[agent_name] = round(
            self.per_agent_latency.get(agent_name, 0.0) + duration_ms, 2
        )

    def record_llm_usage(self, usage: Dict[str, Any]):
        if not usage:
            return
        cum = usage.get("cumulative_usage", usage)
        self.llm_calls += usage.get("llm_calls", 1)
        self.input_tokens += cum.get("input_tokens", 0)
        self.output_tokens += cum.get("output_tokens", 0)
        self.total_tokens += cum.get("total_tokens", self.input_tokens + self.output_tokens)

    def record_attempts(self, attempts: List[Dict[str, Any]]):
        self.reviewer_issues_per_attempt = []
        for att in attempts:
            issues = att.get("review", {}).get("issues", [])
            counts = att.get("issues_count", {
                "critical": sum(1 for i in issues if i.get("severity") == "critical"),
                "major": sum(1 for i in issues if i.get("severity") == "major"),
                "minor": sum(1 for i in issues if i.get("severity") == "minor"),
                "total": len(issues),
            })
            self.reviewer_issues_per_attempt.append({
                "attempt": att.get("attempt", len(self.reviewer_issues_per_attempt) + 1),
                "critical": counts.get("critical", 0),
                "major": counts.get("major", 0),
                "minor": counts.get("minor", 0),
                "total": counts.get("total", 0),
            })
        self.retries_used = max(0, len(attempts) - 1)

    def finish(
        self,
        files_count: int,
        execution_result: Optional[Dict[str, Any]] = None,
        llm=None,
    ) -> Dict[str, Any]:
        self.total_latency_ms = round((time.perf_counter() - self.start_time) * 1000, 2)
        self.files_generated = files_count

        if execution_result:
            self.execution_success = bool(
                execution_result.get("success", False)
                and execution_result.get("exit_code") == 0
            )
        else:
            self.execution_success = False

        if llm and hasattr(llm, "get_usage"):
            self.record_llm_usage(llm.get_usage())

        record = {
            "run_id": self.run_id,
            "prompt": self.prompt,
            "per_agent_latency_ms": self.per_agent_latency,
            "total_latency_ms": self.total_latency_ms,
            "llm_calls": self.llm_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "retries_used": self.retries_used,
            "reviewer_issues_per_attempt": self.reviewer_issues_per_attempt,
            "execution_success": self.execution_success,
            "files_generated": self.files_generated,
        }

        self._save(record)
        return record

    def _save(self, record: Dict[str, Any]):
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def compute_aggregates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes statistical aggregates over metric records.
    """
    if not records:
        return {
            "total_runs": 0,
            "success_rate": 0.0,
            "execution_error_rate": 0.0,
            "avg_total_latency_ms": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "per_agent_avg_latency_ms": {
                "intent": 0.0,
                "planner": 0.0,
                "architect": 0.0,
                "coder": 0.0,
                "reviewer": 0.0,
                "runner": 0.0,
            },
            "avg_llm_calls": 0.0,
            "avg_input_tokens": 0.0,
            "avg_output_tokens": 0.0,
            "avg_total_tokens": 0.0,
            "avg_retries": 0.0,
            "avg_files_generated": 0.0,
            "avg_issue_reduction_rate": 0.0,
        }

    n = len(records)
    successful = sum(1 for r in records if r.get("execution_success"))
    success_rate = round(successful / n, 4)

    latencies = sorted(r.get("total_latency_ms", 0.0) for r in records)
    p50_idx = int(0.50 * (n - 1))
    p95_idx = int(0.95 * (n - 1))
    p50_lat = round(latencies[p50_idx], 2)
    p95_lat = round(latencies[p95_idx], 2)
    avg_lat = round(sum(latencies) / n, 2)

    # Per-agent averages
    agents = ["intent", "planner", "architect", "coder", "reviewer", "runner"]
    agent_avgs: Dict[str, float] = {}
    for ag in agents:
        vals = [r.get("per_agent_latency_ms", {}).get(ag, 0.0) for r in records]
        agent_avgs[ag] = round(sum(vals) / n, 2)

    avg_llm = round(sum(r.get("llm_calls", 0) for r in records) / n, 2)
    avg_inp = round(sum(r.get("input_tokens", 0) for r in records) / n, 2)
    avg_out = round(sum(r.get("output_tokens", 0) for r in records) / n, 2)
    avg_tok = round(sum(r.get("total_tokens", 0) for r in records) / n, 2)
    avg_ret = round(sum(r.get("retries_used", 0) for r in records) / n, 2)
    avg_files = round(sum(r.get("files_generated", 0) for r in records) / n, 2)

    # Issue reduction calculation (first attempt vs final attempt)
    reductions = []
    for r in records:
        issues_per_att = r.get("reviewer_issues_per_attempt", [])
        if len(issues_per_att) >= 2:
            first_issues = issues_per_att[0].get("total", 0)
            final_issues = issues_per_att[-1].get("total", 0)
            if first_issues > 0:
                red = (first_issues - final_issues) / first_issues
                reductions.append(max(0.0, red))
        elif len(issues_per_att) == 1:
            first_issues = issues_per_att[0].get("total", 0)
            if first_issues == 0:
                reductions.append(1.0)

    avg_red = round((sum(reductions) / len(reductions)) * 100, 2) if reductions else 0.0

    return {
        "total_runs": n,
        "success_rate": success_rate,
        "execution_error_rate": round(1.0 - success_rate, 4),
        "avg_total_latency_ms": avg_lat,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "per_agent_avg_latency_ms": agent_avgs,
        "avg_llm_calls": avg_llm,
        "avg_input_tokens": avg_inp,
        "avg_output_tokens": avg_out,
        "avg_total_tokens": avg_tok,
        "avg_retries": avg_ret,
        "avg_files_generated": avg_files,
        "avg_issue_reduction_rate": avg_red,
    }


def load_all_metrics() -> List[Dict[str, Any]]:
    records = []
    if METRICS_FILE.exists():
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
    return records
