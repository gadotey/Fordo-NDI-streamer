from pathlib import Path


NDI_PREFIX_CANDIDATES = (
    Path("/usr/local"),
    Path("/usr"),
)


def discover_ndi_prefix() -> Path | None:
    """Return the first Linux prefix containing a usable NDI SDK/runtime."""
    for prefix in NDI_PREFIX_CANDIDATES:
        header = prefix / "include" / "Processing.NDI.Lib.h"
        library = prefix / "lib" / "libndi.so"

        if header.is_file() and library.exists():
            return prefix

    return None


def resolve_ndi_paths(prefix: Path | None = None) -> dict:
    """Return the NDI SDK/runtime paths associated with a prefix."""
    if prefix is None:
        prefix = discover_ndi_prefix()

    if prefix is None:
        return {
            "prefix": None,
            "include_dir": None,
            "header": None,
            "cpp_header": None,
            "library_dir": None,
            "library": None,
            "library_major": None,
            "hx_dir": None,
        }

    prefix = Path(prefix).resolve()
    include_dir = prefix / "include"
    library_dir = prefix / "lib"

    return {
        "prefix": prefix,
        "include_dir": include_dir,
        "header": include_dir / "Processing.NDI.Lib.h",
        "cpp_header": include_dir / "Processing.NDI.Lib.cplusplus.h",
        "library_dir": library_dir,
        "library": library_dir / "libndi.so",
        "library_major": library_dir / "libndi.so.5",
        "hx_dir": library_dir / "ndi_hx",
    }


def build_ndi_library_path(prefix: Path | None = None) -> str | None:
    """Return the runtime library search path for the discovered NDI runtime."""
    paths = resolve_ndi_paths(prefix)

    library_dir = paths["library_dir"]
    hx_dir = paths["hx_dir"]

    if library_dir is None:
        return None

    search_paths = []

    if hx_dir is not None and hx_dir.is_dir():
        search_paths.append(str(hx_dir))

    if library_dir.is_dir():
        search_paths.append(str(library_dir))

    return ":".join(search_paths) if search_paths else None


def inspect_library_architecture(library_path: Path | None = None) -> dict:
    result = {
        "bits": None,
        "architecture": None,
        "description": None,
    }

    if library_path is None:
        paths = resolve_ndi_paths()
        library_path = paths["library"]

    if library_path is None or not library_path.exists():
        return result

    try:
        library_path = Path(library_path).resolve()
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


def inspect_ndi_runtime(
    machine_architecture: str | None = None,
    prefix: Path | None = None,
) -> dict:
    paths = resolve_ndi_paths(prefix)

    header = paths["header"]
    cpp_header = paths["cpp_header"]
    library = paths["library"]
    library_major = paths["library_major"]
    hx_dir = paths["hx_dir"]

    library_target = None

    if library is not None and library.exists():
        try:
            library_target = str(library.resolve())
        except OSError:
            library_target = None

    library_arch = inspect_library_architecture(library)

    architecture_compatible = None

    if machine_architecture and library_arch["architecture"]:
        architecture_compatible = (
            machine_architecture == library_arch["architecture"]
        )

    header_present = header is not None and header.is_file()
    cpp_header_present = (
        cpp_header is not None and cpp_header.is_file()
    )
    library_present = library is not None and library.exists()
    library_major_present = (
        library_major is not None and library_major.exists()
    )
    hx_dir_present = hx_dir is not None and hx_dir.is_dir()

    runtime_ready = (
        header_present
        and library_present
        and (
            architecture_compatible is True
            if machine_architecture
            else True
        )
    )

    return {
        "prefix": str(paths["prefix"]) if paths["prefix"] else None,
        "include_dir": (
            str(paths["include_dir"])
            if paths["include_dir"]
            else None
        ),
        "library_dir": (
            str(paths["library_dir"])
            if paths["library_dir"]
            else None
        ),
        "hx_dir": str(hx_dir) if hx_dir else None,
        "hx_dir_present": hx_dir_present,
        "header": header_present,
        "cpp_header": cpp_header_present,
        "library": library_present,
        "library_major": library_major_present,
        "library_target": library_target,
        "library_bits": library_arch["bits"],
        "library_architecture": library_arch["architecture"],
        "library_description": library_arch["description"],
        "architecture_compatible": architecture_compatible,
        "runtime_ready": runtime_ready,
    }



NDI_SDK_DOWNLOAD_URL = "https://ndi.video/for-developers/ndi-sdk/download/"


def ndi_runtime_problem(
    state: dict,
    machine_architecture: str | None = None,
) -> str | None:
    """Return a concise reason why the NDI runtime is not ready."""
    if state["runtime_ready"]:
        return None

    if not state["header"] and not state["library"]:
        return "NDI SDK/runtime was not found."

    if not state["header"]:
        return "NDI development header was not found."

    if not state["library"]:
        return "NDI shared library was not found."

    if state["architecture_compatible"] is False:
        detected = state["library_architecture"] or "unknown"
        expected = machine_architecture or "unknown"
        return (
            "NDI runtime architecture is incompatible "
            f"(detected {detected}, expected {expected})."
        )

    if (
        machine_architecture
        and state["library_architecture"] is None
    ):
        return "NDI runtime architecture could not be determined."

    return "NDI SDK/runtime is incomplete or incompatible."


def print_ndi_installation_guidance(
    state: dict,
    machine_architecture: str | None = None,
) -> None:
    """Print safe guidance when Fordo cannot use the NDI runtime."""
    problem = ndi_runtime_problem(
        state,
        machine_architecture=machine_architecture,
    )

    if problem is None:
        return

    architecture = machine_architecture or "unknown"

    print()
    print("NDI Runtime Requirement")
    print("=" * 60)
    print(f"Status: {problem}")
    print(f"Machine architecture: {architecture}")
    print()
    print(
        "Fordo requires the official NDI SDK/runtime and development "
        "files to receive NDI video."
    )
    print()
    print(
        "Fordo does not bundle or redistribute the NDI SDK/runtime."
    )
    print(
        "Obtain a compatible NDI SDK/runtime from the official "
        "NDI developer download page:"
    )
    print()
    print(f"  {NDI_SDK_DOWNLOAD_URL}")
    print()
    print(
        "After installing NDI for this machine architecture, "
        "rerun:"
    )
    print()
    print("  python3 install/install.py --dry-run")
    print()
    print(
        "Fordo will automatically rediscover and validate the "
        "runtime before continuing."
    )
    print("=" * 60)


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
