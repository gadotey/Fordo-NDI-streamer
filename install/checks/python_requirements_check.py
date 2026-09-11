#!/usr/bin/env python3

import re
import subprocess
import sys
from pathlib import Path


PINNED_REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)\s*$")


def get_venv_python(project_root: str) -> Path:
    venv = Path(project_root) / ".venv"

    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"

    return venv / "bin" / "python"


def parse_pinned_requirements(requirements_path: Path) -> dict:
    required = {}

    for raw_line in requirements_path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        match = PINNED_REQUIREMENT.match(line)

        if match:
            package_name = match.group(1).lower().replace("_", "-")
            required[package_name] = match.group(2)

    return required


def get_installed_packages(python_bin: Path) -> dict:
    result = subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "list",
            "--format=freeze",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    installed = {}

    for line in result.stdout.splitlines():
        if "==" not in line:
            continue

        name, version = line.split("==", 1)
        installed[name.lower().replace("_", "-")] = version

    return installed


def compare_requirements(project_root: str) -> dict:
    root = Path(project_root)
    requirements_path = root / "requirements.txt"
    python_bin = get_venv_python(project_root)

    if not requirements_path.exists():
        raise FileNotFoundError("requirements.txt was not found.")

    if not python_bin.exists():
        raise FileNotFoundError("Virtual environment Python was not found.")

    required = parse_pinned_requirements(requirements_path)
    installed = get_installed_packages(python_bin)

    missing = {}
    mismatched = {}

    for package, required_version in required.items():
        installed_version = installed.get(package)

        if installed_version is None:
            missing[package] = required_version
        elif installed_version != required_version:
            mismatched[package] = {
                "required": required_version,
                "installed": installed_version,
            }

    return {
        "required_count": len(required),
        "missing": missing,
        "mismatched": mismatched,
        "satisfied": not missing and not mismatched,
    }


def print_comparison(result: dict) -> None:
    print()
    print("Python Requirements Comparison")
    print("=" * 40)
    print(f"Pinned requirements checked: {result['required_count']}")

    if result["missing"]:
        print()
        print("Missing packages:")
        for package, version in result["missing"].items():
            print(f"  {package}=={version}")

    if result["mismatched"]:
        print()
        print("Version mismatches:")
        for package, versions in result["mismatched"].items():
            print(
                f"  {package}: required {versions['required']}, "
                f"installed {versions['installed']}"
            )

    print()
    print(
        "Requirements status:",
        "SATISFIED" if result["satisfied"] else "ACTION REQUIRED",
    )
    print("=" * 40)


if __name__ == "__main__":
    result = compare_requirements(".")
    print_comparison(result)
