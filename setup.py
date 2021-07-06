# gui_scripts

from setuptools import setup, find_packages
import os
import glob

with open("README.md", "r") as fh:
    long_description = fh.read()

data_files = [file for file in glob.glob("editor/**/*", recursive=True) if ".py" not in file]

setup(
    name="pyunity-editor",
    version="0.1.0",
    author="Ray Chen",
    author_email="tankimarshal2@gmail.com",
    description="An Editor for PyUnity in the style of the UnityEditor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pyunity/pyunity-gui",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        "pyunity",
        "pyqt5",
        "pillow",
    ],
    python_requires='>=3',
    packages= ["editor"] + ["editor." + package for package in find_packages(where="editor")],
    package_data={"editor": [file[7:] for file in data_files]},
    entry_points={
        "console_scripts": [
            "pyunity-editor=editor.__main__:start_splash"
        ]
    }
)
