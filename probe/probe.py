import logging
import os
import socket
import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()

NOC_URL = os.environ.get("NOC_URL", "http://127.0.0.1:8000")
PROBE_HOSTNAME = os.environ.get("PROBE_HOSTNAME", "")
API_KEY = os.environ.get("API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def get_disk_usage():
    command = ["df", "-P", "-k"]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    lines = result.stdout.splitlines()

    disks = []
    for line in lines[1:]:
        parts = line.split(maxsplit=5)
        if not parts[0].startswith("/dev/"):
            continue
        if parts[1] == "0":
            continue
        disk = {
            "mount": parts[5],
            "size_kb": int(parts[1]),
            "used_kb": int(parts[2]),
            "avail_kb": int(parts[3]),
            "use_percent": int(parts[4].rstrip("%")),
        }
        disks.append(disk)

    return disks


all_disks = get_disk_usage()

hostname = PROBE_HOSTNAME or socket.gethostname()

report = {
    "hostname": hostname,
    "disks": all_disks,
}



try:
    response = requests.post(f"{NOC_URL}/api/reports", json=report, timeout=10,headers={"X-API-Key": API_KEY})
    response.raise_for_status()
    logging.info(f"Report sent for {hostname}: {len(all_disks)} disks")
except requests.RequestException as error:
    logging.error(f"Could not send report: {error}")
