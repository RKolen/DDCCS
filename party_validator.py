"""
Party Configuration JSON Validation Module

Validates current party JSON files to ensure they contain proper structure
and data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation
    python party_validator.py [filepath]
    
    # Programmatic validation
    from party_validator import validate_party_json, validate_party_file
    is_valid, errors = validate_party_file("game_data/current_party/current_party.json")
"""

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime


class PartyValidationError(Exception):
    """Custom exception for party validation errors."""
    pass


def validate_party_json(data: Dict[str, Any], filepath: str = "", characters_dir: str = None) -> Tuple[bool, List[str]]:
    """
    Validate a party configuration dictionary against the required schema.
    
    Args:
        data: Dictionary containing party configuration data
        filepath: Optional filepath for error messages
        characters_dir: Optional path to characters directory for cross-reference validation
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Define required fields and their expected types
    required_fields = {
        'party_members': list,
        'last_updated': str
    }
    
    # Check for required fields and types
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}")
    
    # Validate party_members is a list of strings
    if 'party_members' in data and isinstance(data['party_members'], list):
        if len(data['party_members']) == 0:
            errors.append("party_members list is empty - party must have at least one member")
        
        for i, member in enumerate(data['party_members']):
            if not isinstance(member, str):
                errors.append(f"party_members[{i}] must be a string, got {type(member).__name__}")
            elif member.strip() == "":
                errors.append(f"party_members[{i}] is an empty string")
        
        # Check for duplicate members
        if len(data['party_members']) != len(set(data['party_members'])):
            errors.append("party_members contains duplicate entries")
        
        # Optional: Cross-reference with character files
        if characters_dir and os.path.exists(characters_dir):
            available_characters = []
            for filename in os.listdir(characters_dir):
                if filename.endswith('.json') and not filename.endswith('.example.json'):
                    char_path = os.path.join(characters_dir, filename)
                    try:
                        with open(char_path, 'r', encoding='utf-8') as f:
                            char_data = json.load(f)
                            if 'name' in char_data:
                                available_characters.append(char_data['name'])
                    except:
                        pass  # Skip files that can't be loaded
            
            if available_characters:
                for member in data['party_members']:
                    if isinstance(member, str) and member not in available_characters:
                        errors.append(f"Party member '{member}' does not match any character file in {characters_dir}")
    
    # Validate last_updated is a valid ISO format timestamp
    if 'last_updated' in data and isinstance(data['last_updated'], str):
        try:
            datetime.fromisoformat(data['last_updated'])
        except ValueError:
            errors.append(f"last_updated must be a valid ISO format timestamp, got: '{data['last_updated']}'")
    
    if errors:
        raise Exception("The names of the party members are incorrect, please check them.\n" + "\n".join(errors))
    return (True, [])


def validate_party_file(filepath: str, characters_dir: str = None) -> Tuple[bool, List[str]]:
    """
    Validate a party configuration JSON file.
    
    Args:
        filepath: Path to the party JSON file
        characters_dir: Optional path to characters directory for cross-reference validation
        
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
    return validate_party_json(data, filepath, characters_dir)


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
        
        # Auto-detect characters directory for cross-reference
        characters_dir = os.path.join("game_data", "characters")
        if not os.path.exists(characters_dir):
            characters_dir = None
        
        is_valid, errors = validate_party_file(filepath, characters_dir)
        print_validation_report(filepath, is_valid, errors)
        sys.exit(0 if is_valid else 1)
    else:
        # Validate current party file
        party_file = os.path.join("game_data", "current_party", "current_party.json")
        
        if not os.path.exists(party_file):
            print(f"Error: Party configuration file not found: {party_file}")
            print("Looking for current_party.json in game_data/current_party/")
            sys.exit(1)
        
        # Get characters directory for cross-reference
        characters_dir = os.path.join("game_data", "characters")
        if not os.path.exists(characters_dir):
            characters_dir = None
        
        is_valid, errors = validate_party_file(party_file, characters_dir)
        print_validation_report(party_file, is_valid, errors)
        
        sys.exit(0 if is_valid else 1)
