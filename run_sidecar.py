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

    try:
        uvicorn.run(
            app,
            host=config.sidecar.host,
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
