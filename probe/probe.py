import subprocess


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
for disk in all_disks:
    print(disk)
print(len(all_disks))