#!/usr/bin/env python3

from pathlib import Path


SUPPORTED_ARCHITECTURES = {"aarch64", "arm64"}


def validate_raspberry_pi(environment: dict) -> dict:
    architecture = environment.get("architecture")
    model = environment.get("raspberry_pi_model")

    results = {
        "raspberry_pi_detected": environment.get("is_raspberry_pi", False),
        "supported_architecture": architecture in SUPPORTED_ARCHITECTURES,
        "model_detected": bool(model),
        "project_root_exists": Path(
            environment.get("project_root", "")
        ).exists(),
    }

    return results


def print_validation(results: dict) -> None:
    print()
    print("Raspberry Pi Platform Validation")
    print("=" * 40)

    for name, passed in results.items():
        status = "OK" if passed else "FAILED"
        print(f"{name:25} {status}")

    print("=" * 40)


def validation_passed(results: dict) -> bool:
    return all(results.values())
