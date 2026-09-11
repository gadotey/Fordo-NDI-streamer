from pathlib import Path
import shutil
from datetime import datetime


def get_autostart_path() -> Path:
    return Path.home() / ".config" / "labwc" / "autostart"


def get_fordo_line(project_root: str) -> str:
    script = Path(project_root).resolve() / "scripts" / "start-appliance.sh"
    return f"{script} &"


def inspect_autostart(project_root: str) -> dict:
    autostart = get_autostart_path()
    target_line = get_fordo_line(project_root)

    if not autostart.is_file():
        return {
            "path": str(autostart),
            "exists": False,
            "fordo_present": False,
            "fordo_line": target_line,
        }

    lines = [line.strip() for line in autostart.read_text().splitlines()]

    return {
        "path": str(autostart),
        "exists": True,
        "fordo_present": target_line in lines,
        "fordo_line": target_line,
    }


def print_autostart_state(state: dict) -> None:
    print()
    print("labwc Autostart State")
    print("=" * 60)
    print(f"autostart_exists      {'YES' if state['exists'] else 'NO'}")
    print(f"fordo_entry_present   {'YES' if state['fordo_present'] else 'NO'}")
    print(f"autostart_path        {state['path']}")
    print(f"fordo_entry           {state['fordo_line']}")
    print("=" * 60)


def configure_autostart(project_root: str, dry_run: bool = True) -> bool:
    autostart = get_autostart_path()
    target_line = get_fordo_line(project_root)

    existing_lines = []
    if autostart.is_file():
        existing_lines = autostart.read_text().splitlines()

    normalized = [line.strip() for line in existing_lines]

    if target_line in normalized:
        print("Fordo labwc autostart entry already exists. No changes required.")
        return True

    def is_fordo_entry(line: str) -> bool:
        return "scripts/start-appliance.sh" in line.strip()

    stale_entries = [
        line.strip()
        for line in existing_lines
        if is_fordo_entry(line)
    ]

    if dry_run:
        print("DRY RUN - labwc autostart will not be modified.")
        if stale_entries:
            print("Stale Fordo entries to replace:")
            for entry in stale_entries:
                print(f"  {entry}")
            print("Replacement entry:")
        else:
            print("Planned entry:")
        print(target_line)
        return True

    autostart.parent.mkdir(parents=True, exist_ok=True)

    if autostart.is_file():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = autostart.with_name(f"autostart.backup-{timestamp}")
        shutil.copy2(autostart, backup)
        print(f"Backup created: {backup}")

    new_lines = []
    replacement_added = False

    for line in existing_lines:
        if is_fordo_entry(line):
            if not replacement_added:
                new_lines.append(target_line)
                replacement_added = True
            continue

        new_lines.append(line)

    if not replacement_added:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(target_line)

    autostart.write_text("\n".join(new_lines) + "\n")

    return inspect_autostart(project_root)["fordo_present"]


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    state = inspect_autostart(str(project_root))
    print_autostart_state(state)
