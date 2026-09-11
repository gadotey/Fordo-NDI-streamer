#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def get_venv_path(project_root: str) -> Path:
    return Path(project_root) / ".venv"


def venv_is_valid(project_root: str) -> bool:
    venv = get_venv_path(project_root)

    if sys.platform == "win32":
        python_bin = venv / "Scripts" / "python.exe"
        pip_bin = venv / "Scripts" / "pip.exe"
    else:
        python_bin = venv / "bin" / "python"
        pip_bin = venv / "bin" / "pip"

    return venv.is_dir() and python_bin.exists() and pip_bin.exists()


def create_virtual_environment(project_root: str, dry_run: bool = False) -> bool:
    if venv_is_valid(project_root):
        print("Python virtual environment already exists. No changes made.")
        return True

    venv = get_venv_path(project_root)
    command = [sys.executable, "-m", "venv", str(venv)]

    if dry_run:
        print("DRY RUN - Python virtual environment will not be created.")
        print("Planned command:")
        print(" ".join(command))
        return True

    print(f"Creating Python virtual environment: {venv}")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to create Python virtual environment: {exc}")
        return False

    if venv_is_valid(project_root):
        print("Python virtual environment created successfully.")
        return True

    print("Virtual environment creation completed, but validation failed.")
    return False
