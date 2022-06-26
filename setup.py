from setuptools import setup, find_packages
import glob

with open("README.md", "r") as fh:
    long_description = fh.read()

data_files = glob.glob("pyunity_editor/**/*.qss", recursive=True) + \
    glob.glob("pyunity_editor/**/*.png", recursive=True)

setup(
    packages=["pyunity_editor"] + ["pyunity_editor." + package for package in find_packages(where="pyunity_editor")],
    package_data={"pyunity_editor": [file[7:] for file in data_files]},
    entry_points={
        "gui_scripts": [
            "pyunity-editor=pyunity_editor.cli:gui"
        ],
        # "console_scripts": [
        #     "pyunity-editor=pyunity_editor.cli:run"
        # ],
    }
)
