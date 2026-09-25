"""Unit tests for src.ai.comfyui_admin.

No ComfyUI and no process control: the subprocess call is mocked, so these
assert what the module decides, not what a restart does.
"""

import subprocess
from unittest.mock import MagicMock, patch

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

admin = import_module("src.ai.comfyui_admin")
config_types = import_module("src.config.config_types")
ComfyUIConfig = config_types.ComfyUIConfig
ComfyUIEndpoint = config_types.ComfyUIEndpoint
ComfyUILocal = config_types.ComfyUILocal

_HOST = "comfy.test"
_PORT = 18188
_DIR = "/opt/comfyui"


def _config(install_dir: str = _DIR, host: str = _HOST,
            port: int = _PORT) -> object:
    """Build a ComfyUI config with a known endpoint and install."""
    return ComfyUIConfig(
        enabled=True,
        endpoint=ComfyUIEndpoint(host=host, port=port),
        local=ComfyUILocal(install_dir=install_dir, extra_args="--lowvram",
                           restart_after_scene=True, restart_timeout=30.0),
    )


def test_remote_comfyui_is_never_restarted() -> None:
    """With no install directory there is nothing this host may stop.

    The safety property of the whole module: a shared or remote ComfyUI has
    no COMFYUI_DIR, so it is never identified and never signalled.
    """
    print("\n[TEST] restart_comfyui - remote instance untouched")
    with patch("src.ai.comfyui_admin.subprocess.run") as run:
        assert admin.can_restart(_config(install_dir="")) is False
        assert admin.restart_comfyui(_config(install_dir="")) is False
    run.assert_not_called()
    print("  [OK] No subprocess, no signal")


def test_restart_needs_a_host_and_port() -> None:
    """A half-configured endpoint cannot be relaunched or health-checked."""
    print("\n[TEST] can_restart - endpoint required")
    assert admin.can_restart(_config(host="")) is False
    assert admin.can_restart(_config(port=0)) is False
    print("  [OK] Missing host or port refuses")


def test_environment_carries_the_launch_settings() -> None:
    """The script reads the same variables start.sh does."""
    print("\n[TEST] restart_environment - variables")
    env = admin.restart_environment(_config())
    assert env["COMFYUI_DIR"] == _DIR
    assert env["COMFYUI_HOST"] == _HOST
    assert env["COMFYUI_PORT"] == str(_PORT)
    assert env["COMFYUI_EXTRA_ARGS"] == "--lowvram"
    assert env["COMFYUI_RESTART_TIMEOUT"] == "30"
    print("  [OK] Directory, endpoint, flags, and timeout passed through")


def test_successful_restart_reports_true() -> None:
    """Exit zero from the script means ComfyUI answered again."""
    print("\n[TEST] restart_comfyui - success")
    done = MagicMock(returncode=0, stdout="ComfyUI is ready", stderr="")
    with patch("src.ai.comfyui_admin.subprocess.run", return_value=done) as run:
        assert admin.restart_comfyui(_config()) is True
    command = run.call_args.args[0]
    assert command[0] == "bash"
    assert command[1].endswith("scripts/restart-comfyui.sh")
    print("  [OK] Script run, True returned")


def test_failed_restart_reports_false_without_raising() -> None:
    """A restart that fails must not turn a finished render into an error.

    The render is already done by the time this runs; the worst honest
    outcome is that the next one finds ComfyUI unreachable and gets a 503
    from the readiness guard.
    """
    print("\n[TEST] restart_comfyui - failure is not an exception")
    done = MagicMock(returncode=1, stdout="", stderr="did not answer")
    with patch("src.ai.comfyui_admin.subprocess.run", return_value=done):
        assert admin.restart_comfyui(_config()) is False
    with patch("src.ai.comfyui_admin.subprocess.run",
               side_effect=OSError("no bash")):
        assert admin.restart_comfyui(_config()) is False
    with patch("src.ai.comfyui_admin.subprocess.run",
               side_effect=subprocess.TimeoutExpired("bash", 1)):
        assert admin.restart_comfyui(_config()) is False
    print("  [OK] Non-zero, OSError and timeout all return False")


def test_timeout_outlasts_the_scripts_own_wait() -> None:
    """The subprocess timeout must not fire before the script gives up.

    Killing the script mid-wait would leave ComfyUI starting and this
    function reporting failure, which is the one genuinely confusing state.
    """
    print("\n[TEST] restart_comfyui - timeout headroom")
    done = MagicMock(returncode=0, stdout="", stderr="")
    with patch("src.ai.comfyui_admin.subprocess.run", return_value=done) as run:
        admin.restart_comfyui(_config())
    assert run.call_args.kwargs["timeout"] > 30.0
    print("  [OK] Outer timeout exceeds the script's readiness wait")


def run_all_tests() -> None:
    """Run every ComfyUI admin test."""
    test_remote_comfyui_is_never_restarted()
    test_restart_needs_a_host_and_port()
    test_environment_carries_the_launch_settings()
    test_successful_restart_reports_true()
    test_failed_restart_reports_false_without_raising()
    test_timeout_outlasts_the_scripts_own_wait()
    print("\n[PASS] All ComfyUI admin tests passed.")


if __name__ == "__main__":
    run_all_tests()
