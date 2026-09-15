#!/usr/bin/env python3

import os
import shutil


def privilege_prefix() -> list[str] | None:
    """Return the command prefix required for privileged operations.

    Returns:
        [] when already running as root.
        [sudo_path] when sudo is available for a non-root user.
        None when privilege escalation is unavailable.
    """
    if os.geteuid() == 0:
        return []

    sudo = shutil.which("sudo")
    if sudo:
        return [sudo]

    return None


def privileged_command(*command: str) -> list[str] | None:
    """Build a command suitable for a privileged operation."""
    prefix = privilege_prefix()

    if prefix is None:
        return None

    return [*prefix, *command]
