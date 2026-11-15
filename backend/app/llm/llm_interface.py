from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """
    Contract that all LLM clients must follow.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generates a response from the LLM.

        Args:
            prompt: Full prompt string

        Returns:
            Raw text output from the model
        """
        pass
