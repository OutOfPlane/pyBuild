import os
import shutil
import json

def readJson(filename) -> dict:
    f = open(filename)
    js = json.loads(f.read())
    f.close()
    return js

build_config = "build.json"
build = readJson(build_config)

build_keylist = ["GCC_PATH", "PROG_PATH"]

missing_build_settings = set(build_keylist).difference(build.keys())


if len(missing_build_settings) > 0:
    print("Build is missing following REQUIRED settings:")
    for k in missing_build_settings:
        print("\t" + k)
    print("Incomplete build.json")
    exit()


GCC = build['GCC_PATH']
PROG = build['PROG_PATH']




BASE_FOLDER = os.path.join(__file__, os.pardir)
TEMPLATE_FOLDER = os.path.join(BASE_FOLDER, "templates")

DOT_PATH = ""
WORKSPACE_PATH = os.path.join(BASE_FOLDER, os.pardir)

for dir in os.listdir(WORKSPACE_PATH):
    if(os.path.isdir(dir)):
        if(dir == ".vscode"):
            DOT_PATH = os.path.join(WORKSPACE_PATH, dir)

if(DOT_PATH == ""):
    print(".vscode folder not found, make sure it exists and pycbuild/ is in the base of the Workspace")
    exit()



template_list = []

print("Verfügbare Vorlagen:")

cnt = 0
for dir in os.listdir(TEMPLATE_FOLDER):
    lpath = os.path.join(TEMPLATE_FOLDER, dir)
    if(os.path.isdir(lpath)):
        template_list.append(lpath)
        print(f"\t[{cnt:2d}] {dir}")
        cnt += 1


templ = int(input("Auswahl: "))

if(templ >= cnt):
    print("ungültige Auswahl")
    exit()
    
template = template_list[templ]


VS_PATH = os.path.join(template, "vscode")

C_CPP = "c_cpp_properties.json"
TASKS = "tasks.json"
LAUNCH = "launch.json"
SETTINGS = "settings.json"
GITIGNORE = "gitignore_template"


def askOverride(filename) -> bool:
    if(input(f"{filename} existiert bereits, überschreiben? [y/n]: ") == "y"):
        return True
    return False


if(not os.path.exists(os.path.join(DOT_PATH, C_CPP))) or (askOverride(C_CPP)):
    shutil.copy(os.path.join(VS_PATH, C_CPP), DOT_PATH)

if(not os.path.exists(os.path.join(DOT_PATH, TASKS))) or (askOverride(TASKS)):
    shutil.copy(os.path.join(VS_PATH, TASKS), DOT_PATH)

if(not os.path.exists(os.path.join(DOT_PATH, LAUNCH))) or (askOverride(LAUNCH)):
    shutil.copy(os.path.join(VS_PATH, LAUNCH), DOT_PATH)

if(not os.path.exists(os.path.join(DOT_PATH, SETTINGS))) or (askOverride(SETTINGS)):
    shutil.copy(os.path.join(VS_PATH, SETTINGS), DOT_PATH)

if(not os.path.exists(os.path.join(WORKSPACE_PATH, ".gitignore"))) or (askOverride(".gitignore")):
    shutil.copy(os.path.join(VS_PATH, GITIGNORE), ".gitignore")


file = open(os.path.join(DOT_PATH, LAUNCH), "r")
content = str(file.read())
file.close()

file = open(os.path.join(DOT_PATH, LAUNCH), "w")
file.write(content)

file.close()




