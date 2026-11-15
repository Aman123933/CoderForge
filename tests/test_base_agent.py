import pytest
from backend.app.agents.base_agent import BaseAgent


class MockLLM:
    def __init__(self, responses=None, fail_count=0):
        self.responses = list(responses or [])
        self.fail_count = fail_count
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.fail_count > 0:
            self.fail_count -= 1
            raise RuntimeError("Transient connection error")
        if self.responses:
            return self.responses.pop(0)
        return '{"status": "ok"}'


def test_base_agent_parse_json_valid():
    agent = BaseAgent(MockLLM())
    parsed = agent.parse_json('{"key": "value", "number": 42}')
    assert parsed == {"key": "value", "number": 42}


def test_base_agent_parse_json_invalid():
    agent = BaseAgent(MockLLM())
    with pytest.raises(ValueError, match="not valid JSON"):
        agent.parse_json("not a json string")


def test_base_agent_markdown_rejection():
    llm = MockLLM(responses=['```json\n{"key": "value"}\n```'])
    agent = BaseAgent(llm, require_json=True, max_retries=0)
    with pytest.raises(RuntimeError) as exc_info:
        agent.call_llm("prompt")
    assert "Markdown detected" in str(exc_info.value.__cause__)



def test_base_agent_retries_on_failure():
    llm = MockLLM(responses=['{"key": "recovered"}'], fail_count=1)
    agent = BaseAgent(llm, max_retries=2, retry_backoff_sec=0.01)
    res = agent.call_llm("prompt")
    assert res == '{"key": "recovered"}'
    assert llm.calls == 2


def test_base_agent_exceeds_max_retries():
    llm = MockLLM(fail_count=5)
    agent = BaseAgent(llm, max_retries=2, retry_backoff_sec=0.01)
    with pytest.raises(RuntimeError, match="LLM call failed after retries"):
        agent.call_llm("prompt")
    assert llm.calls == 3


def test_validate_required_keys_success():
    agent = BaseAgent(MockLLM())
    data = {"name": "test", "type": "app", "version": 1}
    agent.validate_required_keys(data, {"name", "type"})


def test_validate_required_keys_missing():
    agent = BaseAgent(MockLLM())
    data = {"name": "test"}
    with pytest.raises(ValueError, match="missing required keys"):
        agent.validate_required_keys(data, {"name", "version", "type"})
