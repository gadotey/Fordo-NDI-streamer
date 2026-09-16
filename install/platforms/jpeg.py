from pathlib import Path


JPEG_HEADER_CANDIDATES = (
    Path("/usr/include/jpeglib.h"),
    Path("/usr/local/include/jpeglib.h"),
)


def find_jpeg_header() -> Path | None:
    """Return the first available JPEG development header."""
    for candidate in JPEG_HEADER_CANDIDATES:
        if candidate.is_file():
            return candidate

    return None
