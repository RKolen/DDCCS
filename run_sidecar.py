"""Start the D&D search query parser sidecar server."""

import uvicorn

from src.config.config_loader import load_config
from src.sidecar.app import app


def main() -> None:
    """Load config and start the uvicorn server."""
    config = load_config()
    uvicorn.run(
        app,
        host=config.sidecar.host,
        port=config.sidecar.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
