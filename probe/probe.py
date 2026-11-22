import subprocess

command = ["df", "-P", "-k"]
result = subprocess.run(command, capture_output=True, text=True)
lines = result.stdout.splitlines()

for line in lines[1:]:
    parts = line.split(maxsplit=5)
    if not parts[0].startswith("/dev/"):
        continue
    if parts[1] == "0":
        continue
    print(parts)