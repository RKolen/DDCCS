"""Minimal Drupal GraphQL client.

Reads published content (taxonomy terms, nodes) from the Drupal
``graphql_compose`` endpoint. Published content is readable anonymously, so no
credentials are required for queries; writes need a token and go through
:func:`mutate_drupal`.

Every entry point takes an optional ``config``. Callers holding their own
:class:`DrupalConfig` pass it through so the connection they were built with is
the one actually used; omitting it falls back to the loaded configuration.

The project standardises on GraphQL for all Drupal access; JSON:API is disabled
server-side (``jsonapi_extras`` sets ``default_disabled: true``).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union

import requests

from src.config.config_loader import load_config
from src.config.config_types import DrupalConfig

logger = logging.getLogger(__name__)

_TIMEOUT = 10


class DrupalGraphQLError(Exception):
    """Raised when a Drupal GraphQL write fails.

    Reads degrade silently (an unreachable Drupal is a cache miss), but a write
    that quietly does nothing is a data-loss bug, so mutations raise instead.
    """


def _resolve_config(config: Optional[DrupalConfig]) -> DrupalConfig:
    """Return the given Drupal config, falling back to the loaded one.

    Args:
        config: An explicit configuration, or None to use the loaded one.

    Returns:
        The configuration to build the request from.
    """
    return config if config is not None else load_config().drupal


def graphql_endpoint(config: Optional[DrupalConfig] = None) -> Optional[str]:
    """Return the Drupal GraphQL endpoint URL, or None when unconfigured.

    Args:
        config: Drupal configuration. Defaults to the loaded configuration.

    Returns:
        ``<DRUPAL_BASE_URL>/graphql`` when a base URL is configured, else None.
    """
    base_url = _resolve_config(config).base_url.rstrip("/")
    return f"{base_url}/graphql" if base_url else None


def _build_headers(drupal: DrupalConfig) -> Dict[str, str]:
    """Return the request headers for a GraphQL call.

    Args:
        drupal: The Drupal configuration supplying the bearer token.

    Returns:
        Headers, including Authorization when a token is configured.
    """
    headers = {"Content-Type": "application/json"}
    if drupal.graphql_token:
        headers["Authorization"] = f"Bearer {drupal.graphql_token}"
    return headers


def query_drupal(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    config: Optional[DrupalConfig] = None,
) -> Dict[str, Any]:
    """Run a GraphQL query against Drupal and return its ``data`` object.

    Degrades gracefully: returns an empty dict when the endpoint is unconfigured,
    unreachable, or the response contains errors, so callers can fall back.

    Args:
        query: The GraphQL query string.
        variables: Optional query variables.
        config: Drupal configuration. Defaults to the loaded configuration.

    Returns:
        The ``data`` object from the response, or an empty dict on any failure.
    """
    drupal = _resolve_config(config)
    endpoint = graphql_endpoint(drupal)
    if endpoint is None:
        return {}
    verify: Union[bool, str] = drupal.ca_bundle if drupal.ca_bundle else True
    headers = _build_headers(drupal)
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


def _format_errors(errors: Any) -> str:
    """Render a GraphQL ``errors`` payload as a single readable string.

    Args:
        errors: The ``errors`` value from a GraphQL response. Normally a list of
            dicts carrying a ``message``, but tolerated in any shape.

    Returns:
        A semicolon-separated summary of the error messages.
    """
    if not isinstance(errors, list):
        return str(errors)
    return "; ".join(
        str(err.get("message", err)) if isinstance(err, dict) else str(err) for err in errors
    )


def mutate_drupal(
    mutation: str,
    variables: Optional[Dict[str, Any]] = None,
    config: Optional[DrupalConfig] = None,
) -> Dict[str, Any]:
    """Run a GraphQL mutation against Drupal and return its ``data`` object.

    Unlike :func:`query_drupal`, this does not degrade silently: a write that
    fails must be visible to the caller, so every failure raises.

    Args:
        mutation: The GraphQL mutation string.
        variables: Optional mutation variables.
        config: Drupal configuration. Defaults to the loaded configuration.

    Returns:
        The ``data`` object from the response.

    Raises:
        DrupalGraphQLError: When Drupal is unconfigured, unreachable, returns a
            non-2xx status, sends an undecodable body, or reports GraphQL
            errors.
    """
    drupal = _resolve_config(config)
    endpoint = graphql_endpoint(drupal)
    if endpoint is None:
        raise DrupalGraphQLError("DRUPAL_BASE_URL is not configured")
    verify: Union[bool, str] = drupal.ca_bundle if drupal.ca_bundle else True
    headers = _build_headers(drupal)
    try:
        response = requests.post(
            endpoint,
            json={"query": mutation, "variables": variables or {}},
            headers=headers,
            timeout=_TIMEOUT,
            verify=verify,
        )
        response.raise_for_status()
        payload = response.json()
    except (OSError, ValueError) as exc:
        raise DrupalGraphQLError(f"Drupal GraphQL mutation failed: {exc}") from exc

    errors = payload.get("errors")
    if errors:
        raise DrupalGraphQLError(
            f"Drupal GraphQL mutation returned errors: {_format_errors(errors)}"
        )

    data = payload.get("data")
    return data if isinstance(data, dict) else {}
