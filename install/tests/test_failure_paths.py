import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checks.project_structure import inspect_project_structure
from checks.service_health import check_health_once
from platforms.architecture import (
    architecture_bits,
    detect_architecture,
    normalize_architecture,
)
from platforms.ndi_runtime import (
    inspect_library_architecture,
    inspect_ndi_runtime,
    resolve_ndi_paths,
)
from platforms.python_environment import venv_is_valid
from platforms.python_requirements import requirements_file
from platforms.systemd_service import systemctl_available


class TestArchitectureFailurePaths(unittest.TestCase):

    def test_arm64_normalization(self):
        self.assertEqual(normalize_architecture("aarch64"), "arm64")
        self.assertEqual(architecture_bits("arm64"), 64)

    def test_arm32_normalization(self):
        self.assertEqual(normalize_architecture("armv7l"), "arm32")
        self.assertEqual(architecture_bits("arm32"), 32)

    def test_unsupported_architecture_does_not_become_arm(self):
        result = normalize_architecture("mips64")
        self.assertNotIn(result, ("arm32", "arm64"))


class TestProjectFailurePaths(unittest.TestCase):

    def test_empty_project_directory_is_not_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            state = inspect_project_structure(temp)

            # At least one required project component must fail.
            bool_values = [
                value
                for value in state.values()
                if isinstance(value, bool)
            ]

            self.assertTrue(bool_values)
            self.assertFalse(all(bool_values))


class TestPythonEnvironmentFailurePaths(unittest.TestCase):

    def test_missing_virtual_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(venv_is_valid(temp))

    def test_requirements_path_resolves_inside_project(self):
        with tempfile.TemporaryDirectory() as temp:
            expected = Path(temp) / "requirements.txt"
            self.assertEqual(requirements_file(temp), expected)
            self.assertFalse(expected.exists())


class TestNDIFailurePaths(unittest.TestCase):

    def test_missing_ndi_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp)

            paths = resolve_ndi_paths(prefix=prefix)
            state = inspect_ndi_runtime(
                machine_architecture="aarch64",
                prefix=prefix,
            )

            self.assertFalse(paths["header"].exists())
            self.assertFalse(paths["library"].exists())
            self.assertFalse(state["runtime_ready"])

    def test_non_elf_file_is_not_valid_ndi_library(self):
        with tempfile.TemporaryDirectory() as temp:
            fake_library = Path(temp) / "libndi.so"
            fake_library.write_text("not an ELF shared library")

            state = inspect_library_architecture(fake_library)

            # A text file must never be identified as a valid ARM NDI library.
            self.assertNotEqual(state.get("architecture"), "arm64")
            self.assertNotEqual(state.get("architecture"), "arm32")


class TestSystemFailurePaths(unittest.TestCase):

    def test_missing_systemctl(self):
        with patch("platforms.systemd_service.shutil.which", return_value=None):
            self.assertFalse(systemctl_available())

    def test_unreachable_health_endpoint(self):
        result = check_health_once(
            url="http://127.0.0.1:1/api/health",
            timeout=0.2,
        )

        self.assertFalse(result["reachable"])
        self.assertFalse(result["healthy"])


class TestInstallerProductionMode(unittest.TestCase):

    def test_install_mode_is_exposed_in_help(self):
        command = [
            sys.executable,
            "install/install.py",
            "--help",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        combined = result.stdout + result.stderr

        self.assertEqual(result.returncode, 0)
        self.assertIn("--install", combined)
        self.assertIn(
            "Install Fordo and configure supported system services.",
            combined,
        )
        self.assertNotIn(
            "INSTALL MODE IS NOT ENABLED YET",
            combined,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
