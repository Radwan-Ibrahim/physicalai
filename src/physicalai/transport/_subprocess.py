# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Cross-platform helpers for the detached owner/publisher worker subprocesses."""

from __future__ import annotations

import select
import signal
import subprocess  # noqa: S404 # nosec: B404
import sys
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType

if sys.platform == "win32":
    # A new process group detaches the worker from the parent's Ctrl+C and lets stop() target it with CTRL_BREAK.
    DETACHED_POPEN_KWARGS: dict[str, Any] = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
else:
    DETACHED_POPEN_KWARGS = {"start_new_session": True}


def read_stdout_line(proc: subprocess.Popen[bytes], timeout: float) -> str | None:
    """Read one line from a worker's stdout pipe with a timeout.

    Returns:
        The stripped line, or ``None`` on timeout / EOF.
    """
    stdout = proc.stdout
    if stdout is None:
        return None

    if sys.platform == "win32":
        # select() only accepts sockets on Windows; a reader thread provides the timeout instead.
        lines: list[bytes] = []
        reader = threading.Thread(target=lambda: lines.append(stdout.readline()), daemon=True)
        reader.start()
        reader.join(timeout)
        raw = lines[0] if lines else b""
    else:
        readable, _, _ = select.select([stdout], [], [], timeout)
        if not readable:
            return None
        raw = stdout.readline()

    if not raw:
        return None
    return raw.decode().strip()


def request_stop(proc: subprocess.Popen[bytes]) -> None:
    """Ask a worker to shut down gracefully (SIGTERM, or CTRL_BREAK on Windows)."""
    if sys.platform == "win32":
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            # No console shared with the worker: only a hard TerminateProcess is available.
            proc.terminate()
        return
    proc.terminate()


def install_stop_handler(handler: Callable[[int, FrameType | None], None]) -> None:
    """Route every graceful-stop signal :func:`request_stop` may send to *handler*."""
    signal.signal(signal.SIGTERM, handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, handler)
