"""Shared AI client fixtures for tests.

`test_helpers.FakeAIClient` returns prose. This one returns an exact scripted
response, or raises, for JSON prompts and degradation paths.
"""

from typing import Any, Optional


class ScriptedAIClient:
    """AI client returning a scripted response, or raising a scripted error."""

    def __init__(self, response: str = "", error: Optional[Exception] = None) -> None:
        """Store the scripted behaviour.

        Args:
            response: What `chat_completion` returns when no error is set.
            error: Raised by `chat_completion` instead of returning, when set.
        """
        self.response = response
        self.error = error
        self.calls = 0

    def chat_completion(self, *args: Any, **kwargs: Any) -> str:
        """Return the scripted response or raise the scripted error.

        Args:
            *args: Ignored; accepted for protocol compatibility.
            **kwargs: Ignored; accepted for protocol compatibility.

        Returns:
            The scripted response string.

        Raises:
            Exception: The scripted error, when one was supplied.
        """
        del args, kwargs
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.response

    def call_count(self) -> int:
        """Return how many times `chat_completion` has been called.

        Returns:
            The call count.
        """
        return self.calls
