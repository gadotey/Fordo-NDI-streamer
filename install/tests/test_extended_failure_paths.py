import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import platforms.debian_packages as debian
import platforms.native_preview as native
import platforms.ndi_runtime as ndi
import platforms.labwc_autostart as labwc
from checks.service_health import check_health_once


class TestPackageManagerFailures(unittest.TestCase):

    def test_package_tools_missing_when_dpkg_missing(self):
        def fake_which(command):
            if command == "dpkg-query":
                return None
            if command == "apt-get":
                return "/usr/bin/apt-get"
            return None

        with patch(
            "platforms.debian_packages.shutil.which",
            side_effect=fake_which,
        ):
            self.assertFalse(debian.package_tools_available())

    def test_package_tools_missing_when_apt_missing(self):
        def fake_which(command):
            if command == "dpkg-query":
                return "/usr/bin/dpkg-query"
            if command == "apt-get":
                return None
            return None

        with patch(
            "platforms.debian_packages.shutil.which",
            side_effect=fake_which,
        ):
            self.assertFalse(debian.package_tools_available())

    def test_install_missing_packages_rejects_missing_apt(self):
        state = {
            "curl": {
                "package": "curl",
                "installed": False,
            }
        }

        with patch(
            "platforms.debian_packages.apt_available",
            return_value=False,
        ):
            result = debian.install_missing_packages(
                state,
                dry_run=False,
            )

        self.assertFalse(result)


class TestNativePreviewFailures(unittest.TestCase):

    def test_missing_compiler_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with patch(
                "platforms.native_preview.shutil.which",
                return_value=None,
            ):
                state = native.inspect_native_build(str(root))

            self.assertFalse(state["compiler"])

    def test_missing_jpeg_header_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with patch(
                "platforms.native_preview.find_jpeg_header",
                return_value=None,
            ):
                paths = native.get_paths(str(root))

            self.assertIsNone(paths["jpeg_header"])

    def test_failed_compiler_returns_false(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "ndi_preview"

            ready_state = {
                "compiler": True,
                "source": True,
                "ndi_header": True,
                "ndi_library": True,
                "jpeg_header": True,
                "binary": False,
            }

            with (
                patch(
                    "platforms.native_preview.inspect_native_build",
                    return_value=ready_state,
                ),
                patch(
                    "platforms.native_preview.build_command",
                    return_value=["g++", "simulated.cpp"],
                ),
                patch(
                    "platforms.native_preview.subprocess.run",
                    side_effect=native.subprocess.CalledProcessError(
                        1,
                        ["g++", "simulated.cpp"],
                    ),
                ),
            ):
                result = native.build_native_preview(
                    temp,
                    dry_run=False,
                    output_path=str(target),
                )

            self.assertFalse(result)



class TestNDIArchitectureFailures(unittest.TestCase):

    def test_arm32_runtime_rejected_on_arm64_machine(self):
        fake_state = {
            "bits": 32,
            "architecture": "arm32",
            "description": "ELF32 machine=40 architecture=arm32",
        }

        with patch(
            "platforms.ndi_runtime.inspect_library_architecture",
            return_value=fake_state,
        ):
            with tempfile.TemporaryDirectory() as temp:
                prefix = Path(temp)

                include = prefix / "include"
                lib = prefix / "lib"

                include.mkdir()
                lib.mkdir()

                (include / "Processing.NDI.Lib.h").write_text("fake")
                (include / "Processing.NDI.Lib.cplusplus.h").write_text("fake")
                (lib / "libndi.so").write_bytes(b"fake")
                (lib / "libndi.so.5").write_bytes(b"fake")

                state = ndi.inspect_ndi_runtime(
                    machine_architecture="arm64",
                    prefix=prefix,
                )

        self.assertFalse(state["architecture_compatible"])
        self.assertFalse(state["runtime_ready"])


class TestHealthFailures(unittest.TestCase):

    def test_connection_refused_is_unhealthy(self):
        result = check_health_once(
            "http://127.0.0.1:1/api/health",
            timeout=0.2,
        )

        self.assertFalse(result["reachable"])
        self.assertFalse(result["healthy"])


class TestAutostartFailures(unittest.TestCase):

    def test_missing_autostart_file_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "autostart"

            with patch(
                "platforms.labwc_autostart.get_autostart_path",
                return_value=missing,
            ):
                state = labwc.inspect_autostart(temp)

            self.assertFalse(state["exists"])
            self.assertFalse(state["fordo_present"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
