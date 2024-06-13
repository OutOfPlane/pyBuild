import json
import subprocess
import re
import os
import sys


def readCmdArg(id: str, default: str):
    for i, arg in enumerate(sys.argv):
        if arg == id:
            return sys.argv[i + 1]
    return default

project_config = readCmdArg("-p", "project.json")
build_config = readCmdArg("-b", "build.json")


def readJson(filename) -> dict:
    f = open(filename)
    js = json.loads(f.read())
    f.close()
    return js


def haltCatchFire(reason):
    print()
    print("#" * 40)
    print("Upload failed: " + reason)
    print()
    exit(-1)


project = readJson(project_config)
build = readJson(build_config)

project_keylist = ["name", "version", "outputs"]

build_keylist = ["PROG_PATH"]

missing_project_settings = set(project_keylist).difference(project.keys())
missing_build_settings = set(build_keylist).difference(build.keys())

if len(missing_project_settings) > 0:
    print("Project is missing following REQUIRED settings:")
    for k in missing_project_settings:
        print("\t" + k)
    haltCatchFire("Incomplete project.json")

if len(missing_build_settings) > 0:
    print("Build is missing following REQUIRED settings:")
    for k in missing_build_settings:
        print("\t" + k)
    haltCatchFire("Incomplete build.json")

## Starting Project Upload

#set important variables
LOADER = build['PROG_PATH']
OUTPUTS = project['outputs']

#upload the boy
for outp in OUTPUTS:
    NAME = os.path.join(os.path.splitext(project_config)[0],outp["name"])
    FILENAME = NAME + '.elf'
    ORIG = outp['start_address']
    print(f"Uploading Firmware for {NAME}")
    o = subprocess.run((LOADER, "-c", "port=SWD", "freq=4000", "-w", os.path.abspath(FILENAME), ORIG, "-rst"), capture_output=True)
    print(' '.join(o.args))
    if(o.returncode != 0):
        print(o.stdout.decode("ASCII"))
        haltCatchFire(f"an error occured during upload")
    print()

    print("#"*40)
    print("Upload completed successfully")
    print()