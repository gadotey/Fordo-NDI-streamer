#!/usr/bin/env python3

import shutil
from pathlib import Path

from platforms.ndi_runtime import resolve_ndi_paths


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def file_exists(path: str) -> bool:
    return Path(path).exists()


def supported_browser_exists() -> bool:
    candidates = (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
    )

    return any(command_exists(candidate) for candidate in candidates)


def check_linux_requirements() -> dict:
    ndi_paths = resolve_ndi_paths()

    ndi_library = ndi_paths["library"]
    ndi_library_major = ndi_paths["library_major"]
    ndi_header = ndi_paths["header"]

    return {
        "python3": command_exists("python3"),
        "pip3": command_exists("pip3"),
        "g++": command_exists("g++"),
        "git": command_exists("git"),
        "curl": command_exists("curl"),
        "chromium_browser": supported_browser_exists(),
        "systemctl": command_exists("systemctl"),
        "libjpeg_header": file_exists("/usr/include/jpeglib.h"),
        "ndi_library": (
            (ndi_library is not None and ndi_library.exists())
            or (
                ndi_library_major is not None
                and ndi_library_major.exists()
            )
        ),
        "ndi_header": (
            ndi_header is not None and ndi_header.is_file()
        ),
    }


def print_check_results(results: dict) -> None:
    print()
    print("Fordo System Requirement Check")
    print("=" * 40)

    for name, passed in results.items():
        status = "OK" if passed else "MISSING"
        print(f"{name:20} {status}")

    print("=" * 40)


if __name__ == "__main__":
    results = check_linux_requirements()
    print_check_results(results)
