#!/usr/bin/env python3

import argparse
import getpass
import os
import platform
import sys
from pathlib import Path


MINIMUM_PYTHON = (3, 10)


def require_supported_python() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        detected = platform.python_version()
        print(
            f"Fordo requires Python {required} or newer. "
            f"Detected Python {detected}."
        )
        raise SystemExit(1)


require_supported_python()


from checks.system_requirements import check_linux_requirements, print_check_results
from platforms.raspberry_pi import validate_raspberry_pi, print_validation, validation_passed
from platforms.linux import inspect_linux_installation, print_linux_installation_state
from checks.python_requirements_check import compare_requirements, print_comparison
from platforms.debian_packages import (
    detect_package_state,
    print_package_state,
    install_missing_packages,
    dpkg_query_available,
    apt_available,
    package_tools_available,
)
from platforms.linux_distribution import detect_linux_distribution, print_linux_distribution
from platforms.ndi_runtime import (
    inspect_ndi_runtime,
    print_ndi_runtime_state,
    print_ndi_installation_guidance,
)
from platforms.native_preview import inspect_native_build, print_native_build_state, build_native_preview
from platforms.systemd_service import inspect_service, print_service_state, install_service, service_is_active
from platforms.labwc_autostart import inspect_autostart, print_autostart_state, configure_autostart
from platforms.python_environment import venv_is_valid, create_virtual_environment
from platforms.python_requirements import verify_requirements, install_requirements
from platforms.architecture import detect_architecture
from checks.service_health import wait_for_health, print_health_result
from checks.project_structure import inspect_project_structure, print_project_structure


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
    architecture_info = detect_architecture()

    return {
        "operating_system": platform.system(),
        "platform_release": platform.release(),
        "architecture": architecture_info["raw"],
        "architecture_class": architecture_info["normalized"],
        "architecture_bits": architecture_info["bits"],
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
        help="Install Fordo and configure supported system services.",
    )

    return parser.parse_args()


def ensure_appliance_script_executable(project_root: str, dry_run: bool = True) -> bool:
    script = Path(project_root) / "scripts" / "start-appliance.sh"

    if not script.is_file():
        print(f"Appliance startup script was not found: {script}")
        return False

    if script.stat().st_mode & 0o111:
        print("Appliance startup script is already executable.")
        return True

    if dry_run:
        print("DRY RUN - appliance startup script permissions will not be changed.")
        print(f"Planned action: chmod +x {script}")
        return True

    try:
        script.chmod(script.stat().st_mode | 0o111)
    except OSError as exc:
        print(f"Failed to make appliance startup script executable: {exc}")
        return False

    if script.stat().st_mode & 0o111:
        print("Appliance startup script is now executable.")
        return True

    print("Appliance startup script permission update failed.")
    return False


def run_linux_install(environment: dict, distro_info: dict, dry_run: bool = True) -> bool:
    project_root = environment["project_root"]

    project_state = inspect_project_structure(project_root)
    print_project_structure(project_state)

    if not project_state["valid"]:
        print(
            "Installation stopped: Fordo project checkout is incomplete "
            "or missing required files."
        )
        return False

    if distro_info["is_debian_family"]:
        if not package_tools_available():
            print()
            print("Debian package prerequisites are not available.")

            if not dpkg_query_available():
                print(
                    "  - dpkg-query was not found; Fordo cannot "
                    "reliably inspect installed packages."
                )

            if not apt_available():
                print(
                    "  - apt-get was not found; Fordo cannot "
                    "install missing system packages."
                )

            print(
                "Installation stopped: Debian package management "
                "prerequisites are incomplete."
            )
            return False

        package_state = detect_package_state(distro_info)
        print_package_state(package_state)

        if not install_missing_packages(
            package_state,
            dry_run=dry_run,
            distro_info=distro_info,
        ):
            print("Installation stopped: required system packages could not be installed.")
            return False
    else:
        print()
        print("Automatic package installation is not implemented for this Linux distribution.")
        return False

    if not create_virtual_environment(project_root, dry_run=dry_run):
        print("Installation stopped: Python virtual environment setup failed.")
        return False

    if not install_requirements(project_root, dry_run=dry_run):
        print("Installation stopped: Python requirements installation failed.")
        return False

    ndi_state = inspect_ndi_runtime(environment["architecture_class"])
    print_ndi_runtime_state(ndi_state)

    if not ndi_state["runtime_ready"]:
        print_ndi_installation_guidance(
            ndi_state,
            machine_architecture=environment["architecture_class"],
        )
        print("Installation stopped: compatible NDI runtime was not found.")
        return False

    if not build_native_preview(project_root, dry_run=dry_run):
        print("Installation stopped: native NDI preview build failed.")
        return False

    if not install_service(project_root, dry_run=dry_run):
        print("Installation stopped: systemd service installation failed.")
        return False

    if not dry_run:
        if not service_is_active():
            print("Installation stopped: Fordo systemd service is not active.")
            return False

        print("Fordo systemd service is active.")

        health_result = wait_for_health()
        print_health_result(health_result)

        if not health_result["healthy"]:
            print("Installation stopped: Fordo service health check failed.")
            return False

    if not ensure_appliance_script_executable(project_root, dry_run=dry_run):
        print("Installation stopped: appliance startup script is not executable.")
        return False

    desktop_environment = (
        environment.get("desktop_environment") or ""
    ).lower()

    if "labwc" in desktop_environment:
        if not configure_autostart(project_root, dry_run=dry_run):
            print("Installation stopped: labwc autostart configuration failed.")
            return False

    print()
    print(
        "Fordo Linux installation "
        + ("DRY RUN completed successfully." if dry_run else "completed successfully.")
    )
    return True


def main() -> None:
    args = parse_arguments()

    environment = detect_environment()
    print_environment(environment)

    if args.install and environment["operating_system"] != "Linux":
        print()
        print(
            "Installation stopped: production install mode currently "
            "supports Linux only."
        )
        raise SystemExit(1)

    if environment["operating_system"] == "Linux":
        results = check_linux_requirements()
        print_check_results(results)

        distro_info = detect_linux_distribution()
        print_linux_distribution(distro_info)

        if args.dry_run or args.install:
            success = run_linux_install(
                environment,
                distro_info,
                dry_run=not args.install,
            )
            raise SystemExit(0 if success else 1)

        if distro_info["is_debian_family"]:
            if dpkg_query_available():
                package_state = detect_package_state(distro_info)
                print_package_state(package_state)

                if not apt_available():
                    print()
                    print(
                        "WARNING: apt-get was not found. Package state can be "
                        "inspected, but Fordo cannot automatically install "
                        "missing system packages."
                    )
            else:
                print()
                print("Debian Package State")
                print("=" * 55)
                print(
                    "UNAVAILABLE - dpkg-query was not found, so Fordo "
                    "cannot reliably inspect installed packages."
                )
                print("=" * 55)
        else:
            print()
            print("Debian package checks skipped for this Linux distribution.")

        ndi_state = inspect_ndi_runtime(
            environment["architecture_class"]
        )
        print_ndi_runtime_state(ndi_state)

        native_state = inspect_native_build(environment["project_root"])
        print_native_build_state(native_state)

        service_state = inspect_service(environment["project_root"])
        print_service_state(service_state)

        if service_state["service_matches"]:
            health_result = wait_for_health()
            print_health_result(health_result)

        desktop_environment = (
            environment.get("desktop_environment") or ""
        ).lower()

        if "labwc" in desktop_environment:
            autostart_state = inspect_autostart(environment["project_root"])
            print_autostart_state(autostart_state)

        else:
            print()
            print("labwc autostart configuration skipped for this desktop environment.")

        linux_state = inspect_linux_installation(environment["project_root"])
        print_linux_installation_state(linux_state)

        if linux_state["virtual_environment"] and linux_state["requirements_file"]:
            requirements_result = compare_requirements(environment["project_root"])
            print_comparison(requirements_result)

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
