import subprocess

GIT_EXE = r"C:\Users\luc_mcmullan\Documents\PortableGit\cmd\git.exe"
MAJOR_VERSION = 1

try:
    BUILD_DATE = subprocess.check_output([GIT_EXE, "log", "-1", "--format=%cd", "--date=short"], text=True).strip()
    BUILD_NUMBER = int(subprocess.check_output([GIT_EXE, "rev-list", "--count", "HEAD"], text=True).strip())
except Exception:
    BUILD_DATE = "Unknown - git not found"
    BUILD_NUMBER = 0

build_str = str(BUILD_NUMBER)

if len(build_str) == 1:
    minor = 0
    patch = int(build_str)
else:
    minor = int(build_str[:-1])
    patch = int(build_str[-1])

VERSION = f"{MAJOR_VERSION}.{minor}.{patch}"