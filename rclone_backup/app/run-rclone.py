import json
import subprocess
import sys
from datetime import datetime
from os.path import isdir
from os.path import isfile
from subprocess import CalledProcessError

CONFIG_PATH = "/data/options.json"
BACKUP_PATH = "/backup"
ALLOWED_COMMAND = ["sync", "copy"]
ALLOWED_SOURCE_PATH = ["/backup", "/config", "/share", "/ssl"]

with open(CONFIG_PATH) as file:
    config = json.loads(file.read())

print(f"[RCLONE] Running {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n")

command = config["command"]
sources = config["sources"]
destination = config["destination"]
rclone_config_path = config["config_path"]

if not command in ALLOWED_COMMAND:
    print(f"[RCLONE] Given command is not allowed! Allowed commands: {ALLOWED_COMMAND}")
    exit(1)

if not isfile(rclone_config_path):
    print(f"[RCLONE] Given rclone config file '{rclone_config_path}' does not exist!")
    exit(1)

with open(rclone_config_path) as file:
    if not any(line == ("[" + destination.split(":")[0] + "]\n") for line in file):
        print(f"[RCLONE] Did not find any rclone configuration matching '{destination}'!")
        exit(1)

for source in sources:
    print(f"[RCLONE] Start processing source '{source}'")

    if (not source.startswith(tuple(ALLOWED_SOURCE_PATH)) or (not isdir("/" + source.split("/")[1]))):
        print(f"[RCLONE] Given source '{source}' is not allowed! Allowed sources: {ALLOWED_SOURCE_PATH}")
        continue

    if not isdir(source):
        print(f"[RCLONE] Given source '{source}' directory does not exist!")
        continue

    subfolder = ""
    if len(sources) > 1:
        subfolder = f"{source}"

    if source.startswith(BACKUP_PATH):
        try:
            subprocess.run(
                [sys.executable, "/run-rename.py"], stdout=True, stderr=True, check=True
            )
        except CalledProcessError as ex:
            print(f"[RCLONE] Rename failed!")

    cmd = f"rclone {command} '{source}' '{destination}{subfolder}' --config '{rclone_config_path}' --verbose"

    for include in config["include"]:
        cmd += f" --include='{include}'"

    for exclude in config["exclude"]:
        cmd += f" --exclude='{exclude}'"

    if config.get("dry_run"):
        cmd += " --dry-run"

    if config.get("flags"):
        cmd += " " + config["flags"]

    print(f"[RCLONE] {cmd}")

    try:
        subprocess.run(cmd, stdout=True, stderr=True, check=True, shell=True)
    except CalledProcessError as ex:
        print(f"[RCLONE] Rclone failed!")

    if source.startswith(BACKUP_PATH):
        try:
            subprocess.run(
                [sys.executable, "/run-undo-rename.py"], stdout=True, stderr=True, check=True
            )
        except CalledProcessError as ex:
            print(f"[RCLONE] Undo rename failed!")

    print("\n")

print("[RCLONE] Done!")
print("\n" * 3)
