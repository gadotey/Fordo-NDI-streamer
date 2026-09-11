#!/usr/bin/env python3

import shutil
from pathlib import Path


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def file_exists(path: str) -> bool:
    return Path(path).exists()


def check_linux_requirements() -> dict:
    return {
        "python3": command_exists("python3"),
        "pip3": command_exists("pip3"),
        "g++": command_exists("g++"),
        "git": command_exists("git"),
        "curl": command_exists("curl"),
        "chromium": command_exists("chromium"),
        "systemctl": command_exists("systemctl"),
        "libjpeg_header": file_exists("/usr/include/jpeglib.h"),
        "ndi_library": (
            file_exists("/usr/local/lib/libndi.so")
            or file_exists("/usr/local/lib/libndi.so.5")
        ),
        "ndi_header": file_exists("/usr/local/include/Processing.NDI.Lib.h"),
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
