from pathlib import Path


OS_RELEASE = Path("/etc/os-release")


def read_os_release():
    data = {}

    if not OS_RELEASE.is_file():
        return data

    for line in OS_RELEASE.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        value = value.strip().strip('"')

        data[key] = value

    return data


def detect_linux_distribution():
    data = read_os_release()

    distro_id = data.get("ID", "").lower()
    id_like = {
        item.strip().lower()
        for item in data.get("ID_LIKE", "").split()
        if item.strip()
    }

    is_debian_family = (
        distro_id in {"debian", "ubuntu", "raspbian"}
        or "debian" in id_like
    )

    return {
        "id": distro_id or None,
        "name": data.get("NAME"),
        "pretty_name": data.get("PRETTY_NAME"),
        "version_id": data.get("VERSION_ID"),
        "version_codename": data.get("VERSION_CODENAME"),
        "id_like": sorted(id_like),
        "is_debian_family": is_debian_family,
    }


def print_linux_distribution(info):
    print()
    print("Linux Distribution")
    print("=" * 50)
    print(f"id                    {info['id']}")
    print(f"name                  {info['name']}")
    print(f"pretty_name           {info['pretty_name']}")
    print(f"version_id            {info['version_id']}")
    print(f"version_codename      {info['version_codename']}")
    print(f"id_like               {', '.join(info['id_like']) if info['id_like'] else '-'}")
    print(f"debian_family         {'YES' if info['is_debian_family'] else 'NO'}")
    print("=" * 50)


if __name__ == "__main__":
    print_linux_distribution(detect_linux_distribution())
