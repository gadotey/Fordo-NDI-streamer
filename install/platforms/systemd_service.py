import getpass
import grp
import os
import subprocess
from pathlib import Path

from platforms.privileges import privilege_prefix


SERVICE_NAME = "fordo-ndi.service"
SERVICE_PATH = Path("/etc/systemd/system") / SERVICE_NAME


def get_service_user():
    return getpass.getuser()


def get_service_group():
    user = get_service_user()
    return grp.getgrgid(os.getgid()).gr_name


def render_service(project_root):
    project_root = Path(project_root).resolve()
    user = get_service_user()
    group = get_service_group()
    uvicorn_path = project_root / ".venv" / "bin" / "uvicorn"

    return f"""[Unit]
Description=Fordo NDI Streamer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={project_root}

Environment="PYTHONUNBUFFERED=1"
Environment="LD_LIBRARY_PATH=/usr/local/lib"

ExecStart={uvicorn_path} app.main:app --host 0.0.0.0 --port 8080

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def inspect_service(project_root):
    expected = render_service(project_root)

    return {
        "service_path": str(SERVICE_PATH),
        "service_exists": SERVICE_PATH.is_file(),
        "service_matches": (
            SERVICE_PATH.is_file()
            and SERVICE_PATH.read_text() == expected
        ),
    }


def print_service_state(state):
    print()
    print("Fordo systemd Service State")
    print("=" * 50)
    print(f"service_exists       {'YES' if state['service_exists'] else 'NO'}")
    print(f"service_matches      {'YES' if state['service_matches'] else 'NO'}")
    print(f"service_path         {state['service_path']}")
    print("=" * 50)


def service_is_active() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", SERVICE_NAME],
            check=False,
        )
    except OSError:
        return False

    return result.returncode == 0


def install_service(project_root, dry_run=True):
    expected = render_service(project_root)
    state = inspect_service(project_root)

    if state["service_matches"]:
        print("systemd service is already installed and matches the generated configuration.")
        return True

    if dry_run:
        print("DRY RUN - systemd service will not be modified.")
        print("Planned actions:")
        if state["service_exists"]:
            print(f"  backup existing {SERVICE_PATH}")
        print(f"  write {SERVICE_PATH}")
        print("  systemctl daemon-reload")
        print(f"  systemctl enable {SERVICE_NAME}")
        print(f"  systemctl restart {SERVICE_NAME}")
        return True

    import tempfile
    from datetime import datetime

    prefix = privilege_prefix()

    if prefix is None:
        print(
            "systemd service installation requires root privileges, "
            "but sudo is not available."
        )
        return False

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        prefix="fordo-ndi-",
        suffix=".service",
    ) as temp:
        temp.write(expected)
        temp_path = temp.name

    try:
        if state["service_exists"]:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = SERVICE_PATH.with_name(
                f"{SERVICE_NAME}.backup-{timestamp}"
            )

            print(f"Backing up existing systemd service to {backup_path}")

            subprocess.run(
                [*prefix, "cp", str(SERVICE_PATH), str(backup_path)],
                check=True,
            )

        subprocess.run(
            [*prefix, "cp", temp_path, str(SERVICE_PATH)],
            check=True,
        )
        subprocess.run(
            [*prefix, "systemctl", "daemon-reload"],
            check=True,
        )
        subprocess.run(
            [*prefix, "systemctl", "enable", SERVICE_NAME],
            check=True,
        )
        subprocess.run(
            [*prefix, "systemctl", "restart", SERVICE_NAME],
            check=True,
        )

    except subprocess.CalledProcessError as exc:
        print(f"systemd service installation failed: {exc}")
        return False

    finally:
        Path(temp_path).unlink(missing_ok=True)

    return inspect_service(project_root)["service_matches"]


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    print(render_service(project_root))
