#!/usr/bin/env python3

import platform


ARCHITECTURE_ALIASES = {
    "aarch64": "arm64",
    "arm64": "arm64",

    "armv8l": "arm32",
    "armv7l": "arm32",
    "armv7": "arm32",
    "armhf": "arm32",

    "x86_64": "x86_64",
    "amd64": "x86_64",

    "i386": "x86_32",
    "i486": "x86_32",
    "i586": "x86_32",
    "i686": "x86_32",
    "x86": "x86_32",
}


ARCHITECTURE_BITS = {
    "arm64": 64,
    "arm32": 32,
    "x86_64": 64,
    "x86_32": 32,
}


def normalize_architecture(machine: str | None = None) -> str:
    raw = (machine or platform.machine() or "").strip().lower()
    return ARCHITECTURE_ALIASES.get(raw, "unknown")


def architecture_bits(architecture: str) -> int | None:
    return ARCHITECTURE_BITS.get(architecture)


def detect_architecture(machine: str | None = None) -> dict:
    raw = (machine or platform.machine() or "").strip().lower()
    normalized = normalize_architecture(raw)

    return {
        "raw": raw,
        "normalized": normalized,
        "bits": architecture_bits(normalized),
        "is_arm": normalized in {"arm32", "arm64"},
        "is_32_bit": normalized in {"arm32", "x86_32"},
        "is_64_bit": normalized in {"arm64", "x86_64"},
        "known": normalized != "unknown",
    }


def print_architecture(info: dict) -> None:
    print()
    print("CPU Architecture")
    print("=" * 40)
    print(f"Raw Architecture:        {info['raw']}")
    print(f"Normalized Architecture: {info['normalized']}")
    print(f"Architecture Bits:       {info['bits'] or 'UNKNOWN'}")
    print(f"ARM Architecture:        {'YES' if info['is_arm'] else 'NO'}")
    print(f"Known Architecture:      {'YES' if info['known'] else 'NO'}")
    print("=" * 40)


if __name__ == "__main__":
    print_architecture(detect_architecture())
