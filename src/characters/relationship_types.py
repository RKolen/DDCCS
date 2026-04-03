"""Relationship type definitions for D&D characters."""

from enum import Enum
from typing import Dict


class RelationshipType(Enum):
    """Categories of relationships between characters."""

    # Family relationships
    FAMILY_CLOSE = "family_close"           # Parent, sibling, child
    FAMILY_DISTANT = "family_distant"       # Cousin, in-law
    FAMILY_ESTRANGED = "family_estranged"   # Disowned, exiled

    # Romantic relationships
    ROMANTIC_PARTNER = "romantic_partner"   # Current partner
    ROMANTIC_FORMER = "romantic_former"     # Ex-partner
    ROMANTIC_INTEREST = "romantic_interest" # Crush, attraction

    # Friendship
    FRIEND_CLOSE = "friend_close"           # Best friend
    FRIEND = "friend"                       # Regular friend
    ACQUAINTANCE = "acquaintance"           # Casual contact

    # Professional
    ALLY = "ally"                           # Political/military ally
    COLLEAGUE = "colleague"                 # Work relationship
    MENTOR = "mentor"                       # Teacher/student
    STUDENT = "student"                     # Reverse of mentor

    # Antagonistic
    RIVAL = "rival"                         # Friendly competition
    ENEMY = "enemy"                         # Active hostility
    NEMESIS = "nemesis"                     # Archenemy

    # Social hierarchy
    LORD = "lord"                           # Feudal superior
    VASSAL = "vassal"                       # Feudal subordinate
    EMPLOYER = "employer"                   # Employment
    EMPLOYEE = "employee"                   # Employed by

    # Other
    DEBTOR = "debtor"                       # Owes something
    CREDITOR = "creditor"                   # Owed something
    UNKNOWN = "unknown"                     # Relationship exists but undefined


# Mapping of relationship types to their inverse
RELATIONSHIP_INVERSES: Dict[RelationshipType, RelationshipType] = {
    RelationshipType.MENTOR: RelationshipType.STUDENT,
    RelationshipType.STUDENT: RelationshipType.MENTOR,
    RelationshipType.LORD: RelationshipType.VASSAL,
    RelationshipType.VASSAL: RelationshipType.LORD,
    RelationshipType.EMPLOYER: RelationshipType.EMPLOYEE,
    RelationshipType.EMPLOYEE: RelationshipType.EMPLOYER,
    RelationshipType.DEBTOR: RelationshipType.CREDITOR,
    RelationshipType.CREDITOR: RelationshipType.DEBTOR,
    RelationshipType.FRIEND_CLOSE: RelationshipType.FRIEND_CLOSE,
    RelationshipType.FRIEND: RelationshipType.FRIEND,
    RelationshipType.ALLY: RelationshipType.ALLY,
    RelationshipType.RIVAL: RelationshipType.RIVAL,
    RelationshipType.ENEMY: RelationshipType.ENEMY,
    RelationshipType.NEMESIS: RelationshipType.NEMESIS,
    RelationshipType.ROMANTIC_PARTNER: RelationshipType.ROMANTIC_PARTNER,
}


def get_inverse(relationship_type: RelationshipType) -> RelationshipType:
    """Get the inverse relationship type.

    For asymmetric relationships, returns the corresponding type.
    For symmetric relationships, returns the same type.
    """
    return RELATIONSHIP_INVERSES.get(
        relationship_type,
        RelationshipType.UNKNOWN
    )
