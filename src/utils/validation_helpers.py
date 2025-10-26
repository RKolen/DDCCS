"""
Validation helper functions for common validation patterns.

This module provides reusable functions for:
- Required field validation
- Type checking
- List validation
- Error message formatting
"""

from typing import Any, Dict, List, Tuple, Optional, Type


def validate_required_fields(data: Dict[str, Any],
                            required_fields: List[str]) -> Tuple[bool, List[str]]:
    """Validate that all required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
        elif data[field] is None:
            errors.append(f"Required field '{field}' cannot be None")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Required field '{field}' cannot be empty")

    return len(errors) == 0, errors


def validate_field_type(data: Dict[str, Any],
                       field: str,
                       expected_type: Type,
                       required: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate that a field has the expected type.

    Args:
        data: Dictionary containing the field
        field: Field name to validate
        expected_type: Expected Python type
        required: Whether the field is required (default: True)

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Check if field exists
    if field not in data:
        if required:
            return False, f"Missing required field: '{field}'"
        return True, None

    # Check type
    value = data[field]
    if value is None:
        if required:
            return False, f"Required field '{field}' cannot be None"
        return True, None

    if not isinstance(value, expected_type):
        return False, (
            f"Field '{field}' must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )

    return True, None


def validate_list_field(
        data: Dict[str, Any],
        field: str,
        required: bool = True,
        **constraints) -> Tuple[bool, List[str]]:
    """Validate a list field with optional constraints.

    Args:
        data: Dictionary containing the field
        field: Field name to validate
        required: Whether the field is required (default: True)
        **constraints: Optional validation constraints:
            - item_type: Expected type of list items
            - min_length: Minimum list length
            - max_length: Maximum list length

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []

    # Extract constraints with defaults
    item_type = constraints.get('item_type')
    min_length = constraints.get('min_length')
    max_length = constraints.get('max_length')

    # Check if field exists
    if field not in data:
        if required:
            errors.append(f"Missing required field: '{field}'")
        return len(errors) == 0, errors

    value = data[field]

    # Check if None
    if value is None:
        if required:
            errors.append(f"Required field '{field}' cannot be None")
        return len(errors) == 0, errors

    # Check if list
    if not isinstance(value, list):
        errors.append(
            f"Field '{field}' must be a list, got {type(value).__name__}"
        )
        return False, errors

    # Check length constraints
    if min_length is not None and len(value) < min_length:
        errors.append(
            f"Field '{field}' must have at least {min_length} item(s), "
            f"got {len(value)}"
        )

    if max_length is not None and len(value) > max_length:
        errors.append(
            f"Field '{field}' must have at most {max_length} item(s), "
            f"got {len(value)}"
        )

    # Check item types
    if item_type is not None:
        for i, item in enumerate(value):
            if not isinstance(item, item_type):
                errors.append(
                    f"Field '{field}[{i}]' must be {item_type.__name__}, "
                    f"got {type(item).__name__}"
                )

    return len(errors) == 0, errors


def validate_enum_value(data: Dict[str, Any],
                       field: str,
                       allowed_values: List[Any],
                       required: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate that a field's value is in allowed values.

    Args:
        data: Dictionary containing the field
        field: Field name to validate
        allowed_values: List of allowed values
        required: Whether the field is required (default: True)

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Check if field exists
    if field not in data:
        if required:
            return False, f"Missing required field: '{field}'"
        return True, None

    value = data[field]

    if value is None:
        if required:
            return False, f"Required field '{field}' cannot be None"
        return True, None

    if value not in allowed_values:
        return False, (
            f"Field '{field}' must be one of {allowed_values}, got '{value}'"
        )

    return True, None


def validate_dict_field(data: Dict[str, Any],
                       field: str,
                       required: bool = True,
                       allow_empty: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate that a field is a dictionary.

    Args:
        data: Dictionary containing the field
        field: Field name to validate
        required: Whether the field is required (default: True)
        allow_empty: Whether empty dict is allowed (default: True)

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Check if field exists
    if field not in data:
        return (False, f"Missing required field: '{field}'") if required else (True, None)

    value = data[field]

    # Check if None
    if value is None:
        return (False, f"Required field '{field}' cannot be None") if required else (True, None)

    # Check if dict
    if not isinstance(value, dict):
        return False, f"Field '{field}' must be a dictionary, got {type(value).__name__}"

    # Check if empty (if not allowed)
    if not allow_empty and len(value) == 0:
        return False, f"Field '{field}' cannot be empty"

    return True, None


def format_validation_errors(errors: List[str], data_type: str = "data") -> str:
    """Format validation errors into a readable message.

    Args:
        errors: List of error messages
        data_type: Type description (e.g., "character", "NPC")

    Returns:
        Formatted error message string
    """
    if not errors:
        return ""

    message = f"Validation errors for {data_type}:\n"
    for error in errors:
        message += f"  - {error}\n"

    return message.rstrip()


def collect_errors(validation_results: List[Tuple[bool, Any]]) -> List[str]:
    """Collect errors from multiple validation results.

    Args:
        validation_results: List of (is_valid, error_or_errors) tuples

    Returns:
        Flattened list of all error messages
    """
    all_errors = []

    for is_valid, error_data in validation_results:
        if not is_valid:
            if isinstance(error_data, list):
                all_errors.extend(error_data)
            elif isinstance(error_data, str):
                all_errors.append(error_data)
            elif error_data is not None:
                all_errors.append(str(error_data))

    return all_errors


def get_type_name(expected_type) -> str:
    """Get a human-readable type name string.

    Args:
        expected_type: A type or tuple of types

    Returns:
        String representation of the type(s)
    """
    if isinstance(expected_type, tuple):
        type_parts = []
        for type_option in expected_type:
            if hasattr(type_option, '__name__'):
                type_parts.append(type_option.__name__)
            elif type_option is type(None):
                type_parts.append('None')
            else:
                type_parts.append(str(type_option))
        return " or ".join(type_parts)
    return getattr(expected_type, '__name__', str(expected_type))


def print_validation_report(filepath: str, is_valid: bool, errors: List[str]) -> None:
    """Print a formatted validation report.

    Args:
        filepath: Path to the file that was validated
        is_valid: Whether the file passed validation
        errors: List of validation error messages
    """
    if is_valid:
        print(f"[OK] {filepath}: Valid")
    else:
        print(f"[INVALID] {filepath}: INVALID")
        for error in errors:
            print(f"  - {error}")
