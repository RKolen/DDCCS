"""HTTP client for the local ComfyUI image-generation workflow API.

ComfyUI runs as a host process (like Ollama), never in DDEV, so the sidecar
reaches it directly. This client drives ComfyUI's workflow API: queue a prompt
(a workflow in API-JSON form), poll history until the run finishes, then fetch
the produced image bytes.
"""

import time
from typing import Any, Dict, Optional

import requests


class ComfyUIClient:
    """Minimal client for ComfyUI's HTTP workflow API."""

    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        """Initialize the client.

        Args:
            base_url: The ComfyUI server base URL (e.g. http://localhost:8188).
            timeout: Overall seconds to wait for a generation to complete.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        """Return True when the ComfyUI server responds to a stats probe."""
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def upload_image(self, name: str, data: bytes) -> Optional[str]:
        """Upload an input image, returning the stored filename (for img2img).

        Args:
            name: The filename to store the image under.
            data: The raw image bytes.

        Returns:
            The stored filename ComfyUI reports, or None on failure.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/upload/image",
                files={"image": (name, data, "image/png")},
                data={"overwrite": "true"},
                timeout=30,
            )
            resp.raise_for_status()
            return str(resp.json().get("name", name))
        except (requests.RequestException, ValueError):
            return None

    def generate(self, workflow: Dict[str, Any]) -> Optional[bytes]:
        """Queue a workflow, wait for it, and return the first output image.

        Args:
            workflow: The ComfyUI workflow in API JSON (node-id -> node) form.

        Returns:
            PNG bytes of the first output image, or None on failure/timeout.
        """
        prompt_id = self._queue(workflow)
        if prompt_id is None:
            return None
        image_ref = self._await_image(prompt_id)
        if image_ref is None:
            return None
        return self._view(image_ref)

    def _queue(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Submit a workflow to /prompt, returning the prompt id."""
        try:
            resp = requests.post(
                f"{self.base_url}/prompt", json={"prompt": workflow}, timeout=30
            )
            resp.raise_for_status()
            return str(resp.json()["prompt_id"])
        except (requests.RequestException, KeyError, ValueError):
            return None

    def _await_image(self, prompt_id: str) -> Optional[Dict[str, str]]:
        """Poll /history until the run produces an output image reference."""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            history = self._history(prompt_id)
            if history:
                image = self._first_image(history.get("outputs", {}))
                if image is not None:
                    return image
            time.sleep(1.0)
        return None

    def _history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the history entry for a prompt id, or None if not ready."""
        try:
            resp = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10)
            resp.raise_for_status()
            entry = resp.json().get(prompt_id)
            return entry if isinstance(entry, dict) else None
        except (requests.RequestException, ValueError):
            return None

    @staticmethod
    def _first_image(outputs: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Return the first output image reference from a history outputs map."""
        for node_output in outputs.values():
            if not isinstance(node_output, dict):
                continue
            for image in node_output.get("images", []):
                if isinstance(image, dict) and image.get("type") == "output":
                    return {
                        "filename": str(image.get("filename", "")),
                        "subfolder": str(image.get("subfolder", "")),
                        "type": str(image.get("type", "output")),
                    }
        return None

    def _view(self, image_ref: Dict[str, str]) -> Optional[bytes]:
        """Fetch the image bytes for an output reference via /view."""
        try:
            resp = requests.get(f"{self.base_url}/view", params=image_ref, timeout=30)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException:
            return None
