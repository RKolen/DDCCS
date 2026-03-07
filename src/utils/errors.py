"""
Centralized Error Handling System

Provides consistent, actionable error messages throughout the D&D Consultant system.
All custom exceptions inherit from DnDError to enable catching all
application-specific errors.

Usage:
    from src.utils.errors import (
        DnDError,
        UserInputError,
        AIConnectionError,
        handle_errors,
        display_error,
    )

    # Raise specific errors
    raise UserInputError("Invalid input", user_guidance="Try again with valid input.")

    # Use decorator for consistent handling
    @handle_errors(FileSystemError, AIIntegrationError)
    def my_function():
        # ... code that might raise errors
        pass
"""

import builtins
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

LOGGER = logging.getLogger(__name__)


class DnDError(Exception):
    """Base exception for all D&D Consultant errors.

    All custom exceptions inherit from this class to enable
    catching all application-specific errors.

    Attributes:
        message: The main error message describing what went wrong.
        user_guidance: Optional actionable guidance for the user.
        recoverable: Whether the error can be recovered from without restart.
        context: Additional context data for debugging/logging.
    """

    def __init__(
        self,
        message: str,
        user_guidance: Optional[str] = None,
        recoverable: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a DnDError.

        Args:
            message: The main error message describing what went wrong.
            user_guidance: Optional actionable guidance for the user.
            recoverable: Whether the error can be recovered from without restart.
            context: Additional context data for debugging/logging.
        """
        super().__init__(message)
        self.message = message
        self.user_guidance = user_guidance
        self.recoverable = recoverable
        self.context = context or {}

    def __str__(self) -> str:
        """Return formatted error message with guidance if available."""
        if self.user_guidance:
            return f"{self.message}\n  Guidance: {self.user_guidance}"
        return self.message


# =============================================================================
# User Input Errors
# =============================================================================


class UserInputError(DnDError):
    """Errors caused by invalid user input.

    Use for errors where the user provided incorrect or invalid input
    that can be corrected by re-entering data.
    """


class InvalidChoiceError(UserInputError):
    """User selected an invalid menu option.

    Provides the user with a list of valid options to choose from.
    """

    def __init__(self, choice: str, valid_options: List[str]) -> None:
        """Initialize InvalidChoiceError.

        Args:
            choice: The invalid choice the user made.
            valid_options: List of valid options to display to the user.
        """
        options_display = ", ".join(valid_options[:5])
        if len(valid_options) > 5:
            options_display += "..."
        super().__init__(
            message=f"Invalid selection: '{choice}'",
            user_guidance=f"Please choose from: {options_display}",
        )


class MissingDataError(UserInputError):
    """Required data is missing or empty.

    Use when an operation requires data that has not been provided
    or loaded (e.g., no characters in party, no campaign selected).
    """

    def __init__(self, data_name: str, action: str) -> None:
        """Initialize MissingDataError.

        Args:
            data_name: Name of the missing data (e.g., "characters", "campaign").
            action: The action that requires the data (e.g., "continuing a story").
        """
        super().__init__(
            message=f"No {data_name} available",
            user_guidance=f"You need to add {data_name} before {action}",
            recoverable=True,
        )


# =============================================================================
# File System Errors
# =============================================================================


class FileSystemError(DnDError):
    """Errors related to file operations.

    Base class for all file-related errors including read, write,
    and parse operations.
    """


class DnDFileNotFoundError(FileSystemError):
    """Required file does not exist.

    Note: Named DnDFileNotFoundError to avoid shadowing built-in FileNotFoundError.
    """

    def __init__(
        self, filepath: str, file_type: str = "file", context: Optional[Dict] = None
    ) -> None:
        """Initialize DnDFileNotFoundError.

        Args:
            filepath: Path to the file that was not found.
            file_type: Type of file (e.g., "character", "story", "campaign").
            context: Optional additional context data.
        """
        super().__init__(
            message=f"{file_type.capitalize()} not found: {filepath}",
            user_guidance=f"Check that the {file_type} exists and the path is correct.",
            recoverable=True,
            context={"filepath": filepath, "file_type": file_type, **(context or {})},
        )


class FileParseError(FileSystemError):
    """File content could not be parsed.

    Use when a file exists but its content cannot be parsed as
    the expected format (e.g., invalid JSON, malformed markdown).
    """

    def __init__(
        self,
        filepath: str,
        parse_error: str,
        expected_format: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize FileParseError.

        Args:
            filepath: Path to the file that could not be parsed.
            parse_error: Description of the parsing error.
            expected_format: The expected file format (e.g., "JSON", "markdown").
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Could not parse {filepath}: {parse_error}",
            user_guidance=f"Ensure the file is valid {expected_format} format.",
            recoverable=True,
            context={
                "filepath": filepath,
                "expected_format": expected_format,
                **(context or {}),
            },
        )


class PermissionDeniedError(FileSystemError):
    """Permission denied when accessing a file.

    Use when a file operation fails due to insufficient permissions.
    """

    def __init__(self, filepath: str, context: Optional[Dict] = None) -> None:
        """Initialize PermissionDeniedError.

        Args:
            filepath: Path to the file with permission issues.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Permission denied: {filepath}",
            user_guidance="Check file permissions or run with appropriate access rights.",
            recoverable=False,
            context={"filepath": filepath, **(context or {})},
        )


# =============================================================================
# AI Integration Errors
# =============================================================================


class AIIntegrationError(DnDError):
    """Errors related to AI API calls.

    Base class for all AI-related errors including connection,
    response parsing, and rate limiting issues.
    """


class AIConnectionError(AIIntegrationError):
    """Could not connect to AI service.

    Use when network issues or service unavailability prevent
    connecting to the AI API.
    """

    def __init__(
        self,
        service: str,
        original_error: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize AIConnectionError.

        Args:
            service: Name of the AI service (e.g., "OpenAI", "Anthropic").
            original_error: Optional original error message.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Could not connect to AI service: {service}",
            user_guidance="Check your internet connection and API configuration. "
            "Run 'Test AI Connection' from the Setup menu to diagnose.",
            recoverable=True,
            context={
                "service": service,
                "original_error": original_error,
                **(context or {}),
            },
        )


class AIResponseError(AIIntegrationError):
    """AI returned an unexpected or invalid response.

    Use when the AI service returns a response that cannot be
    processed or is missing expected data.
    """

    def __init__(
        self,
        operation: str,
        details: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize AIResponseError.

        Args:
            operation: The operation that was being performed.
            details: Details about the invalid response.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"AI response error during {operation}",
            user_guidance="Try again with a simpler prompt, or check your AI model "
            "configuration in the Setup menu.",
            recoverable=True,
            context={"operation": operation, "details": details, **(context or {})},
        )


class AIRateLimitError(AIIntegrationError):
    """AI API rate limit exceeded.

    Use when the AI service returns a rate limit error.
    """

    def __init__(
        self,
        service: str,
        retry_after: Optional[int] = None,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize AIRateLimitError.

        Args:
            service: Name of the AI service.
            retry_after: Optional seconds to wait before retrying.
            context: Optional additional context data.
        """
        guidance = "Wait a moment and try again."
        if retry_after:
            guidance = f"Wait {retry_after} seconds and try again."
        super().__init__(
            message=f"Rate limit exceeded for {service}",
            user_guidance=guidance,
            recoverable=True,
            context={"service": service, "retry_after": retry_after, **(context or {})},
        )


class AITimeoutError(AIIntegrationError):
    """AI request timed out.

    Use when an AI request takes too long to complete.
    """

    def __init__(
        self,
        operation: str,
        timeout_seconds: Optional[int] = None,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize AITimeoutError.

        Args:
            operation: The operation that timed out.
            timeout_seconds: Optional timeout duration in seconds.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Operation timed out: {operation}",
            user_guidance="The request took too long. Try again or use a simpler prompt.",
            recoverable=True,
            context={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
                **(context or {}),
            },
        )


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(DnDError):
    """Errors in system configuration.

    Use when required configuration is missing or invalid.
    """

    pass


class MissingConfigError(ConfigurationError):
    """Required configuration is missing.

    Use when a required configuration setting or file is not found.
    """

    def __init__(
        self,
        config_name: str,
        how_to_fix: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize MissingConfigError.

        Args:
            config_name: Name of the missing configuration.
            how_to_fix: Instructions for fixing the issue.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Missing configuration: {config_name}",
            user_guidance=how_to_fix,
            recoverable=True,
            context={"config_name": config_name, **(context or {})},
        )


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid.

    Use when a configuration setting has an invalid value.
    """

    def __init__(
        self,
        config_name: str,
        value: str,
        expected: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize InvalidConfigError.

        Args:
            config_name: Name of the invalid configuration.
            value: The invalid value that was provided.
            expected: Description of expected valid values.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Invalid configuration for {config_name}: '{value}'",
            user_guidance=f"Expected: {expected}",
            recoverable=True,
            context={
                "config_name": config_name,
                "value": value,
                "expected": expected,
                **(context or {}),
            },
        )


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(DnDError):
    """Data validation failures.

    Base class for all validation-related errors.
    """

    pass


class SchemaValidationError(ValidationError):
    """Data does not match expected schema.

    Use when loaded data fails schema validation.
    """

    def __init__(
        self,
        data_type: str,
        errors: List[str],
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize SchemaValidationError.

        Args:
            data_type: Type of data being validated (e.g., "character", "NPC").
            errors: List of validation error messages.
            context: Optional additional context data.
        """
        error_list = "\n  - ".join(errors[:5])
        if len(errors) > 5:
            error_list += f"\n  ... and {len(errors) - 5} more errors"

        super().__init__(
            message=f"Invalid {data_type} data",
            user_guidance=f"Fix the following issues:\n  - {error_list}",
            recoverable=True,
            context={"data_type": data_type, "errors": errors, **(context or {})},
        )


class DataIntegrityError(ValidationError):
    """Data integrity constraint violated.

    Use when data violates referential or business integrity constraints.
    """

    def __init__(
        self,
        data_type: str,
        constraint: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Initialize DataIntegrityError.

        Args:
            data_type: Type of data with integrity issue.
            constraint: Description of the violated constraint.
            context: Optional additional context data.
        """
        super().__init__(
            message=f"Data integrity error for {data_type}",
            user_guidance=f"Constraint violated: {constraint}",
            recoverable=True,
            context={
                "data_type": data_type,
                "constraint": constraint,
                **(context or {}),
            },
        )


# =============================================================================
# Error Handler Utility
# =============================================================================


def handle_errors(
    *error_types: Type[Exception],
    default_return: Any = None,
    log_level: int = logging.ERROR,
) -> Callable:
    """Decorator for consistent error handling.

    Catches specified exceptions and DnDErrors, displays them to the user,
    logs them, and returns a default value.

    Args:
        *error_types: Exception types to catch in addition to DnDError.
        default_return: Value to return on error.
        log_level: Logging level for errors.

    Returns:
        Decorated function that handles errors gracefully.

    Example:
        @handle_errors(FileSystemError, AIIntegrationError)
        def load_character(name: str) -> dict:
            # ... code that might raise errors
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except DnDError as exc:
                LOGGER.log(log_level, "%s: %s", func.__name__, exc.message)
                display_error(exc)
                return default_return
            except error_types as exc:
                LOGGER.log(log_level, "%s: %s", func.__name__, exc)
                display_error(wrap_exception(exc))
                return default_return

        return wrapper

    return decorator


def wrap_exception(
    exc: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> DnDError:
    """Convert standard exceptions to DnDError with context.

    Maps common Python exceptions to appropriate DnDError types
    with user-friendly messages and guidance.

    Args:
        exc: Original exception to wrap.
        context: Additional context about the error.

    Returns:
        DnDError with appropriate message and guidance.

    Example:
        try:
            with open("character.json") as f:
                data = json.load(f)
        except Exception as exc:
            raise wrap_exception(exc, context={"filepath": "character.json"})
    """
    if isinstance(exc, DnDError):
        return exc

    # Map common exceptions to DnDError types
    exception_map: Dict[
        Type[Exception], Callable[[Exception, Optional[Dict]], DnDError]
    ] = {
        builtins.FileNotFoundError: _wrap_file_not_found,
        builtins.PermissionError: _wrap_permission_error,
        json.JSONDecodeError: _wrap_json_error,
        ValueError: _wrap_value_error,
        KeyError: _wrap_key_error,
        builtins.ConnectionError: _wrap_connection_error,
        TimeoutError: _wrap_timeout_error,
    }

    wrapper = exception_map.get(type(exc), _wrap_generic)
    return wrapper(exc, context)


def display_error(error: DnDError) -> None:
    """Display error message to user with appropriate formatting.

    Uses terminal_display utilities for consistent output.

    Args:
        error: The DnDError to display.
    """
    from src.utils.terminal_display import print_error, print_info, print_warning

    print_error(error.message)

    if error.user_guidance:
        print_info(error.user_guidance)

    if not error.recoverable:
        print_warning("This error requires application restart.")


# =============================================================================
# Internal Wrapper Functions
# =============================================================================


def _wrap_file_not_found(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap built-in FileNotFoundError as DnDFileNotFoundError."""
    filename = getattr(exc, "filename", None)
    filepath = str(filename) if filename else "unknown"
    file_type = context.get("file_type", "file") if context else "file"
    return DnDFileNotFoundError(filepath=filepath, file_type=file_type, context=context)


def _wrap_permission_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap built-in PermissionError as PermissionDeniedError."""
    filename = getattr(exc, "filename", None)
    filepath = str(filename) if filename else "unknown"
    return PermissionDeniedError(filepath=filepath, context=context)


def _wrap_json_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap json.JSONDecodeError as FileParseError."""
    filepath = context.get("filepath", "unknown") if context else "unknown"
    return FileParseError(
        filepath=filepath,
        parse_error=str(exc),
        expected_format="JSON",
        context=context,
    )


def _wrap_value_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap ValueError as UserInputError."""
    return UserInputError(
        message=str(exc),
        user_guidance="Check your input and try again.",
        context=context,
    )


def _wrap_key_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap KeyError as MissingDataError."""
    key = str(exc).strip("'\"")
    return MissingDataError(data_name=key, action="this operation")


def _wrap_connection_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap built-in ConnectionError as AIConnectionError."""
    service = context.get("service", "AI service") if context else "AI service"
    return AIConnectionError(service=service, original_error=str(exc), context=context)


def _wrap_timeout_error(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap TimeoutError as AITimeoutError."""
    operation = (
        context.get("operation", "unknown operation")
        if context
        else "unknown operation"
    )
    return AITimeoutError(operation=operation, context=context)


def _wrap_generic(exc: Exception, context: Optional[Dict]) -> DnDError:
    """Wrap unknown exception types as generic DnDError."""
    return DnDError(
        message=f"Unexpected error: {type(exc).__name__}: {exc}",
        user_guidance="If this persists, check the logs or report an issue.",
        recoverable=True,
        context={"original_type": type(exc).__name__, **(context or {})},
    )


# =============================================================================
# Convenience Exports
# =============================================================================

# List of all public exception classes for easy importing
__all__ = [
    # Base
    "DnDError",
    # User Input
    "UserInputError",
    "InvalidChoiceError",
    "MissingDataError",
    # File System
    "FileSystemError",
    "DnDFileNotFoundError",
    "FileParseError",
    "PermissionDeniedError",
    # AI Integration
    "AIIntegrationError",
    "AIConnectionError",
    "AIResponseError",
    "AIRateLimitError",
    "AITimeoutError",
    # Configuration
    "ConfigurationError",
    "MissingConfigError",
    "InvalidConfigError",
    # Validation
    "ValidationError",
    "SchemaValidationError",
    "DataIntegrityError",
    # Utilities
    "handle_errors",
    "wrap_exception",
    "display_error",
]
