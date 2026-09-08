import os
import socket
import psutil


def get_temperature():
    paths = [
        "/sys/class/thermal/thermal_zone0/temp",
    ]

    for path in paths:
        try:
            with open(path, "r") as f:
                value = float(f.read().strip())
                return round(value / 1000, 1)
        except Exception:
            pass

    return None


def get_network_interfaces():
    interfaces = []

    stats = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()

    for name, addr_list in addresses.items():
        if name == "lo":
            continue

        ipv4 = None

        for addr in addr_list:
            if addr.family == socket.AF_INET:
                ipv4 = addr.address
                break

        interface_stats = stats.get(name)

        interfaces.append({
            "name": name,
            "ipv4": ipv4,
            "up": interface_stats.isup if interface_stats else False,
            "speed_mbps": (
                interface_stats.speed
                if interface_stats and interface_stats.speed > 0
                else None
            ),
        })

    return interfaces


def get_system_metrics():
    memory = psutil.virtual_memory()

    return {
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "temperature_c": get_temperature(),
        "memory_percent": memory.percent,
        "memory_used_mb": round(memory.used / 1024 / 1024),
        "memory_total_mb": round(memory.total / 1024 / 1024),
        "load_average": [
            round(value, 2)
            for value in os.getloadavg()
        ],
        "network_interfaces": get_network_interfaces(),
    }
