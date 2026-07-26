"""Start the D&D search query parser sidecar server."""

import os
import sys

import uvicorn

from src.config.config_loader import load_config
from src.sidecar.app import app


def main() -> None:
    """Load config and start the uvicorn server."""
    config = load_config()
    workers = int(os.getenv("SIDECAR_WORKERS", "1"))
    # The interface to listen on, which is not always the address clients dial:
    # binding every interface is what lets the DDEV web container reach the
    # sidecar over its host gateway for queued AI jobs, while host clients keep
    # using SIDECAR_HOST. A launch knob, like SIDECAR_WORKERS above.
    bind_host = os.getenv("SIDECAR_BIND_HOST", "") or config.sidecar.host

    # No address is guessed: an unset host or port is a configuration error, and
    # binding a default would silently serve somewhere nobody is dialling.
    if not bind_host or not config.sidecar.port:
        print(
            "[ERROR] SIDECAR_HOST and SIDECAR_PORT must be set (see .env.example).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        uvicorn.run(
            app,
            host=bind_host,
            port=config.sidecar.port,
            log_level=config.sidecar.log_level,
            reload=config.sidecar.reload,
            workers=workers,
        )
    except OSError as exc:
        print(f"[ERROR] Failed to start sidecar server: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
