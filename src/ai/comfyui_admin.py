"""Restart a ComfyUI this host started itself.

ComfyUI does not give system RAM back. ``POST /free`` unloads models from the
GPU, but the process keeps the arena it grew while loading them, so on a small
box the second scene render of a session starts with no room and the kernel
takes the process out mid-render. Restarting between renders is the only thing
that returns the memory, which is why this exists at all.

Nothing here touches a ComfyUI this deployment did not start. "Local" is not
guessed from the address - a loopback URL can still be somebody else's
container - it means ``COMFYUI_DIR`` is set. Knowing where the install is, is
the same thing as being able to relaunch it.

The mechanics live in ``scripts/restart-comfyui.sh``, beside the ``start.sh``
that launches ComfyUI in the first place, so the launch recipe has one home.
That script finds the process by command line and never by what is listening
on a port: a port says nothing about what you are about to stop.
"""

import logging
import os
import pathlib
import subprocess
from typing import Dict

from src.config.config_types import ComfyUIConfig

logger = logging.getLogger(__name__)

RESTART_SCRIPT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts" / "restart-comfyui.sh"
)

# Beyond the script's own readiness wait, which is what the timeout is for.
# Only reached if the script itself wedges.
_OVERHEAD = 60.0


def restart_environment(comfyui: ComfyUIConfig) -> Dict[str, str]:
    """The variables ``restart-comfyui.sh`` reads, over the current ones.

    Args:
        comfyui: Loaded ComfyUI config.

    Returns:
        An environment mapping for the subprocess.
    """
    local = comfyui.local
    env = dict(os.environ)
    env["COMFYUI_DIR"] = local.install_dir
    env["COMFYUI_HOST"] = comfyui.endpoint.host
    env["COMFYUI_PORT"] = str(comfyui.endpoint.port)
    env["COMFYUI_EXTRA_ARGS"] = local.extra_args
    env["COMFYUI_RESTART_TIMEOUT"] = str(int(local.restart_timeout))
    if local.log_file:
        env["COMFYUI_LOG_FILE"] = local.log_file
    return env


def can_restart(comfyui: ComfyUIConfig) -> bool:
    """Whether this deployment is able to restart its own ComfyUI.

    Args:
        comfyui: Loaded ComfyUI config.

    Returns:
        True when an install directory, host and port are all known and the
        script is present.
    """
    return bool(
        comfyui.local.manages_process()
        and comfyui.endpoint.host
        and comfyui.endpoint.port
        and RESTART_SCRIPT.is_file()
    )


def restart_comfyui(comfyui: ComfyUIConfig) -> bool:
    """Restart a locally managed ComfyUI and wait for it to answer.

    A no-op for any ComfyUI this deployment does not start, which is the
    safety property that matters: with no install directory there is nothing
    to identify, nothing to stop, and nothing to relaunch.

    Never raises. A failed restart leaves the next render to the readiness
    guard, which reports an unreachable ComfyUI as a 503 - worse than a slow
    render, but the render that just finished is already returned by then.

    Args:
        comfyui: Loaded ComfyUI config.

    Returns:
        True when ComfyUI is answering again afterwards.
    """
    if not can_restart(comfyui):
        return False
    try:
        done = subprocess.run(
            ["bash", str(RESTART_SCRIPT)],
            env=restart_environment(comfyui),
            capture_output=True, text=True, check=False,
            timeout=comfyui.local.restart_timeout + _OVERHEAD,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("Could not run %s", RESTART_SCRIPT)
        return False
    if done.returncode != 0:
        logger.error("ComfyUI restart failed (%s): %s",
                     done.returncode, done.stderr.strip())
        return False
    logger.info("ComfyUI restarted: %s", done.stdout.strip())
    return True
