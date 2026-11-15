from backend.app.tools.metrics_collector import MetricsCollector, compute_aggregates


def test_metrics_collector_measure_and_finish():
    collector = MetricsCollector(run_id="run-123", prompt="Test Prompt")

    with collector.measure("intent"):
        pass

    with collector.measure("coder"):
        pass

    collector.record_attempts([
        {
            "attempt": 1,
            "issues_count": {"critical": 1, "major": 1, "minor": 1, "total": 3},
        },
        {
            "attempt": 2,
            "issues_count": {"critical": 0, "major": 0, "minor": 0, "total": 0},
        },
    ])

    dummy_llm = type(
        "DummyLLM",
        (),
        {
            "get_usage": lambda self: {
                "llm_calls": 2,
                "cumulative_usage": {
                    "input_tokens": 500,
                    "output_tokens": 200,
                    "total_tokens": 700,
                },
            }
        },
    )()

    record = collector.finish(
        files_count=2,
        execution_result={"success": True, "exit_code": 0},
        llm=dummy_llm,
    )

    assert record["run_id"] == "run-123"
    assert record["execution_success"] is True
    assert record["retries_used"] == 1
    assert record["files_generated"] == 2
    assert record["input_tokens"] == 500
    assert record["output_tokens"] == 200
    assert len(record["reviewer_issues_per_attempt"]) == 2


def test_compute_aggregates_empty():
    agg = compute_aggregates([])
    assert agg["total_runs"] == 0
    assert agg["success_rate"] == 0.0


def test_compute_aggregates_multiple_records():
    records = [
        {
            "run_id": "r1",
            "execution_success": True,
            "total_latency_ms": 100.0,
            "input_tokens": 50,
            "output_tokens": 25,
            "total_tokens": 75,
            "retries_used": 0,
            "files_generated": 2,
            "reviewer_issues_per_attempt": [{"attempt": 1, "total": 0}],
            "per_agent_latency_ms": {"intent": 20.0, "coder": 80.0},
        },
        {
            "run_id": "r2",
            "execution_success": False,
            "total_latency_ms": 200.0,
            "input_tokens": 150,
            "output_tokens": 75,
            "total_tokens": 225,
            "retries_used": 2,
            "files_generated": 1,
            "reviewer_issues_per_attempt": [
                {"attempt": 1, "total": 4},
                {"attempt": 2, "total": 1},
            ],
            "per_agent_latency_ms": {"intent": 40.0, "coder": 160.0},
        },
    ]

    agg = compute_aggregates(records)
    assert agg["total_runs"] == 2
    assert agg["success_rate"] == 0.5
    assert agg["execution_error_rate"] == 0.5
    assert agg["avg_total_latency_ms"] == 150.0
    assert agg["avg_retries"] == 1.0
    assert agg["avg_files_generated"] == 1.5
    assert agg["avg_total_tokens"] == 150.0
