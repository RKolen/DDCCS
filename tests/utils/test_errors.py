"""
Tests for the error handling system.

Tests the DnDError exception classes, handle_errors decorator,
and error wrapping functions from src.utils.errors.
"""

from src.utils.errors import (
    DnDError,
    UserInputError,
    InvalidChoiceError,
    MissingDataError,
    DnDFileNotFoundError,
    FileParseError,
    AIConnectionError,
    AIResponseError,
    AITimeoutError,
    MissingConfigError,
    SchemaValidationError,
    handle_errors,
    wrap_exception,
)


class TestDnDBaseError:
    """Tests for the base DnDError class."""

    def test_creates_basic_error(self):
        """Basic error creation works."""
        error = DnDError("Test error message")
        assert error.message == "Test error message"
        assert error.user_guidance is None
        assert error.recoverable is True
        assert error.context == {}

    def test_creates_error_with_guidance(self):
        """Error with user guidance works."""
        error = DnDError(
            "Test error",
            user_guidance="Try again",
            recoverable=False
        )
        assert error.message == "Test error"
        assert error.user_guidance == "Try again"
        assert error.recoverable is False

    def test_error_str_includes_guidance(self):
        """String representation includes guidance when present."""
        error = DnDError("Test error", user_guidance="Fix this")
        assert "Test error" in str(error)
        assert "Fix this" in str(error)

    def test_error_str_without_guidance(self):
        """String representation excludes guidance when not present."""
        error = DnDError("Test error")
        assert str(error) == "Test error"

    def test_error_context_stored(self):
        """Error context is stored correctly."""
        error = DnDError("Test", context={"key": "value"})
        assert error.context == {"key": "value"}

    def test_error_exception_inheritance(self):
        """DnDError inherits from Exception."""
        error = DnDError("Test")
        assert isinstance(error, Exception)


class TestUserInputErrors:
    """Tests for user input error types."""

    def test_invalid_choice_error(self):
        """InvalidChoiceError formats options correctly."""
        error = InvalidChoiceError("invalid", ["a", "b", "c"])
        assert "invalid" in error.message
        assert error.recoverable is True

    def test_invalid_choice_with_many_options(self):
        """InvalidChoiceError handles many options."""
        error = InvalidChoiceError("x", ["a", "b", "c", "d", "e", "f"])
        assert "x" in error.message
        assert error.recoverable is True

    def test_missing_data_error(self):
        """MissingDataError provides helpful guidance."""
        error = MissingDataError("characters", "creating a story")
        assert "characters" in error.message
        assert "creating a story" in error.user_guidance
        assert error.recoverable is True


class TestFileSystemErrors:
    """Tests for file system error types."""

    def test_file_not_found_error(self):
        """DnDFileNotFoundError includes filepath and type."""
        error = DnDFileNotFoundError("/path/to/file.json", "character file")
        assert "/path/to/file.json" in error.message
        assert "character file" in error.message
        assert error.recoverable is True

    def test_file_parse_error(self):
        """FileParseError shows expected format."""
        error = FileParseError("file.json", "Invalid JSON", "JSON")
        assert "file.json" in error.message
        assert "Invalid JSON" in error.message
        assert "JSON" in error.user_guidance
        assert error.recoverable is True


class TestAIErrors:
    """Tests for AI integration error types."""

    def test_ai_connection_error(self):
        """AIConnectionError includes service info."""
        error = AIConnectionError("OpenAI", "Connection refused")
        assert "OpenAI" in error.message
        assert error.recoverable is True

    def test_ai_response_error(self):
        """AIResponseError includes operation details."""
        error = AIResponseError("story generation", "Invalid response format")
        assert "story generation" in error.message
        assert error.recoverable is True

    def test_ai_timeout_error(self):
        """AITimeoutError includes operation info."""
        error = AITimeoutError("API request")
        assert "API request" in error.message
        assert error.recoverable is True


class TestConfigurationErrors:
    """Tests for configuration error types."""

    def test_missing_config_error(self):
        """MissingConfigError provides fix guidance."""
        error = MissingConfigError("API key", "Add it to config.json")
        assert "API key" in error.message
        assert "config.json" in error.user_guidance
        assert error.recoverable is True

    def test_missing_config_error_defaults(self):
        """MissingConfigError has correct defaults."""
        error = MissingConfigError("test", "fix it")
        assert error.recoverable is True
        assert error.context == {}


class TestValidationErrors:
    """Tests for validation error types."""

    def test_schema_validation_error(self):
        """SchemaValidationError formats error list."""
        errors = ["Field 'name' is required", "Field 'level' must be int"]
        error = SchemaValidationError("character", errors)
        assert "character" in error.message
        assert "name" in error.user_guidance
        assert "level" in error.user_guidance
        assert error.recoverable is True

    def test_schema_validation_empty_errors(self):
        """SchemaValidationError handles empty error list."""
        error = SchemaValidationError("test", [])
        assert error.recoverable is True
        assert error.context == {"data_type": "test", "errors": []}


class TestHandleErrorsDecorator:
    """Tests for handle_errors decorator."""

    def test_returns_value_on_success(self):
        """Successful function returns value."""
        @handle_errors()
        def success_func():
            return "success"

        assert success_func() == "success"

    def test_returns_default_on_error(self):
        """Failed function returns default."""
        @handle_errors(ValueError, default_return=None)
        def fail_func():
            raise ValueError("test")

        assert fail_func() is None

    def test_handles_multiple_error_types(self):
        """Decorator handles multiple error types."""
        @handle_errors(ValueError, KeyError, default_return="default")
        def multi_fail(error_type):
            if error_type == "value":
                raise ValueError("test")
            raise KeyError("test")

        assert multi_fail("value") == "default"
        assert multi_fail("key") == "default"

    def test_propagates_non_handled_errors(self):
        """Non-handled errors propagate up."""
        @handle_errors(ValueError, default_return="default")
        def raise_type_error():
            raise TypeError("test")

        propagated = False
        try:
            raise_type_error()
        except TypeError:
            propagated = True
        assert propagated is True

    def test_passes_args_through(self):
        """Arguments are passed through to function."""
        @handle_errors()
        def func_with_args(a, b):
            return a + b

        assert func_with_args(1, 2) == 3

    def test_passes_kwargs_through(self):
        """Keyword arguments are passed through."""
        @handle_errors()
        def func_with_kwargs(a, b=0):
            return a + b

        assert func_with_kwargs(1, b=2) == 3


class TestWrapException:
    """Tests for wrap_exception function."""

    def test_dnd_error_passthrough(self):
        """DnDError types pass through unchanged."""
        original = AIConnectionError("test")
        wrapped = wrap_exception(original)
        assert wrapped is original

    def test_wraps_file_not_found(self):
        """FileNotFoundError is wrapped correctly."""
        original = FileNotFoundError("test.json")
        wrapped = wrap_exception(original, {})
        assert isinstance(wrapped, DnDFileNotFoundError)
        assert "test.json" in wrapped.message

    def test_wraps_value_error(self):
        """ValueError is wrapped as UserInputError."""
        original = ValueError("invalid value")
        wrapped = wrap_exception(original, {})
        assert isinstance(wrapped, UserInputError)
        assert "invalid value" in wrapped.message

    def test_wraps_key_error(self):
        """KeyError is wrapped as MissingDataError."""
        original = KeyError("character_name")
        wrapped = wrap_exception(original, {})
        assert isinstance(wrapped, MissingDataError)
        assert "character_name" in wrapped.message

    def test_wraps_generic_exception(self):
        """Unknown exceptions are wrapped as generic DnDError."""
        original = RuntimeError("unknown error")
        wrapped = wrap_exception(original, {})
        assert isinstance(wrapped, DnDError)
        assert "unknown error" in wrapped.message
