"""Minimal Drupal GraphQL read client.

Reads published content (taxonomy terms, nodes) from the Drupal ``graphql_compose``
endpoint. Published content is readable anonymously, so no credentials are
required for queries. Writes go through the dedicated mutation data producers,
not this helper.

The project standardises on GraphQL for all Drupal access; JSON:API is not used.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union

import requests

from src.config.config_loader import load_config

logger = logging.getLogger(__name__)

_TIMEOUT = 10


def graphql_endpoint() -> Optional[str]:
    """Return the Drupal GraphQL endpoint URL, or None when unconfigured.

    Returns:
        ``<DRUPAL_BASE_URL>/graphql`` when a base URL is configured, else None.
    """
    base_url = load_config().drupal.base_url.rstrip("/")
    return f"{base_url}/graphql" if base_url else None


def query_drupal(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run a GraphQL query against Drupal and return its ``data`` object.

    Degrades gracefully: returns an empty dict when the endpoint is unconfigured,
    unreachable, or the response contains errors, so callers can fall back.

    Args:
        query: The GraphQL query string.
        variables: Optional query variables.

    Returns:
        The ``data`` object from the response, or an empty dict on any failure.
    """
    endpoint = graphql_endpoint()
    if endpoint is None:
        return {}
    drupal = load_config().drupal
    verify: Union[bool, str] = drupal.ca_bundle if drupal.ca_bundle else True
    headers = {"Content-Type": "application/json"}
    if drupal.graphql_token:
        headers["Authorization"] = f"Bearer {drupal.graphql_token}"
    try:
        response = requests.post(
            endpoint,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=_TIMEOUT,
            verify=verify,
        )
        response.raise_for_status()
        payload = response.json()
    except (OSError, ValueError) as exc:
        logger.debug("Drupal GraphQL query failed: %s", exc)
        return {}
    if payload.get("errors"):
        logger.debug("Drupal GraphQL returned errors: %s", payload["errors"])
    data = payload.get("data")
    return data if isinstance(data, dict) else {}
