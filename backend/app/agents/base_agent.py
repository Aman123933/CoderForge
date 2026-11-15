import json
import time
import logging
from typing import Any, Dict, Optional


class BaseAgent:
    """
    Base class for all agents.
    Centralizes LLM calls, retries, logging, and response discipline.
    """

    def __init__(
        self,
        llm,
        *,
        max_retries: int = 2,
        retry_backoff_sec: float = 0.8,
        require_json: bool = True,
        agent_name: Optional[str] = None,
    ):
        """
        Args:
            llm: LLM client with `generate(prompt: str) -> str`
            max_retries: Number of retries on transient failures
            retry_backoff_sec: Base backoff between retries
            require_json: Enforce raw JSON-only responses
            agent_name: Optional name for logging
        """
        self.llm = llm
        self.max_retries = max_retries
        self.retry_backoff_sec = retry_backoff_sec
        self.require_json = require_json
        self.agent_name = agent_name or self.__class__.__name__
        self.logger = logging.getLogger(self.agent_name)

    # ---------- Core Execution ----------

    def call_llm(self, prompt: str) -> str:
        """
        Executes a prompt with retries and basic safety checks.
        """
        last_err: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug("LLM call attempt %s", attempt + 1)
                if hasattr(self.llm, "generate_json") and self.require_json:
                    response = self.llm.generate_json(prompt)
                else:
                    response = self.llm.generate(prompt)

                if not isinstance(response, str) or not response.strip():
                    raise ValueError("Empty or non-text LLM response")


                if self.require_json and response.lstrip().startswith("```"):
                    raise ValueError("Markdown detected; expected raw JSON")

                return response

            except Exception as e:
                last_err = e
                err_msg = str(e)
                wait_time = self.retry_backoff_sec * (attempt + 1)
                if "429" in err_msg or "quota" in err_msg.lower():
                    wait_time = 30.0
                    self.logger.warning(
                        "Rate limit (429) hit. Waiting %ss before retry (attempt %s/%s)",
                        wait_time,
                        attempt + 1,
                        self.max_retries + 1,
                    )
                else:
                    self.logger.warning(
                        "LLM call failed (attempt %s/%s): %s",
                        attempt + 1,
                        self.max_retries + 1,
                        err_msg,
                    )
                if attempt < self.max_retries:
                    time.sleep(wait_time)


        raise RuntimeError(
            f"{self.agent_name}: LLM call failed after retries"
        ) from last_err

    # ---------- Helpers ----------

    def parse_json(self, response_text: str) -> Dict[str, Any]:
        """
        Strict JSON parsing. Fails fast.
        """
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"{self.agent_name}: response is not valid JSON"
            ) from e


    def validate_required_keys(self, data: Dict[str, Any], required_keys: set[str]) -> None:
        missing = required_keys - data.keys()
        if missing:
            raise ValueError(
                f"{self.agent_name}: missing required keys: {missing}"
            )
