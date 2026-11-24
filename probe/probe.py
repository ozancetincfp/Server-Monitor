import socket
import subprocess

import requests


def get_disk_usage():
    command = ["df", "-P", "-k"]
    result = subprocess.run(command, capture_output=True, text=True)
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
hostname = socket.gethostname()

report = { 
    "hostname": hostname,
    "disks": all_disks,
}

response = requests.post("http://127.0.0.1:8000/api/reports", json=report)
print(response.status_code)
print(response.json())
