import subprocess
command = ["df", "-P", "-k"]
result = subprocess.run(command, capture_output=True, text=True)
print(result.stdout)