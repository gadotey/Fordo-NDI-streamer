#!/usr/bin/env python3

from pathlib import Path

from platforms.debian_packages import apt_available


def virtual_environment_exists(project_root: str) -> bool:
    venv = Path(project_root) / ".venv"

    return (
        venv.is_dir()
        and (venv / "bin" / "python").exists()
        and (venv / "bin" / "pip").exists()
    )


def requirements_file_exists(project_root: str) -> bool:
    return (Path(project_root) / "requirements.txt").is_file()


def native_preview_source_exists(project_root: str) -> bool:
    return (Path(project_root) / "native" / "ndi_preview.cpp").is_file()


def native_preview_binary_exists(project_root: str) -> bool:
    return (Path(project_root) / "native" / "ndi_preview").is_file()


def inspect_linux_installation(project_root: str) -> dict:
    return {
        "apt_available": apt_available(),
        "virtual_environment": virtual_environment_exists(project_root),
        "requirements_file": requirements_file_exists(project_root),
        "native_preview_source": native_preview_source_exists(project_root),
        "native_preview_binary": native_preview_binary_exists(project_root),
    }


def print_linux_installation_state(results: dict) -> None:
    print()
    print("Linux Installation State")
    print("=" * 40)

    for name, present in results.items():
        status = "PRESENT" if present else "MISSING"
        print(f"{name:25} {status}")

    print("=" * 40)
