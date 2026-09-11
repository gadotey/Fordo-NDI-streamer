from pathlib import Path


NDI_HEADER = Path("/usr/local/include/Processing.NDI.Lib.h")
NDI_CPP_HEADER = Path("/usr/local/include/Processing.NDI.Lib.cplusplus.h")
NDI_LIBRARY = Path("/usr/local/lib/libndi.so")
NDI_LIBRARY_MAJOR = Path("/usr/local/lib/libndi.so.5")


def inspect_ndi_runtime() -> dict:
    library_target = None

    if NDI_LIBRARY.exists():
        try:
            library_target = str(NDI_LIBRARY.resolve())
        except OSError:
            library_target = None

    return {
        "header": NDI_HEADER.is_file(),
        "cpp_header": NDI_CPP_HEADER.is_file(),
        "library": NDI_LIBRARY.exists(),
        "library_major": NDI_LIBRARY_MAJOR.exists(),
        "library_target": library_target,
        "runtime_ready": (
            NDI_HEADER.is_file()
            and NDI_LIBRARY.exists()
        ),
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
    print(f"runtime_ready         {'YES' if state['runtime_ready'] else 'NO'}")
    print("=" * 60)


if __name__ == "__main__":
    print_ndi_runtime_state(inspect_ndi_runtime())
