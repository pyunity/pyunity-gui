from setuptools import setup, find_packages
import glob

with open("README.md", "r") as fh:
    long_description = fh.read()

data_files = glob.glob("editor/**/*.qss", recursive=True) + \
    glob.glob("editor/**/*.png", recursive=True)

setup(
    packages=["editor"] + ["editor." + package for package in find_packages(where="editor")],
    package_data={"editor": [file[7:] for file in data_files]},
    entry_points={
        "gui_scripts": [
            "pyunity-editor=editor.cli:gui"
        ],
        # "console_scripts": [
        #     "pyunity-editor=editor.cli:run"
        # ],
    }
)
