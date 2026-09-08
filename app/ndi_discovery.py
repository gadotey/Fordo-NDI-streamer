import ctypes
import threading
import time
from dataclasses import dataclass, asdict
from typing import List


class NDISource(ctypes.Structure):
    _fields_ = [
        ("p_ndi_name", ctypes.c_char_p),
        ("p_url_address", ctypes.c_char_p),
    ]


class NDIFindCreate(ctypes.Structure):
    _fields_ = [
        ("show_local_sources", ctypes.c_bool),
        ("p_groups", ctypes.c_char_p),
        ("p_extra_ips", ctypes.c_char_p),
    ]


@dataclass
class SourceInfo:
    name: str
    url: str | None = None


class NDIDiscovery:
    def __init__(self):
        self._sources: List[SourceInfo] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._finder = None
        self._ndi_initialized = False

        self.ndi = ctypes.CDLL("libndi.so.5")

        self.ndi.NDIlib_initialize.argtypes = []
        self.ndi.NDIlib_initialize.restype = ctypes.c_bool

        self.ndi.NDIlib_find_create_v2.argtypes = [
            ctypes.POINTER(NDIFindCreate)
        ]
        self.ndi.NDIlib_find_create_v2.restype = ctypes.c_void_p

        self.ndi.NDIlib_find_wait_for_sources.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        self.ndi.NDIlib_find_wait_for_sources.restype = ctypes.c_bool

        self.ndi.NDIlib_find_get_current_sources.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        self.ndi.NDIlib_find_get_current_sources.restype = ctypes.POINTER(
            NDISource
        )

        self.ndi.NDIlib_find_destroy.argtypes = [ctypes.c_void_p]
        self.ndi.NDIlib_find_destroy.restype = None

        self.ndi.NDIlib_destroy.argtypes = []
        self.ndi.NDIlib_destroy.restype = None

    def start(self):
        if self._running:
            return

        if not self.ndi.NDIlib_initialize():
            raise RuntimeError("NDI runtime failed to initialize.")

        self._ndi_initialized = True

        settings = NDIFindCreate(
            show_local_sources=True,
            p_groups=None,
            p_extra_ips=None,
        )

        self._finder = self.ndi.NDIlib_find_create_v2(
            ctypes.byref(settings)
        )

        if not self._finder:
            self.ndi.NDIlib_destroy()
            self._ndi_initialized = False
            raise RuntimeError("Unable to create NDI finder.")

        self._running = True

        self._thread = threading.Thread(
            target=self._discover_loop,
            daemon=True,
            name="ndi-discovery",
        )

        self._thread.start()

    def stop(self):
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self._thread = None

        if self._finder:
            self.ndi.NDIlib_find_destroy(self._finder)
            self._finder = None

        if self._ndi_initialized:
            self.ndi.NDIlib_destroy()
            self._ndi_initialized = False

    def _discover_loop(self):
        while self._running:
            self.ndi.NDIlib_find_wait_for_sources(
                self._finder,
                1000,
            )

            count = ctypes.c_uint32(0)

            sources_ptr = self.ndi.NDIlib_find_get_current_sources(
                self._finder,
                ctypes.byref(count),
            )

            found: List[SourceInfo] = []

            if sources_ptr:
                for index in range(count.value):
                    item = sources_ptr[index]

                    name = (
                        item.p_ndi_name.decode(
                            "utf-8",
                            errors="replace",
                        )
                        if item.p_ndi_name
                        else "Unknown NDI Source"
                    )

                    url = (
                        item.p_url_address.decode(
                            "utf-8",
                            errors="replace",
                        )
                        if item.p_url_address
                        else None
                    )

                    found.append(
                        SourceInfo(
                            name=name,
                            url=url,
                        )
                    )

            with self._lock:
                self._sources = found

            time.sleep(0.25)

    def get_sources(self):
        with self._lock:
            return [
                asdict(source)
                for source in self._sources
            ]


discovery = NDIDiscovery()
