#!/usr/bin/env python3

import json
import time
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_HEALTH_URL = "http://127.0.0.1:8080/api/health"


def check_health_once(url: str = DEFAULT_HEALTH_URL, timeout: float = 2.0) -> dict:
    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "healthy": False,
        "response": None,
        "error": None,
    }

    try:
        with urlopen(url, timeout=timeout) as response:
            result["status_code"] = response.status
            body = response.read().decode("utf-8", errors="replace")
            result["reachable"] = True

            try:
                result["response"] = json.loads(body)
            except json.JSONDecodeError:
                result["response"] = body

            result["healthy"] = (
                response.status == 200
                and isinstance(result["response"], dict)
                and result["response"].get("status") == "ok"
            )

    except (URLError, TimeoutError, OSError) as exc:
        result["error"] = str(exc)

    return result


def wait_for_health(
    url: str = DEFAULT_HEALTH_URL,
    attempts: int = 15,
    delay: float = 2.0,
    timeout: float = 2.0,
) -> dict:
    last_result = None

    for attempt in range(1, attempts + 1):
        result = check_health_once(url=url, timeout=timeout)
        last_result = result

        if result["healthy"]:
            result["attempt"] = attempt
            return result

        if attempt < attempts:
            time.sleep(delay)

    if last_result is None:
        last_result = {
            "url": url,
            "reachable": False,
            "status_code": None,
            "healthy": False,
            "response": None,
            "error": "Health check did not run.",
        }

    last_result["attempt"] = attempts
    return last_result


def print_health_result(result: dict) -> None:
    print()
    print("Fordo Service Health")
    print("=" * 50)
    print(f"url                 {result['url']}")
    print(f"reachable           {'YES' if result['reachable'] else 'NO'}")
    print(f"status_code         {result['status_code'] or '-'}")
    print(f"healthy             {'YES' if result['healthy'] else 'NO'}")
    print(f"attempt             {result.get('attempt', 1)}")

    if result.get("error"):
        print(f"error               {result['error']}")

    print("=" * 50)


if __name__ == "__main__":
    result = wait_for_health()
    print_health_result(result)
    raise SystemExit(0 if result["healthy"] else 1)
