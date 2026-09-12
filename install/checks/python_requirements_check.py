#!/usr/bin/env python3

import re
import subprocess
import sys
from pathlib import Path


PINNED_REQUIREMENT = re.compile(
    r'^\s*([A-Za-z0-9_.-]+)==([^\s;#]+)'
    r'(?:\s*;\s*sys_platform\s*(!=|==)\s*["\']([^"\']+)["\'])?'
    r'\s*$'
)


def get_venv_python(project_root: str) -> Path:
    venv = Path(project_root) / ".venv"

    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"

    return venv / "bin" / "python"


def normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pinned_requirements(requirements_path: Path) -> dict:
    required = {}

    for raw_line in requirements_path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        match = PINNED_REQUIREMENT.match(line)

        if not match:
            continue

        package_name = normalize_package_name(match.group(1))
        version = match.group(2)
        operator = match.group(3)
        marker_platform = match.group(4)

        if operator and marker_platform:
            if operator == "!=" and sys.platform == marker_platform:
                continue
            if operator == "==" and sys.platform != marker_platform:
                continue

        required[package_name] = version

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
