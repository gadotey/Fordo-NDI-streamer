import ctypes.util
import os
from pathlib import Path


NDI_PREFIX_CANDIDATES = (
    Path("/usr/local"),
    Path("/usr"),
)


def resolve_ndi_runtime() -> dict:
    """Resolve the NDI runtime used by the Fordo application."""

    for prefix in NDI_PREFIX_CANDIDATES:
        library_dir = prefix / "lib"
        library = library_dir / "libndi.so.5"

        if not library.exists():
            library = library_dir / "libndi.so"

        if library.exists():
            hx_dir = library_dir / "ndi_hx"

            return {
                "prefix": prefix,
                "library_dir": library_dir,
                "library": library,
                "hx_dir": hx_dir if hx_dir.is_dir() else None,
            }

    loader_library = ctypes.util.find_library("ndi")

    return {
        "prefix": None,
        "library_dir": None,
        "library": loader_library,
        "hx_dir": None,
    }


def ndi_library_path() -> str | None:
    """Return the NDI runtime search path for child processes."""

    runtime = resolve_ndi_runtime()
    entries = []

    hx_dir = runtime["hx_dir"]
    library_dir = runtime["library_dir"]

    if hx_dir is not None:
        entries.append(str(hx_dir))

    if library_dir is not None:
        entries.append(str(library_dir))

    existing = os.environ.get("LD_LIBRARY_PATH")

    if existing:
        entries.append(existing)

    return os.pathsep.join(entries) if entries else existing


def ndi_library_name() -> str:
    """Return the library path/name suitable for ctypes."""

    runtime = resolve_ndi_runtime()
    library = runtime["library"]

    if library:
        return str(library)

    return "libndi.so.5"
