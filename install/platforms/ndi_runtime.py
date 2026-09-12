from pathlib import Path


NDI_HEADER = Path("/usr/local/include/Processing.NDI.Lib.h")
NDI_CPP_HEADER = Path("/usr/local/include/Processing.NDI.Lib.cplusplus.h")
NDI_LIBRARY = Path("/usr/local/lib/libndi.so")
NDI_LIBRARY_MAJOR = Path("/usr/local/lib/libndi.so.5")


def inspect_library_architecture() -> dict:
    result = {
        "bits": None,
        "architecture": None,
        "description": None,
    }

    if not NDI_LIBRARY.exists():
        return result

    try:
        library_path = NDI_LIBRARY.resolve()
        header = library_path.read_bytes()[:20]
    except OSError:
        return result

    if len(header) < 20 or header[:4] != b"\x7fELF":
        result["description"] = "Not a valid ELF library"
        return result

    elf_class = header[4]
    byte_order = header[5]

    if elf_class == 1:
        result["bits"] = 32
    elif elf_class == 2:
        result["bits"] = 64

    if byte_order == 1:
        endian = "little"
    elif byte_order == 2:
        endian = "big"
    else:
        result["description"] = "Unknown ELF byte order"
        return result

    machine = int.from_bytes(header[18:20], byteorder=endian)

    machine_map = {
        3: "x86_32",
        40: "arm32",
        62: "x86_64",
        183: "arm64",
    }

    result["architecture"] = machine_map.get(machine)
    result["description"] = (
        f"ELF{result['bits'] or '?'} "
        f"machine={machine} "
        f"architecture={result['architecture'] or 'unknown'}"
    )

    return result


def inspect_ndi_runtime(machine_architecture: str | None = None) -> dict:
    library_target = None

    if NDI_LIBRARY.exists():
        try:
            library_target = str(NDI_LIBRARY.resolve())
        except OSError:
            library_target = None

    library_arch = inspect_library_architecture()

    architecture_compatible = None

    if machine_architecture and library_arch["architecture"]:
        architecture_compatible = (
            machine_architecture == library_arch["architecture"]
        )

    runtime_ready = (
        NDI_HEADER.is_file()
        and NDI_LIBRARY.exists()
        and (
            architecture_compatible is True
            if machine_architecture
            else True
        )
    )

    return {
        "header": NDI_HEADER.is_file(),
        "cpp_header": NDI_CPP_HEADER.is_file(),
        "library": NDI_LIBRARY.exists(),
        "library_major": NDI_LIBRARY_MAJOR.exists(),
        "library_target": library_target,
        "library_bits": library_arch["bits"],
        "library_architecture": library_arch["architecture"],
        "library_description": library_arch["description"],
        "architecture_compatible": architecture_compatible,
        "runtime_ready": runtime_ready,
    }


def print_ndi_runtime_state(state: dict) -> None:
    print()
    print("NDI Runtime State")
    print("=" * 60)
    print(f"ndi_header            {'PRESENT' if state['header'] else 'MISSING'}")
    print(f"ndi_cpp_header        {'PRESENT' if state['cpp_header'] else 'MISSING'}")
    print(f"ndi_library           {'PRESENT' if state['library'] else 'MISSING'}")
    print(f"ndi_library_major     {'PRESENT' if state['library_major'] else 'MISSING'}")
    print(f"library_target        {state['library_target'] or '-'}")
    print(f"library_bits          {state['library_bits'] or '-'}")
    print(f"library_architecture  {state['library_architecture'] or '-'}")

    compatible = state["architecture_compatible"]
    if compatible is None:
        compatible_text = "UNKNOWN"
    else:
        compatible_text = "YES" if compatible else "NO"

    print(f"architecture_match    {compatible_text}")
    print(f"runtime_ready         {'YES' if state['runtime_ready'] else 'NO'}")
    print("=" * 60)


if __name__ == "__main__":
    print_ndi_runtime_state(inspect_ndi_runtime())
