#!/usr/bin/env python3

import shutil
import subprocess
from pathlib import Path

from platforms.ndi_runtime import resolve_ndi_paths


def get_paths(
    project_root: str,
    ndi_prefix: Path | None = None,
) -> dict:
    root = Path(project_root)
    ndi_paths = resolve_ndi_paths(ndi_prefix)

    return {
        "source": root / "native" / "ndi_preview.cpp",
        "binary": root / "native" / "ndi_preview",
        "ndi_header": ndi_paths["header"],
        "ndi_library": ndi_paths["library"],
        "ndi_include_dir": ndi_paths["include_dir"],
        "ndi_library_dir": ndi_paths["library_dir"],
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


def build_command(
    project_root: str,
    output_path: str | None = None,
    ndi_prefix: Path | None = None,
) -> list[str]:
    paths = get_paths(project_root, ndi_prefix=ndi_prefix)
    target = Path(output_path) if output_path else paths["binary"]

    if paths["ndi_include_dir"] is None or paths["ndi_library_dir"] is None:
        raise RuntimeError("NDI SDK/runtime paths could not be resolved.")

    include_dir = str(paths["ndi_include_dir"])
    library_dir = str(paths["ndi_library_dir"])

    return [
        "g++",
        "-O2",
        "-std=c++17",
        str(paths["source"]),
        f"-I{include_dir}",
        f"-L{library_dir}",
        "-lndi",
        "-ljpeg",
        f"-Wl,-rpath,{library_dir}",
        "-o",
        str(target),
    ]


def print_native_build_state(state: dict) -> None:
    print()
    print("Native NDI Preview Build State")
    print("=" * 45)

    for name, present in state.items():
        status = "PRESENT" if present else "MISSING"
        print(f"{name:20} {status}")

    print("=" * 45)


def build_native_preview(
    project_root: str,
    dry_run: bool = True,
    output_path: str | None = None,
) -> bool:
    state = inspect_native_build(project_root)
    target = (
        Path(output_path)
        if output_path
        else get_paths(project_root)["binary"]
    )

    always_required = [
        "source",
        "ndi_header",
        "ndi_library",
    ]

    missing = [item for item in always_required if not state[item]]

    if missing:
        print("Native preview cannot be built. Missing:")
        for item in missing:
            print(f"  - {item}")
        return False

    package_managed = [
        "compiler",
        "jpeg_header",
    ]

    missing_packages = [
        item for item in package_managed if not state[item]
    ]

    if missing_packages and not dry_run:
        print("Native preview cannot be built. Missing:")
        for item in missing_packages:
            print(f"  - {item}")
        return False

    if missing_packages and dry_run:
        print(
            "DRY RUN - build prerequisites expected from the "
            "system package installation stage:"
        )
        for item in missing_packages:
            print(f"  - {item}")

    if target.is_file():
        print(f"Native preview binary already exists: {target}")
        print("No build required.")
        return True

    command = build_command(project_root, output_path=output_path)

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

    if target.is_file():
        print(f"Native NDI preview compiled successfully: {target}")
        return True

    print(f"Compilation completed, but binary was not found: {target}")
    return False


if __name__ == "__main__":
    state = inspect_native_build(".")
    print_native_build_state(state)
    build_native_preview(".", dry_run=True)
