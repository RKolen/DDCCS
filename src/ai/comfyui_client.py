"""HTTP client for the local ComfyUI image-generation workflow API.

ComfyUI runs as a host process (like Ollama), never in DDEV, so the sidecar
reaches it directly. This client drives ComfyUI's workflow API: queue a prompt
(a workflow in API-JSON form), poll history until the run finishes, then fetch
the produced image bytes.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """Minimal client for ComfyUI's HTTP workflow API."""

    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        """Initialize the client.

        Args:
            base_url: The ComfyUI server base URL - scheme, host, and port, from
                COMFYUI_BASE_URL or COMFYUI_HOST/COMFYUI_PORT.
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

    def free(self) -> bool:
        """Ask ComfyUI to unload models and free memory (POST /free).

        Called between the vision step and generation (and after generation) so
        the vision model and the SD checkpoint are never resident at once - the
        top OOM risk on this CPU-only, 32 GB box.

        Returns:
            True if ComfyUI accepted the free request, False otherwise.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/free",
                json={"unload_models": True, "free_memory": True},
                timeout=30,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

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

    def generate_then_free(self, workflow: Dict[str, Any]) -> Optional[bytes]:
        """Generate an image, then unload models even if generation failed.

        Args:
            workflow: The ComfyUI workflow in API JSON form.

        Returns:
            PNG bytes of the first output image, or None on failure/timeout.
        """
        try:
            return self.generate(workflow)
        finally:
            self.free()

    def _queue(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Submit a workflow to /prompt, returning the prompt id.

        A rejected workflow never reaches the queue, so it leaves no history
        entry for `_await_image` to report on. ComfyUI names the offending
        node in the response body, and that body is the only account of the
        failure there will be - log it rather than returning a bare None.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/prompt", json={"prompt": workflow}, timeout=30
            )
            if resp.status_code != 200:
                logger.error(
                    "ComfyUI rejected the workflow (HTTP %s): %s",
                    resp.status_code,
                    resp.text.strip()[:500],
                )
                return None
            return str(resp.json()["prompt_id"])
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.error("ComfyUI workflow submission failed: %s", exc)
            return None

    def _await_image(self, prompt_id: str) -> Optional[Dict[str, str]]:
        """Poll /history until the run produces an output image reference.

        A failed run produces no image, so waiting for one means waiting out
        the whole timeout and then reporting nothing but None. ComfyUI says so
        immediately in the history entry's status, and a node that raised - a
        missing model, a face the detector could not find - is worth naming
        rather than reporting as a timeout minutes later.
        """
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            history = self._history(prompt_id)
            if history:
                image = self._first_image(history.get("outputs", {}))
                if image is not None:
                    return image
                if self._failed(history):
                    return None
            time.sleep(1.0)
        logger.warning("ComfyUI prompt %s produced no image before the timeout",
                       prompt_id)
        return None

    @staticmethod
    def _failed(history: Dict[str, Any]) -> bool:
        """Report whether a history entry says the run errored.

        Args:
            history: One /history entry.

        Returns:
            True when ComfyUI marked the run as failed.
        """
        status = history.get("status")
        if not isinstance(status, dict) or status.get("status_str") != "error":
            return False
        for message in status.get("messages", []):
            if not isinstance(message, list) or len(message) != 2:
                continue
            kind, detail = message
            if kind == "execution_error" and isinstance(detail, dict):
                logger.error(
                    "ComfyUI node %s (%s) failed: %s",
                    detail.get("node_id"),
                    detail.get("node_type"),
                    str(detail.get("exception_message", "")).strip(),
                )
                return True
        logger.error("ComfyUI run failed without an execution_error message")
        return True

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
