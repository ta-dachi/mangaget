import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
#build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

includefiles = ['mangabee_parsers.py', 'mangahere_parsers.py', 'helper.py'] # include any files here that you wish
includes = []
excludes = []
packages = []

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable(
    script = "mangaget.py",
    copyDependentFiles = True,
    compress = True,
    appendScriptToExe = True,
    appendScriptToLibrary = True,
)

setup(  name = "mangaget",
        version = "1.0.0",
        description = "Downloads manga from mangahere and mangabee",
        options = {"build_exe": {"excludes":excludes,"packages":packages,
            "include_files":includefiles}},
        executables = [exe]
)
