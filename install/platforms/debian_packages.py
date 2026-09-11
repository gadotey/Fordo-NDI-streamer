#!/usr/bin/env python3

import shutil
import subprocess


REQUIRED_PACKAGES = {
    "python3": "python3",
    "pip3": "python3-pip",
    "venv": "python3-venv",
    "g++": "g++",
    "git": "git",
    "curl": "curl",
    "chromium": "chromium",
    "jpeg": "libjpeg62-turbo-dev",
}


def package_is_installed(package: str) -> bool:
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Status}", package],
        capture_output=True,
        text=True,
    )

    return (
        result.returncode == 0
        and "install ok installed" in result.stdout
    )


def detect_package_state() -> dict:
    state = {}

    for component, package in REQUIRED_PACKAGES.items():
        state[component] = {
            "package": package,
            "installed": package_is_installed(package),
        }

    return state


def missing_packages(state: dict) -> list[str]:
    return [
        info["package"]
        for info in state.values()
        if not info["installed"]
    ]


def print_package_state(state: dict) -> None:
    print()
    print("Debian Package State")
    print("=" * 55)

    for component, info in state.items():
        status = "INSTALLED" if info["installed"] else "MISSING"
        print(
            f"{component:12} "
            f"{info['package']:25} "
            f"{status}"
        )

    missing = missing_packages(state)

    print("=" * 55)

    if missing:
        print()
        print("Packages requiring installation:")
        print(" ".join(missing))
    else:
        print()
        print("All required Debian packages are installed.")



def install_missing_packages(state: dict, dry_run: bool = True) -> bool:
    packages = missing_packages(state)

    if not packages:
        print("No Debian package installation required.")
        return True

    command = [
        "sudo",
        "apt-get",
        "install",
        "-y",
        *packages,
    ]

    if dry_run:
        print()
        print("DRY RUN - no packages will be installed.")
        print("Planned command:")
        print(" ".join(command))
        return True

    print()
    print("Installing required Debian packages...")

    try:
        subprocess.run(
            ["sudo", "apt-get", "update"],
            check=True,
        )
        subprocess.run(
            command,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Debian package installation failed: {exc}")
        return False

    remaining = missing_packages(detect_package_state())

    if remaining:
        print("Some required packages are still missing:")
        print(" ".join(remaining))
        return False

    print("Required Debian packages installed successfully.")
    return True


def apt_available() -> bool:
    return shutil.which("apt-get") is not None


if __name__ == "__main__":
    if not apt_available():
        print("apt-get was not found. This module requires Debian/Ubuntu-style package management.")
        raise SystemExit(1)

    package_state = detect_package_state()
    print_package_state(package_state)
