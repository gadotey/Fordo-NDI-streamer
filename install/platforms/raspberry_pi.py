#!/usr/bin/env python3

from pathlib import Path

from platforms.architecture import normalize_architecture


SUPPORTED_ARCHITECTURES = {"arm64", "arm32"}


def validate_raspberry_pi(environment: dict) -> dict:
    raw_architecture = environment.get("architecture")
    architecture = normalize_architecture(raw_architecture)
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
