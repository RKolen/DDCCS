"""
D&D 5e (2024) Class Knowledge Database

Static reference data for all 12 D&D classes including typical behaviors,
key features, and roleplay guidance for character consultants.
"""

from typing import Dict, Any

# Class knowledge database for all 12 D&D 5e (2024) classes
CLASS_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "Barbarian": {
        "primary_ability": "Strength",
        "typical_role": "Tank/Damage",
        "decision_style": "Instinctive and direct",
        "common_reactions": {
            "threat": "Charge headfirst into danger",
            "puzzle": "Try to solve with brute force first",
            "social": "Speak bluntly and honestly",
            "magic": "Distrust or be wary of magic",
        },
        "key_features": ["Rage", "Unarmored Defense", "Reckless Attack"],
        "roleplay_notes": "Often act on emotion, value strength and courage",
    },
    "Bard": {
        "primary_ability": "Charisma",
        "typical_role": "Support/Face",
        "decision_style": "Creative and social",
        "common_reactions": {
            "threat": "Try to talk way out or inspire allies",
            "puzzle": "Use knowledge and creativity",
            "social": "Take the lead in conversations",
            "magic": "Appreciate all forms of magic and art",
        },
        "key_features": [
            "Bardic Inspiration",
            "Spellcasting",
            "Jack of All Trades",
        ],
        "roleplay_notes": "Love stories, music, and being the center of attention",
    },
    "Cleric": {
        "primary_ability": "Wisdom",
        "typical_role": "Healer/Support",
        "decision_style": "Faith-based and protective",
        "common_reactions": {
            "threat": "Protect allies and fight evil",
            "puzzle": "Seek divine guidance or wisdom",
            "social": "Offer comfort and moral guidance",
            "magic": "View divine magic as sacred duty",
        },
        "key_features": ["Spellcasting", "Channel Divinity", "Divine Domain"],
        "roleplay_notes": "Strong moral compass, serve their deity's will",
    },
    "Druid": {
        "primary_ability": "Wisdom",
        "typical_role": "Versatile Caster",
        "decision_style": "Nature-focused and balanced",
        "common_reactions": {
            "threat": "Use nature's power or wild shape",
            "puzzle": "Look for natural solutions",
            "social": "Advocate for nature and balance",
            "magic": "Prefer natural magic over artificial",
        },
        "key_features": ["Spellcasting", "Wild Shape", "Druidcraft"],
        "roleplay_notes": "Protect nature, suspicious of civilization",
    },
    "Fighter": {
        "primary_ability": "Strength or Dexterity",
        "typical_role": "Tank/Damage",
        "decision_style": "Tactical and disciplined",
        "common_reactions": {
            "threat": "Assess tactically and engage strategically",
            "puzzle": "Use experience and practical knowledge",
            "social": "Be direct and honest",
            "magic": "Respect magic but rely on martial skill",
        },
        "key_features": ["Fighting Style", "Action Surge", "Extra Attack"],
        "roleplay_notes": "Disciplined, value training and skill",
    },
    "Monk": {
        "primary_ability": "Dexterity and Wisdom",
        "typical_role": "Mobile Striker",
        "decision_style": "Contemplative and disciplined",
        "common_reactions": {
            "threat": "Use speed and ki abilities",
            "puzzle": "Meditate and seek inner wisdom",
            "social": "Speak thoughtfully and with purpose",
            "magic": "View ki as internal magic",
        },
        "key_features": ["Martial Arts", "Ki", "Unarmored Defense"],
        "roleplay_notes": "Seek self-improvement and inner peace",
    },
    "Paladin": {
        "primary_ability": "Strength and Charisma",
        "typical_role": "Tank/Support",
        "decision_style": "Honor-bound and righteous",
        "common_reactions": {
            "threat": "Stand firm against evil",
            "puzzle": "Apply oath principles",
            "social": "Lead by example and inspire",
            "magic": "Use divine power for righteous cause",
        },
        "key_features": ["Divine Sense", "Lay on Hands", "Sacred Oath"],
        "roleplay_notes": "Follow sacred oath, champion justice",
    },
    "Ranger": {
        "primary_ability": "Dexterity and Wisdom",
        "typical_role": "Scout/Damage",
        "decision_style": "Practical and observant",
        "common_reactions": {
            "threat": "Use terrain and ranged attacks",
            "puzzle": "Apply survival knowledge",
            "social": "Be cautious with strangers",
            "magic": "Use nature magic practically",
        },
        "key_features": ["Favored Enemy", "Natural Explorer", "Spellcasting"],
        "roleplay_notes": "Independent, protect civilization's borders",
    },
    "Rogue": {
        "primary_ability": "Dexterity",
        "typical_role": "Scout/Damage",
        "decision_style": "Opportunistic and careful",
        "common_reactions": {
            "threat": "Look for advantages and weak points",
            "puzzle": "Find creative or sneaky solutions",
            "social": "Read people and situations carefully",
            "magic": "Be wary but appreciate utility",
        },
        "key_features": ["Sneak Attack", "Thieves' Cant", "Cunning Action"],
        "roleplay_notes": "Trust carefully, always have an escape plan",
    },
    "Sorcerer": {
        "primary_ability": "Charisma",
        "typical_role": "Damage/Utility Caster",
        "decision_style": "Intuitive and emotional",
        "common_reactions": {
            "threat": "React with raw magical power",
            "puzzle": "Use innate magical understanding",
            "social": "Let emotions guide interactions",
            "magic": "Magic is part of their being",
        },
        "key_features": ["Spellcasting", "Sorcerous Origin", "Metamagic"],
        "roleplay_notes": "Magic is instinctive, often emotional",
    },
    "Warlock": {
        "primary_ability": "Charisma",
        "typical_role": "Damage/Utility Caster",
        "decision_style": "Driven by pact obligations",
        "common_reactions": {
            "threat": "Use eldritch power strategically",
            "puzzle": "Consult patron knowledge",
            "social": "Pursue personal agenda",
            "magic": "Magic comes with a price",
        },
        "key_features": [
            "Otherworldly Patron",
            "Pact Magic",
            "Eldritch Invocations",
        ],
        "roleplay_notes": "Bound by pact, complex relationship with patron",
    },
    "Wizard": {
        "primary_ability": "Intelligence",
        "typical_role": "Utility/Control Caster",
        "decision_style": "Analytical and methodical",
        "common_reactions": {
            "threat": "Analyze and use appropriate spell",
            "puzzle": "Apply knowledge and research",
            "social": "Use intelligence and reasoning",
            "magic": "Magic is science to be mastered",
        },
        "key_features": ["Spellcasting", "Arcane Recovery", "Spell Mastery"],
        "roleplay_notes": "Knowledge is power, always learning",
    },
}


def get_class_knowledge(class_name: str) -> Dict[str, Any]:
    """
    Get knowledge database for a specific D&D class.

    Args:
        class_name: Name of the D&D class (case-sensitive)

    Returns:
        Dictionary with class knowledge (primary_ability, typical_role, etc.)
        Returns empty dict if class not found
    """
    return CLASS_KNOWLEDGE.get(class_name, {})


def get_all_class_names() -> list[str]:
    """
    Get list of all available D&D class names.

    Returns:
        List of class names
    """
    return list(CLASS_KNOWLEDGE.keys())
