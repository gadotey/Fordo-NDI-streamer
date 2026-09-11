#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def get_venv_python(project_root: str) -> Path:
    venv = Path(project_root) / ".venv"

    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"

    return venv / "bin" / "python"


def requirements_file(project_root: str) -> Path:
    return Path(project_root) / "requirements.txt"


def verify_requirements(project_root: str) -> bool:
    python_bin = get_venv_python(project_root)
    req_file = requirements_file(project_root)

    if not python_bin.exists():
        print("Virtual environment Python was not found.")
        return False

    if not req_file.exists():
        print("requirements.txt was not found.")
        return False

    result = subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "check",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("Python package dependency check PASSED.")
        return True

    print("Python package dependency check FAILED.")
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

    return False


def install_requirements(project_root: str, dry_run: bool = False) -> bool:
    python_bin = get_venv_python(project_root)
    req_file = requirements_file(project_root)

    if not python_bin.exists():
        print("Virtual environment Python was not found.")
        return False

    if not req_file.exists():
        print("requirements.txt was not found.")
        return False

    command = [
        str(python_bin),
        "-m",
        "pip",
        "install",
        "-r",
        str(req_file),
    ]

    if dry_run:
        print("DRY RUN - Python requirements will not be installed.")
        print("Planned command:")
        print(" ".join(command))
        return True

    print("Installing Python requirements...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Python requirements installation failed: {exc}")
        return False

    return verify_requirements(project_root)


if __name__ == "__main__":
    verify_requirements(".")
