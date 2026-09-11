#!/usr/bin/env python3

import argparse
import getpass
import os
import platform
from pathlib import Path

from checks.system_requirements import check_linux_requirements, print_check_results
from platforms.raspberry_pi import validate_raspberry_pi, print_validation, validation_passed
from platforms.linux import inspect_linux_installation, print_linux_installation_state
from checks.python_requirements_check import compare_requirements, print_comparison
from platforms.debian_packages import detect_package_state, print_package_state, install_missing_packages
from platforms.linux_distribution import detect_linux_distribution, print_linux_distribution
from platforms.ndi_runtime import inspect_ndi_runtime, print_ndi_runtime_state
from platforms.native_preview import inspect_native_build, print_native_build_state, build_native_preview
from platforms.systemd_service import inspect_service, print_service_state, install_service
from platforms.labwc_autostart import inspect_autostart, print_autostart_state, configure_autostart
from platforms.python_environment import venv_is_valid, create_virtual_environment
from platforms.python_requirements import verify_requirements, install_requirements


def is_raspberry_pi() -> bool:
    model_file = Path("/proc/device-tree/model")

    if not model_file.exists():
        return False

    try:
        model = model_file.read_text(errors="ignore").strip("\x00").lower()
        return "raspberry pi" in model
    except OSError:
        return False


def get_raspberry_pi_model() -> str | None:
    model_file = Path("/proc/device-tree/model")

    if not model_file.exists():
        return None

    try:
        return model_file.read_text(errors="ignore").strip("\x00").strip()
    except OSError:
        return None


def detect_environment() -> dict:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    return {
        "operating_system": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "current_user": getpass.getuser(),
        "home_directory": str(Path.home()),
        "project_root": str(project_root),
        "is_raspberry_pi": is_raspberry_pi(),
        "raspberry_pi_model": get_raspberry_pi_model(),
        "desktop_environment": os.environ.get("XDG_CURRENT_DESKTOP"),
        "session_type": os.environ.get("XDG_SESSION_TYPE"),
    }


def print_environment(info: dict) -> None:
    print()
    print("Fordo NDI Streamer Installer")
    print("=" * 40)

    for key, value in info.items():
        label = key.replace("_", " ").title()
        print(f"{label}: {value}")

    print("=" * 40)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fordo NDI Streamer cross-platform installer"
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "--check",
        action="store_true",
        help="Inspect the system without making changes (default).",
    )

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Show installation actions without making changes.",
    )

    mode.add_argument(
        "--install",
        action="store_true",
        help="Perform installation actions when full install mode is enabled.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.install:
        print(
            "INSTALL MODE IS NOT ENABLED YET. "
            "Fordo will not make system changes until all installation stages "
            "have been implemented and verified."
        )
        return

    dry_run = args.dry_run

    environment = detect_environment()
    print_environment(environment)

    if environment["operating_system"] == "Linux":
        results = check_linux_requirements()
        print_check_results(results)

        distro_info = detect_linux_distribution()
        print_linux_distribution(distro_info)

        if distro_info["is_debian_family"]:
            package_state = detect_package_state()
            print_package_state(package_state)

            if dry_run:
                install_missing_packages(package_state, dry_run=True)
        else:
            print()
            print("Debian package checks skipped for this Linux distribution.")

        ndi_state = inspect_ndi_runtime()
        print_ndi_runtime_state(ndi_state)

        native_state = inspect_native_build(environment["project_root"])
        print_native_build_state(native_state)

        if dry_run:
            build_native_preview(environment["project_root"], dry_run=True)

        service_state = inspect_service(environment["project_root"])
        print_service_state(service_state)

        if dry_run:
            install_service(environment["project_root"], dry_run=True)

        autostart_state = inspect_autostart(environment["project_root"])
        print_autostart_state(autostart_state)

        if dry_run:
            configure_autostart(environment["project_root"], dry_run=True)

        linux_state = inspect_linux_installation(environment["project_root"])
        print_linux_installation_state(linux_state)

        if dry_run:
            if venv_is_valid(environment["project_root"]):
                print()
                print("Python virtual environment already exists. No changes required.")
            else:
                print()
                print("DRY RUN - Python virtual environment would be created.")
                print(f"Target: {Path(environment['project_root']) / '.venv'}")

            install_requirements(environment["project_root"], dry_run=True)

        if linux_state["virtual_environment"] and linux_state["requirements_file"]:
            requirements_result = compare_requirements(environment["project_root"])
            print_comparison(requirements_result)

            if not dry_run:
                verify_requirements(environment["project_root"])

        if environment["is_raspberry_pi"]:
            pi_results = validate_raspberry_pi(environment)
            print_validation(pi_results)

            if validation_passed(pi_results):
                print()
                print("Raspberry Pi platform validation PASSED.")
            else:
                print()
                print("Raspberry Pi platform validation FAILED.")


if __name__ == "__main__":
    main()
