from typing import Dict, Any


class StateStore:
    """
    In-memory state store for a single orchestration run.
    Can be extended later to Redis / DB.
    """

    def __init__(self):
        self._state: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def all(self) -> Dict[str, Any]:
        return self._state.copy()

    def clear(self) -> None:
        self._state.clear()
