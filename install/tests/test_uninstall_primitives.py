import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

INSTALL_DIR = Path(__file__).resolve().parents[1]
if str(INSTALL_DIR) not in sys.path:
    sys.path.insert(0, str(INSTALL_DIR))

from platforms import labwc_autostart
from platforms import systemd_service


class TestSystemdServiceRemoval(unittest.TestCase):

    def test_missing_service_is_already_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service_path = Path(temp_dir) / "fordo-ndi.service"

            with patch.object(systemd_service, "SERVICE_PATH", service_path):
                result = systemd_service.remove_service(dry_run=False)

            self.assertTrue(result)
            self.assertFalse(service_path.exists())

    def test_dry_run_does_not_remove_service(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service_path = Path(temp_dir) / "fordo-ndi.service"
            service_path.write_text("test service")

            with (
                patch.object(systemd_service, "SERVICE_PATH", service_path),
                patch.object(systemd_service, "systemctl_available", return_value=True),
                patch.object(systemd_service, "service_is_active", return_value=True),
            ):
                result = systemd_service.remove_service(dry_run=True)

            self.assertTrue(result)
            self.assertTrue(service_path.exists())

    @patch.object(systemd_service.subprocess, "run")
    def test_real_removal_uses_systemctl_and_removes_service(self, run):
        with tempfile.TemporaryDirectory() as temp_dir:
            service_path = Path(temp_dir) / "fordo-ndi.service"
            service_path.write_text("test service")

            def command_side_effect(command, check=False):
                if "rm" in command:
                    service_path.unlink(missing_ok=True)

            run.side_effect = command_side_effect

            with (
                patch.object(systemd_service, "SERVICE_PATH", service_path),
                patch.object(systemd_service, "systemctl_available", return_value=True),
                patch.object(systemd_service, "service_is_active", return_value=True),
                patch.object(systemd_service, "privilege_prefix", return_value=["sudo"]),
            ):
                result = systemd_service.remove_service(dry_run=False)

            self.assertTrue(result)
            self.assertFalse(service_path.exists())

            commands = [call.args[0] for call in run.call_args_list]

            self.assertIn(
                ["sudo", "systemctl", "stop", systemd_service.SERVICE_NAME],
                commands,
            )
            self.assertIn(
                ["sudo", "systemctl", "disable", systemd_service.SERVICE_NAME],
                commands,
            )
            self.assertIn(
                ["sudo", "rm", "-f", str(service_path)],
                commands,
            )
            self.assertIn(
                ["sudo", "systemctl", "daemon-reload"],
                commands,
            )


class TestLabwcAutostartRemoval(unittest.TestCase):

    def test_missing_autostart_is_already_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            autostart = Path(temp_dir) / "autostart"

            with patch.object(
                labwc_autostart,
                "get_autostart_path",
                return_value=autostart,
            ):
                result = labwc_autostart.remove_autostart(
                    "/tmp/fordo",
                    dry_run=False,
                )

            self.assertTrue(result)
            self.assertFalse(autostart.exists())

    def test_dry_run_preserves_fordo_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            autostart = Path(temp_dir) / "autostart"
            autostart.write_text(
                "unrelated-command &\n"
                "/tmp/fordo/scripts/start-appliance.sh &\n"
            )

            with patch.object(
                labwc_autostart,
                "get_autostart_path",
                return_value=autostart,
            ):
                result = labwc_autostart.remove_autostart(
                    "/tmp/fordo",
                    dry_run=True,
                )

            self.assertTrue(result)

            content = autostart.read_text()
            self.assertIn("unrelated-command &", content)
            self.assertIn("scripts/start-appliance.sh", content)

    def test_removal_preserves_unrelated_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            autostart = Path(temp_dir) / "autostart"
            autostart.write_text(
                "first-command &\n"
                "/old/fordo/scripts/start-appliance.sh &\n"
                "second-command &\n"
                "/tmp/fordo/scripts/start-appliance.sh &\n"
            )

            with patch.object(
                labwc_autostart,
                "get_autostart_path",
                return_value=autostart,
            ):
                result = labwc_autostart.remove_autostart(
                    "/tmp/fordo",
                    dry_run=False,
                )

            self.assertTrue(result)

            content = autostart.read_text()

            self.assertIn("first-command &", content)
            self.assertIn("second-command &", content)
            self.assertIn(
                "/old/fordo/scripts/start-appliance.sh &",
                content,
            )
            self.assertNotIn(
                "/tmp/fordo/scripts/start-appliance.sh &",
                content,
            )

            backups = list(
                Path(temp_dir).glob("autostart.backup-*")
            )
            self.assertEqual(len(backups), 1)


if __name__ == "__main__":
    unittest.main()
