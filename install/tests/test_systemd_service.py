import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

INSTALL_DIR = Path(__file__).resolve().parents[1]
if str(INSTALL_DIR) not in sys.path:
    sys.path.insert(0, str(INSTALL_DIR))

from platforms import systemd_service


class TestSystemdService(unittest.TestCase):

    def test_inspect_service_handles_unreadable_existing_service(self):
        with TemporaryDirectory() as temp_dir:
            service_path = Path(temp_dir) / "fordo-ndi.service"
            service_path.write_text(
                "[Unit]\nDescription=Existing Fordo Test\n"
            )

            original_read_text = Path.read_text

            def unreadable_service(path_obj, *args, **kwargs):
                if path_obj == service_path:
                    raise PermissionError("permission denied")
                return original_read_text(path_obj, *args, **kwargs)

            with patch.object(
                systemd_service,
                "SERVICE_PATH",
                service_path,
            ), patch.object(
                systemd_service,
                "render_service",
                return_value="[Unit]\nDescription=Expected Fordo Test\n",
            ), patch.object(
                Path,
                "read_text",
                unreadable_service,
            ):
                state = systemd_service.inspect_service(
                    Path("/tmp/fordo-test")
                )

            self.assertTrue(state["service_exists"])
            self.assertFalse(state["service_matches"])


    def test_install_service_deploys_unit_as_root_root_0644(self):
        project_root = Path("/tmp/fordo-test")
        expected = "[Unit]\nDescription=Fordo Test\n"

        initial_state = {
            "service_path": str(systemd_service.SERVICE_PATH),
            "service_exists": False,
            "service_matches": False,
        }

        final_state = {
            "service_path": str(systemd_service.SERVICE_PATH),
            "service_exists": True,
            "service_matches": True,
        }

        with patch.object(
            systemd_service,
            "systemctl_available",
            return_value=True,
        ), patch.object(
            systemd_service,
            "render_service",
            return_value=expected,
        ), patch.object(
            systemd_service,
            "inspect_service",
            side_effect=[initial_state, final_state],
        ), patch.object(
            systemd_service,
            "privilege_prefix",
            return_value=["sudo"],
        ), patch.object(
            systemd_service.subprocess,
            "run",
        ) as run_mock:

            result = systemd_service.install_service(
                project_root,
                dry_run=False,
            )

        self.assertTrue(result)

        commands = [
            call.args[0]
            for call in run_mock.call_args_list
        ]

        install_commands = [
            command
            for command in commands
            if len(command) >= 2
            and command[0:2] == ["sudo", "install"]
        ]

        self.assertEqual(len(install_commands), 1)

        command = install_commands[0]

        self.assertIn("-o", command)
        self.assertIn("root", command)
        self.assertIn("-g", command)
        self.assertIn("-m", command)
        self.assertIn("0644", command)
        self.assertEqual(
            command[-1],
            str(systemd_service.SERVICE_PATH),
        )


if __name__ == "__main__":
    unittest.main()
