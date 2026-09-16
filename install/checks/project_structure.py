#!/usr/bin/env python3

from pathlib import Path


REQUIRED_FILES = (
    "requirements.txt",
    "app/main.py",
    "app/ndi_discovery.py",
    "native/ndi_preview.cpp",
    "scripts/start-appliance.sh",
)

REQUIRED_DIRECTORIES = (
    "app/static",
)


def inspect_project_structure(project_root: str) -> dict:
    root = Path(project_root).resolve()

    files = {
        relative: (root / relative).is_file()
        for relative in REQUIRED_FILES
    }

    directories = {
        relative: (root / relative).is_dir()
        for relative in REQUIRED_DIRECTORIES
    }

    missing = [
        relative
        for relative, present in {**files, **directories}.items()
        if not present
    ]

    return {
        "project_root": str(root),
        "root_exists": root.is_dir(),
        "files": files,
        "directories": directories,
        "missing": missing,
        "valid": root.is_dir() and not missing,
    }


def print_project_structure(state: dict) -> None:
    print()
    print("Fordo Project Structure")
    print("=" * 60)
    print(
        f"{'project_root':28} "
        f"{'PRESENT' if state['root_exists'] else 'MISSING'}"
    )

    for relative, present in state["files"].items():
        print(
            f"{relative:28} "
            f"{'PRESENT' if present else 'MISSING'}"
        )

    for relative, present in state["directories"].items():
        print(
            f"{relative + '/':28} "
            f"{'PRESENT' if present else 'MISSING'}"
        )

    print("=" * 60)

    if state["valid"]:
        print("Fordo project structure validation PASSED.")
    else:
        print("Fordo project structure validation FAILED.")
        if state["missing"]:
            print("Missing required project items:")
            for item in state["missing"]:
                print(f"  - {item}")
