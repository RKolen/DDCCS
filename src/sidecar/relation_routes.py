"""Arc relationship suggestion routes for the FastAPI sidecar.

Exposes ``/relations/suggest`` (one subject, one model call) and
``/relations/merge`` (collapse the per-subject batches into one set).
"""

import os
from functools import lru_cache
from typing import List, Optional

from fastapi import APIRouter

from src.ai.ai_client import AIClient
from src.relations.relation_suggester import (
    merge_suggestions,
    suggest_relations_for_subject,
)
from src.relations.relation_types import CharacterDigest, RelationSuggestion
from src.sidecar.ai_profiles import build_profile_client
from src.sidecar.models import (
    CharacterDigestModel,
    RelationMergeRequest,
    RelationMergeResponse,
    RelationSuggestionModel,
    RelationSuggestRequest,
    RelationSuggestResponse,
)

router = APIRouter(prefix="/relations", tags=["relations"])


@lru_cache(maxsize=1)
def get_relations_ai_client() -> Optional[AIClient]:
    """Return the AI client used for relationship suggestion.

    Must be an instruct model: a local "thinking" model ignores ``think:false``
    over the OpenAI endpoint and spends the whole budget reasoning, returning
    empty content. Override with ``RELATIONS_PROFILE``.

    Returns:
        A configured AIClient, or None when no profile is usable.
    """
    return build_profile_client(os.getenv("RELATIONS_PROFILE", "creative"))


def _to_digest(model: CharacterDigestModel) -> CharacterDigest:
    """Convert a request digest model into the internal dataclass.

    Args:
        model: A CharacterDigestModel from the request.

    Returns:
        The equivalent CharacterDigest.
    """
    return CharacterDigest.from_dict(model.model_dump())


def _to_suggestion_model(suggestion: RelationSuggestion) -> RelationSuggestionModel:
    """Convert an internal suggestion into its response model.

    Args:
        suggestion: The internal suggestion.

    Returns:
        The response model.
    """
    return RelationSuggestionModel(**suggestion.to_dict())


@router.post("/suggest", response_model=RelationSuggestResponse)
def relations_suggest_endpoint(req: RelationSuggestRequest) -> RelationSuggestResponse:
    """Suggest one subject's relationships in a single model call.

    Args:
        req: The subject, the candidates, the relation side, and arc context.

    Returns:
        Validated suggestions; empty is a valid answer and the failure mode.
    """
    suggestions = suggest_relations_for_subject(
        get_relations_ai_client(),
        _to_digest(req.subject),
        [_to_digest(other) for other in req.others],
        kind=req.kind,
        context=req.context,
    )
    return RelationSuggestResponse(
        subject=req.subject.name,
        relations=[_to_suggestion_model(s) for s in suggestions],
    )


@router.post("/merge", response_model=RelationMergeResponse)
def relations_merge_endpoint(req: RelationMergeRequest) -> RelationMergeResponse:
    """Merge per-subject batches into one deduplicated relationship set.

    Args:
        req: The per-subject suggestion batches.

    Returns:
        One suggestion per character pair.
    """
    batches: List[List[RelationSuggestion]] = []
    for batch in req.batches:
        parsed = (RelationSuggestion.from_dict(item.model_dump()) for item in batch)
        batches.append([s for s in parsed if s is not None])
    merged = merge_suggestions(batches)
    return RelationMergeResponse(relations=[_to_suggestion_model(s) for s in merged])
