import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

INSTALL_DIR = Path(__file__).resolve().parents[1]
if str(INSTALL_DIR) not in sys.path:
    sys.path.insert(0, str(INSTALL_DIR))

import importlib.util

INSTALLER_PATH = INSTALL_DIR / "install.py"
spec = importlib.util.spec_from_file_location(
    "fordo_installer",
    INSTALLER_PATH,
)
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


def make_environment(operating_system="Linux"):
    return {
        "operating_system": operating_system,
        "platform_release": "test",
        "architecture": "aarch64",
        "architecture_class": "arm64",
        "architecture_bits": 64,
        "python_version": "3.13.5",
        "current_user": "test",
        "home_directory": "/tmp",
        "project_root": "/tmp/fordo-test",
        "is_raspberry_pi": True,
        "raspberry_pi_model": "Raspberry Pi 5 Model B",
        "desktop_environment": "labwc",
        "session_type": "wayland",
    }


class TestInstallCli(unittest.TestCase):

    @patch.object(install, "print_linux_distribution")
    @patch.object(install, "detect_linux_distribution")
    @patch.object(install, "print_check_results")
    @patch.object(install, "check_linux_requirements")
    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_install_dispatches_real_linux_install(
        self,
        parse_arguments,
        run_linux_install,
        detect_environment,
        print_environment,
        check_linux_requirements,
        print_check_results,
        detect_linux_distribution,
        print_linux_distribution,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=True,
            repair=False,
            uninstall=False,
            uninstall_dry_run=False,
        )

        environment = make_environment()
        distro_info = {
            "is_debian_family": True,
        }

        detect_environment.return_value = environment
        detect_linux_distribution.return_value = distro_info
        check_linux_requirements.return_value = []
        run_linux_install.return_value = True

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 0)

        run_linux_install.assert_called_once_with(
            environment,
            distro_info,
            dry_run=False,
        )

    @patch.object(install, "print_linux_distribution")
    @patch.object(install, "detect_linux_distribution")
    @patch.object(install, "print_check_results")
    @patch.object(install, "check_linux_requirements")
    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_dry_run_dispatches_non_destructive_linux_install(
        self,
        parse_arguments,
        run_linux_install,
        detect_environment,
        print_environment,
        check_linux_requirements,
        print_check_results,
        detect_linux_distribution,
        print_linux_distribution,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=True,
            install=False,
            repair=False,
            uninstall=False,
            uninstall_dry_run=False,
        )

        environment = make_environment()
        distro_info = {
            "is_debian_family": True,
        }

        detect_environment.return_value = environment
        detect_linux_distribution.return_value = distro_info
        check_linux_requirements.return_value = []
        run_linux_install.return_value = True

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 0)

        run_linux_install.assert_called_once_with(
            environment,
            distro_info,
            dry_run=True,
        )

    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_install_rejects_non_linux_platform(
        self,
        parse_arguments,
        run_linux_install,
        detect_environment,
        print_environment,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=True,
            repair=False,
            uninstall=False,
            uninstall_dry_run=False,
        )

        detect_environment.return_value = make_environment(
            operating_system="Darwin"
        )

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 1)
        run_linux_install.assert_not_called()


    @patch.object(install, "print_linux_distribution")
    @patch.object(install, "detect_linux_distribution")
    @patch.object(install, "print_check_results")
    @patch.object(install, "check_linux_requirements")
    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_repair_dispatches_real_linux_install(
        self,
        parse_arguments,
        run_linux_install,
        detect_environment,
        print_environment,
        check_linux_requirements,
        print_check_results,
        detect_linux_distribution,
        print_linux_distribution,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=False,
            repair=True,
            uninstall=False,
            uninstall_dry_run=False,
        )

        environment = make_environment()
        distro_info = {
            "is_debian_family": True,
        }

        detect_environment.return_value = environment
        detect_linux_distribution.return_value = distro_info
        check_linux_requirements.return_value = []
        run_linux_install.return_value = True

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 0)

        run_linux_install.assert_called_once_with(
            environment,
            distro_info,
            dry_run=False,
        )

    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_uninstall")
    @patch.object(install, "parse_arguments")
    def test_uninstall_dispatches_linux_uninstall(
        self,
        parse_arguments,
        run_linux_uninstall,
        detect_environment,
        print_environment,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=False,
            repair=False,
            uninstall=True,
            uninstall_dry_run=False,
        )

        environment = make_environment()
        detect_environment.return_value = environment
        run_linux_uninstall.return_value = True

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 0)

        run_linux_uninstall.assert_called_once_with(
            environment,
            dry_run=False,
        )

    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_uninstall")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_repair_rejects_non_linux_platform(
        self,
        parse_arguments,
        run_linux_install,
        run_linux_uninstall,
        detect_environment,
        print_environment,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=False,
            repair=True,
            uninstall=False,
            uninstall_dry_run=False,
        )

        detect_environment.return_value = make_environment("Windows")

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 1)
        run_linux_install.assert_not_called()
        run_linux_uninstall.assert_not_called()

    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_uninstall")
    @patch.object(install, "run_linux_install")
    @patch.object(install, "parse_arguments")
    def test_uninstall_rejects_non_linux_platform(
        self,
        parse_arguments,
        run_linux_install,
        run_linux_uninstall,
        detect_environment,
        print_environment,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=False,
            repair=False,
            uninstall=True,
            uninstall_dry_run=False,
        )

        detect_environment.return_value = make_environment("Darwin")

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 1)
        run_linux_install.assert_not_called()
        run_linux_uninstall.assert_not_called()


    @patch.object(install, "print_environment")
    @patch.object(install, "detect_environment")
    @patch.object(install, "run_linux_uninstall")
    @patch.object(install, "parse_arguments")
    def test_uninstall_dry_run_dispatches_non_destructive_uninstall(
        self,
        parse_arguments,
        run_linux_uninstall,
        detect_environment,
        print_environment,
    ):
        parse_arguments.return_value = Namespace(
            check=False,
            dry_run=False,
            install=False,
            repair=False,
            uninstall=False,
            uninstall_dry_run=True,
        )

        environment = make_environment()
        detect_environment.return_value = environment
        run_linux_uninstall.return_value = True

        with self.assertRaises(SystemExit) as context:
            install.main()

        self.assertEqual(context.exception.code, 0)

        run_linux_uninstall.assert_called_once_with(
            environment,
            dry_run=True,
        )


if __name__ == "__main__":
    unittest.main()
