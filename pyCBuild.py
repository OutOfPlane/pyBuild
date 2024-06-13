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

contains_cpp = False


def readJson(filename) -> dict:
    f = open(filename)
    js = json.loads(f.read())
    f.close()
    return js


def writeJson(data, filename):
    f = open(filename, "w")
    f.write(json.dumps(data, indent=4))
    f.close()


def haltCatchFire(reason):
    print()
    print("#" * 40)
    print("Build failed: " + reason)
    print()
    exit(-1)


project = readJson(project_config)
build = readJson(build_config)

project_keylist = ["name", "version", "outputs"]

build_keylist = ["GCC_PATH", "PROG_PATH"]

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

## Starting Project Build
print("#" * 40)
print("Building Project: " + project["name"])
print("Version: " + project["version"])
print()

# set important variables
GCC = build["GCC_PATH"]

OUTPUTS = project["outputs"]
BUILD_FLAGS = project["build_flags"]
DEFINES = []
ALL_DEFINES = []
if "defines" in project:
    DEFINES = project["defines"]
C_DEFINES = []
for d in DEFINES:
    C_DEFINES.append("-D")
    C_DEFINES.append(d)

ALL_DEFINES += DEFINES

## Testing GCC and retrieve Version
gcc = subprocess.run((GCC, "--version"), capture_output=True)
GCC_VERSION = re.search(r"\d+\D\d+\D\d+ \d+", gcc.stdout.decode("ASCII"))
if GCC_VERSION != None:
    GCC_VERSION = GCC_VERSION.group(0)
    print("GCC Version: " + GCC_VERSION)
else:
    haltCatchFire("GCC Version konnte nicht ermittelt werden")

print()

obj_list = []
inc_list = []
changed_files = 0

latest_include = 0
latest_file = 0
project_def_tm = os.path.getmtime(project_config)

def addIncludeFolder(path):
    global inc_list, latest_include

    inc_list.append("-I")
    inc_list.append(os.path.abspath(path))

    for file in os.listdir(path):
        if file.endswith(".h"):
            mod_tm = os.path.getmtime(os.path.join(path, file))
            if mod_tm > latest_include:
                latest_include = mod_tm


def compileAllFiles(rpath, source_path, defines, flags):
    global obj_list, changed_files, latest_file, contains_cpp
    # create outdir
    objDir = os.path.join(OUT_DIR_ABS, rpath)
    if not os.path.exists(objDir):
        os.makedirs(objDir, exist_ok=True)

    for file in os.listdir(source_path):
        if file.endswith(".c") or file.endswith(".s") or file.endswith(".cpp"):
            if file.endswith(".cpp"):
                contains_cpp = True
            o_path = os.path.join(objDir, f"{os.path.splitext(file)[0]}.o")
            obj_list.append(o_path)
            c_path = os.path.join(source_path, file)
            c_tm = os.path.getmtime(c_path)
            o_tm = 0
            if os.path.exists(o_path):
                o_tm = os.path.getmtime(o_path)

            if latest_file < o_tm:
                latest_file = o_tm

            if (o_tm < c_tm) or (o_tm < latest_include) or (o_tm < project_def_tm):
                print("Compiling: " + file)
                changed_files += 1
                o = subprocess.run(
                    [
                        GCC,
                        f"-mcpu={CPU}",
                        os.path.abspath(c_path),
                        "-c",
                        "-o",
                        os.path.abspath(o_path),
                    ]
                    + inc_list
                    + defines
                    + flags,
                    capture_output=True,
                )
                print(" ".join(o.args))
                if o.returncode != 0:
                    print(o.stderr.decode("ASCII"))
                    haltCatchFire(f"an error occured compiling: {file}")
                print()
                o_tm = os.path.getmtime(o_path)
                if latest_file < o_tm:
                    latest_file = o_tm
            else:
                print(f"{file} already up to date!")
                # print()


def buildFolder(path, defines, flags):
    cSrc = os.path.join(path, "src/")
    cInc = os.path.join(path, "include/")
    cInc2 = os.path.join(path, "Inc/")

    if os.path.exists(cInc):
        addIncludeFolder(cInc)

    if os.path.exists(cInc2):
        addIncludeFolder(cInc2)

    if os.path.exists(cSrc):
        compileAllFiles(path, cSrc, defines, flags)

    if os.path.exists(path):
        compileAllFiles(path, path, defines, flags)


# build output products
for outp in OUTPUTS:
    OUT_NAME = os.path.join(os.path.splitext(project_config)[0],outp["name"] + ".elf")
    BUILD_ORDER = outp["build_order"]
    OUT_DIR = os.path.join(os.path.splitext(project_config)[0], outp["output_dir"])
    OUT_DIR_ABS = os.path.abspath(OUT_DIR)

    LINKER_FILE = outp["linker_file"]
    LINKER_FILE_ABS = os.path.abspath(LINKER_FILE)
    CPU = outp["cpu"]

    L_DEFINES = []
    if "defines" in outp:
        L_DEFINES = outp["defines"]
    LC_DEFINES = []
    for d in L_DEFINES:
        LC_DEFINES.append("-D")
        LC_DEFINES.append(d)

    ALL_DEFINES += L_DEFINES

    LBUILD_FLAGS = []
    if "build_flags" in outp:
        LBUILD_FLAGS = outp["build_flags"]

    if not os.path.isdir(OUT_DIR):
        print("creating missing output directory")
        os.makedirs(OUT_DIR, exist_ok=True)

    obj_list = []
    inc_list = []
    changed_files = 0

    latest_include = 0
    latest_file = 0

    for obj in BUILD_ORDER:
        if obj.endswith("*"):
            build_dir = str(obj).strip("*")
            b_dir = os.path.join(OUT_DIR, build_dir)
            out_dir = os.path.abspath(b_dir)
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            for folder in os.listdir(build_dir):
                buildFolder(
                    os.path.join(build_dir, folder),
                    C_DEFINES + LC_DEFINES,
                    LBUILD_FLAGS + BUILD_FLAGS,
                )
        else:
            buildFolder(obj, C_DEFINES + LC_DEFINES, LBUILD_FLAGS + BUILD_FLAGS)

    # link everything together
    elf_tm = 0
    if os.path.exists(OUT_NAME):
        elf_tm = os.path.getmtime(OUT_NAME)

    print("Linking everything together")
    if latest_file > elf_tm:
        extra_linker_flags = []
        if contains_cpp:
            print(
                "C++ files detected, add library libsupc++_nano for minimal c++ support"
            )
            extra_linker_flags.append("-lsupc++_nano")

        args = (
            [GCC, "-T", LINKER_FILE_ABS, f"-mcpu={CPU}"]
            + BUILD_FLAGS
            + LBUILD_FLAGS
            + obj_list
            + ["-o", OUT_NAME]
            + extra_linker_flags
        )
        o = subprocess.run(args, capture_output=True)
        print(" ".join(o.args))
        if o.returncode != 0:
            print(o.stderr.decode("ASCII"))
            haltCatchFire(f"an error occured during linking")
        print()

        print("#" * 40)
        print("Build completed successfully")
        print()
    else:
        print("#" * 40)
        print("Already up to date")
        print()


# last step: update c_cpp_proterties with defines
C_CPP_JSON = ".vscode/c_cpp_properties.json"

if os.path.exists(C_CPP_JSON):
    print("#" * 40)
    print("updating c_cpp_properties...")
    prop = readJson(C_CPP_JSON)
    prop["env"]["autogeneratedDefines"] = ALL_DEFINES
    writeJson(prop, C_CPP_JSON)
    print("done")
