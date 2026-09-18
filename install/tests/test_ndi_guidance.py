import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from platforms.ndi_runtime import (
    NDI_SDK_DOWNLOAD_URL,
    discover_downloaded_ndi_sdk,
    inspect_downloaded_ndi_sdk,
    inspect_ndi_runtime,
    install_downloaded_ndi_sdk,
    ndi_runtime_problem,
    print_ndi_installation_guidance,
)


def state(
    *,
    header=False,
    library=False,
    architecture=None,
    compatible=None,
    ready=False,
):
    return {
        "header": header,
        "library": library,
        "library_architecture": architecture,
        "architecture_compatible": compatible,
        "runtime_ready": ready,
    }


def write_fake_elf(path: Path, machine: int, bits: int = 64) -> None:
    """Create the minimum ELF header needed by Fordo's architecture check."""
    header = bytearray(20)
    header[0:4] = b"\x7fELF"
    header[4] = 2 if bits == 64 else 1
    header[5] = 1
    header[18:20] = machine.to_bytes(2, byteorder="little")
    path.write_bytes(header)


def create_fake_sdk(
    home: Path,
    *,
    architecture_dir: str = "aarch64-rpi4-linux-gnueabi",
    machine: int = 183,
    library_name: str = "libndi.so.6.3.2",
) -> Path:
    """Create a minimal extracted NDI SDK layout for tests."""
    sdk_root = home / "Downloads" / "NDI SDK for Linux"
    include_dir = sdk_root / "include"
    library_dir = sdk_root / "lib" / architecture_dir

    include_dir.mkdir(parents=True)
    library_dir.mkdir(parents=True)

    (include_dir / "Processing.NDI.Lib.h").write_text(
        "/* test NDI header */\n",
        encoding="utf-8",
    )
    (include_dir / "Processing.NDI.Lib.cplusplus.h").write_text(
        "/* test NDI C++ header */\n",
        encoding="utf-8",
    )

    library = library_dir / library_name
    write_fake_elf(library, machine=machine)

    major = ".".join(library_name.split(".")[:3])
    (library_dir / major).symlink_to(library_name)

    return sdk_root


class TestNDIRuntimeGuidance(unittest.TestCase):

    def test_missing_runtime_reason(self):
        result = ndi_runtime_problem(
            state(),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI SDK/runtime was not found.",
        )

    def test_missing_header_reason(self):
        result = ndi_runtime_problem(
            state(library=True),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI development header was not found.",
        )

    def test_missing_library_reason(self):
        result = ndi_runtime_problem(
            state(header=True),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI shared library was not found.",
        )

    def test_incompatible_architecture_reason(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture="arm32",
                compatible=False,
            ),
            machine_architecture="arm64",
        )

        self.assertIn("arm32", result)
        self.assertIn("arm64", result)
        self.assertIn("incompatible", result.lower())

    def test_unknown_library_architecture_reason(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture=None,
                compatible=None,
            ),
            machine_architecture="arm64",
        )

        self.assertIn(
            "could not be determined",
            result,
        )

    def test_ready_runtime_has_no_problem(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture="arm64",
                compatible=True,
                ready=True,
            ),
            machine_architecture="arm64",
        )

        self.assertIsNone(result)

    def test_missing_runtime_guidance(self):
        output = io.StringIO()

        with redirect_stdout(output):
            print_ndi_installation_guidance(
                state(),
                machine_architecture="arm64",
            )

        rendered = output.getvalue()

        self.assertIn("NDI Runtime Requirement", rendered)
        self.assertIn("arm64", rendered)
        self.assertIn(NDI_SDK_DOWNLOAD_URL, rendered)
        self.assertIn(
            "python3 install/install.py --dry-run",
            rendered,
        )
        self.assertIn(
            "does not bundle or redistribute",
            rendered,
        )

    def test_ready_runtime_prints_no_guidance(self):
        output = io.StringIO()

        with redirect_stdout(output):
            print_ndi_installation_guidance(
                state(
                    header=True,
                    library=True,
                    architecture="arm64",
                    compatible=True,
                    ready=True,
                ),
                machine_architecture="arm64",
            )

        self.assertEqual(output.getvalue(), "")


class TestNDISDKDiscovery(unittest.TestCase):

    def test_discovers_extracted_sdk_in_downloads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            sdk_root = create_fake_sdk(home)

            result = discover_downloaded_ndi_sdk(home)

            self.assertEqual(result, sdk_root)

    def test_missing_sdk_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = discover_downloaded_ndi_sdk(
                Path(temp_dir)
            )

            self.assertIsNone(result)

    def test_arm64_sdk_selects_real_versioned_library(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            sdk_root = create_fake_sdk(home)

            result = inspect_downloaded_ndi_sdk(
                "arm64",
                sdk_root=sdk_root,
            )

            self.assertTrue(result["found"])
            self.assertTrue(result["header_present"])
            self.assertTrue(result["library_present"])
            self.assertEqual(
                result["library"].name,
                "libndi.so.6.3.2",
            )
            self.assertEqual(
                result["library_architecture"],
                "arm64",
            )
            self.assertTrue(
                result["architecture_compatible"]
            )
            self.assertTrue(result["ready"])

    def test_incompatible_library_architecture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            sdk_root = create_fake_sdk(
                home,
                machine=62,
            )

            result = inspect_downloaded_ndi_sdk(
                "arm64",
                sdk_root=sdk_root,
            )

            self.assertEqual(
                result["library_architecture"],
                "x86_64",
            )
            self.assertFalse(
                result["architecture_compatible"]
            )
            self.assertFalse(result["ready"])

    def test_unsupported_architecture_is_not_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            sdk_root = create_fake_sdk(home)

            result = inspect_downloaded_ndi_sdk(
                "arm32",
                sdk_root=sdk_root,
            )

            self.assertTrue(result["found"])
            self.assertFalse(result["library_present"])
            self.assertFalse(result["ready"])


class TestNDIInstalledRuntime(unittest.TestCase):

    def test_dynamic_major_library_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir)
            include_dir = prefix / "include"
            library_dir = prefix / "lib"

            include_dir.mkdir()
            library_dir.mkdir()

            (include_dir / "Processing.NDI.Lib.h").write_text(
                "/* test */\n",
                encoding="utf-8",
            )

            versioned_library = (
                library_dir / "libndi.so.6.3.2"
            )
            write_fake_elf(
                versioned_library,
                machine=183,
            )

            (library_dir / "libndi.so.6").symlink_to(
                versioned_library.name
            )
            (library_dir / "libndi.so").symlink_to(
                "libndi.so.6"
            )

            result = inspect_ndi_runtime(
                "arm64",
                prefix=prefix,
            )

            self.assertTrue(result["library"])
            self.assertTrue(result["library_major"])
            self.assertEqual(
                result["library_target"],
                str(versioned_library),
            )
            self.assertEqual(
                result["library_architecture"],
                "arm64",
            )
            self.assertTrue(
                result["architecture_compatible"]
            )
            self.assertTrue(result["runtime_ready"])


class TestNDISDKInstallation(unittest.TestCase):

    def test_dry_run_is_non_destructive_and_uses_dynamic_major(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            home = root / "home"
            destination = root / "destination"

            sdk_root = create_fake_sdk(home)

            output = io.StringIO()

            with redirect_stdout(output):
                result = install_downloaded_ndi_sdk(
                    "arm64",
                    sdk_root=sdk_root,
                    dry_run=True,
                    destination_prefix=destination,
                )

            rendered = output.getvalue()

            self.assertTrue(result)
            self.assertIn(
                "DRY RUN - no NDI files will be modified.",
                rendered,
            )
            self.assertIn(
                "libndi.so.6 -> libndi.so.6.3.2",
                rendered,
            )
            self.assertIn(
                "libndi.so -> libndi.so.6",
                rendered,
            )

            self.assertFalse(destination.exists())

    def test_missing_sdk_installation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_sdk = (
                Path(temp_dir) / "missing-sdk"
            )

            output = io.StringIO()

            with redirect_stdout(output):
                result = install_downloaded_ndi_sdk(
                    "arm64",
                    sdk_root=missing_sdk,
                    dry_run=True,
                )

            self.assertFalse(result)
            self.assertIn(
                "compatible extracted NDI SDK was not found",
                output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()