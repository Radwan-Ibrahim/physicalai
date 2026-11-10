# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Platform preparation iceoryx2 needs before creating IPC nodes."""

from __future__ import annotations

import sys
from pathlib import Path

# iceoryx2 <= 0.9 hard-codes this Windows shm directory and fails node creation if it is missing (iceoryx2#1868).
_WINDOWS_SHM_DIR = Path("C:/Temp/iceoryx2/shm")


def prepare_iceoryx2() -> None:
    """Create the directories iceoryx2 assumes exist on this platform."""
    if sys.platform == "win32":
        _WINDOWS_SHM_DIR.mkdir(parents=True, exist_ok=True)
