"""
NPC JSON Validation Module

Validates NPC profile JSON files to ensure they contain all required fields
and proper data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation
    python npc_validator.py [filepath]
    
    # Programmatic validation
    from npc_validator import validate_npc_json, validate_npc_file
    is_valid, errors = validate_npc_file("game_data/npcs/my_npc.json")
"""

import json
import os
from typing import Dict, Any, List, Tuple


class NPCValidationError(Exception):
    """Custom exception for NPC validation errors."""
    pass


def validate_npc_json(data: Dict[str, Any], filepath: str = "") -> Tuple[bool, List[str]]:
    """
    Validate an NPC profile dictionary against the required schema.
    
    Args:
        data: Dictionary containing NPC profile data
        filepath: Optional filepath for error messages
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Define required fields and their expected types
    required_fields = {
        'name': str,
        'nickname': (str, type(None)),
        'role': str,
        'species': str,
        'lineage': str,
        'personality': str,
        'relationships': dict,
        'key_traits': list,
        'abilities': list,
        'recurring': bool,
        'notes': str,
        'ai_config': dict
    }
    
    # Check for required fields and types
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}")

    # Disallowed characters in name
    disallowed_chars = set("'\"`$%&|<>/\\")
    name = data.get('name', '')
    if any(c in name for c in disallowed_chars):
        errors.append(f"{filepath}: Strange characters are not allowed in NPC name. Please use another name (disallowed: {''.join(disallowed_chars)}). Name: '{name}'")
    
    # Validate ai_config structure if present
    if 'ai_config' in data and isinstance(data['ai_config'], dict):
        ai_config = data['ai_config']
        
        # Check for required ai_config fields
        if 'enabled' not in ai_config:
            errors.append("ai_config missing required field: enabled")
        elif not isinstance(ai_config['enabled'], bool):
            errors.append("ai_config.enabled must be a boolean")
        
        # Validate optional ai_config fields if present
        if 'temperature' in ai_config and not isinstance(ai_config['temperature'], (int, float)):
            errors.append("ai_config.temperature must be a number")
        
        if 'max_tokens' in ai_config and not isinstance(ai_config['max_tokens'], int):
            errors.append("ai_config.max_tokens must be an integer")
        
        if 'system_prompt' in ai_config and not isinstance(ai_config['system_prompt'], str):
            errors.append("ai_config.system_prompt must be a string")
        
        if 'model' in ai_config and not isinstance(ai_config['model'], str):
            errors.append("ai_config.model must be a string")
        
        if 'base_url' in ai_config and not isinstance(ai_config['base_url'], str):
            errors.append("ai_config.base_url must be a string")
        
        if 'api_key' in ai_config and not isinstance(ai_config['api_key'], str):
            errors.append("ai_config.api_key must be a string")
    
    # Validate relationships structure
    if 'relationships' in data and isinstance(data['relationships'], dict):
        for char_name, relationship in data['relationships'].items():
            if not isinstance(relationship, str):
                errors.append(f"Relationship value for '{char_name}' must be a string")
    
    # Validate key_traits is list of strings
    if 'key_traits' in data and isinstance(data['key_traits'], list):
        for trait in data['key_traits']:
            if not isinstance(trait, str):
                errors.append("All key_traits must be strings")
                break
    
    # Validate abilities is list of strings
    if 'abilities' in data and isinstance(data['abilities'], list):
        for ability in data['abilities']:
            if not isinstance(ability, str):
                errors.append("All abilities must be strings")
                break
    
    return (len(errors) == 0, errors)


def validate_npc_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate an NPC JSON file.
    
    Args:
        filepath: Path to the NPC JSON file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if file exists
    if not os.path.exists(filepath):
        return (False, [f"File not found: {filepath}"])
    
    # Try to load and parse JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return (False, [f"Invalid JSON format: {e}"])
    except Exception as e:
        return (False, [f"Error reading file: {e}"])
    
    # Validate the data
    return validate_npc_json(data, filepath)


def print_validation_report(filepath: str, is_valid: bool, errors: List[str]):
    """Print a formatted validation report."""
    if is_valid:
        print(f"✓ {filepath}: Valid")
    else:
        print(f"✗ {filepath}: INVALID")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Validate specific file
        filepath = sys.argv[1]
        is_valid, errors = validate_npc_file(filepath)
        print_validation_report(filepath, is_valid, errors)
        sys.exit(0 if is_valid else 1)
    else:
        # Validate all NPC files
        npcs_dir = os.path.join("game_data", "npcs")
        
        if not os.path.exists(npcs_dir):
            print(f"Error: NPC directory not found: {npcs_dir}")
            sys.exit(1)
        
        all_valid = True
        validated_count = 0
        
        for filename in sorted(os.listdir(npcs_dir)):
            if filename.endswith('.json') and not filename.endswith('.example.json'):
                filepath = os.path.join(npcs_dir, filename)
                is_valid, errors = validate_npc_file(filepath)
                print_validation_report(filepath, is_valid, errors)
                
                if not is_valid:
                    all_valid = False
                validated_count += 1
        
        if validated_count == 0:
            print("No NPC files found to validate")
            sys.exit(1)
        
        sys.exit(0 if all_valid else 1)
