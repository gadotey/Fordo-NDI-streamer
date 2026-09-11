#!/usr/bin/env python3

import shutil
import subprocess
from pathlib import Path


def get_paths(project_root: str) -> dict:
    root = Path(project_root)

    return {
        "source": root / "native" / "ndi_preview.cpp",
        "binary": root / "native" / "ndi_preview",
        "ndi_header": Path("/usr/local/include/Processing.NDI.Lib.h"),
        "ndi_library": Path("/usr/local/lib/libndi.so"),
        "jpeg_header": Path("/usr/include/jpeglib.h"),
    }


def inspect_native_build(project_root: str) -> dict:
    paths = get_paths(project_root)

    return {
        "compiler": shutil.which("g++") is not None,
        "source": paths["source"].is_file(),
        "ndi_header": paths["ndi_header"].is_file(),
        "ndi_library": paths["ndi_library"].exists(),
        "jpeg_header": paths["jpeg_header"].is_file(),
        "binary": paths["binary"].is_file(),
    }


def build_command(project_root: str) -> list[str]:
    paths = get_paths(project_root)

    return [
        "g++",
        "-O2",
        "-std=c++17",
        str(paths["source"]),
        "-I/usr/local/include",
        "-L/usr/local/lib",
        "-lndi",
        "-ljpeg",
        "-Wl,-rpath,/usr/local/lib",
        "-o",
        str(paths["binary"]),
    ]


def print_native_build_state(state: dict) -> None:
    print()
    print("Native NDI Preview Build State")
    print("=" * 45)

    for name, present in state.items():
        status = "PRESENT" if present else "MISSING"
        print(f"{name:20} {status}")

    print("=" * 45)


def build_native_preview(project_root: str, dry_run: bool = True) -> bool:
    state = inspect_native_build(project_root)

    required = [
        "compiler",
        "source",
        "ndi_header",
        "ndi_library",
        "jpeg_header",
    ]

    missing = [item for item in required if not state[item]]

    if missing:
        print("Native preview cannot be built. Missing:")
        for item in missing:
            print(f"  - {item}")
        return False

    if state["binary"]:
        print("Native preview binary already exists. No build required.")
        return True

    command = build_command(project_root)

    if dry_run:
        print("DRY RUN - native preview will not be compiled.")
        print("Planned command:")
        print(" ".join(command))
        return True

    print("Compiling native NDI preview...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Native preview compilation failed: {exc}")
        return False

    if get_paths(project_root)["binary"].is_file():
        print("Native NDI preview compiled successfully.")
        return True

    print("Compilation completed, but native preview binary was not found.")
    return False


if __name__ == "__main__":
    state = inspect_native_build(".")
    print_native_build_state(state)
    build_native_preview(".", dry_run=True)
