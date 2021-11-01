# PyUnity Editor

[![License](https://img.shields.io/pypi/l/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://github.com/pyunity/pyunity-gui/blob/master/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://pypi.python.org/pypi/pyunity-gui)
[![Python version](https://img.shields.io/pypi/pyversions/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://pypi.python.org/pypi/pyunity-gui)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/pyunity/pyunity-editor.svg?logo=lgtm)](https://lgtm.com/projects/g/pyunity/pyunity-gui/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/pyunity/pyunity-gui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/pyunity/pyunity-gui/alerts/)
[![Discord](https://img.shields.io/discord/835911328693616680?logo=discord&label=discord)](https://discord.gg/zTn48BEbF9)
[![Gitter](https://badges.gitter.im/pyunity/community.svg)](https://gitter.im/pyunity/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![GitHub Repo stars](https://img.shields.io/github/stars/pyunity/pyunity-gui?logo=github)](https://github.com/pyunity/pyunity-gui/stargazers)

This is a pure Python editor to make <a href="https://github.com/pyunity/pyunity">PyUnity</a> projects.
PyUnity is a pure Python Game Engine that is only inspired by Unity and does not contain or is not a binding for Unity itself.
Therefore, PyUnity Editor is also completely seperate from UnityEditor.

## Installing

The PyUnity Editor can be installed via pip:

    > pip install pyunity-editor

Alternatively, you can clone the repository to build the package from source. These builds are sometimes broken, so use at your own risk. You can build as follows:

    > git clone https://github.com/pyunity/pyunity-gui
    > git checkout master
    > python setup.py install

Its only dependencies are PyUnity, PyQt5 and Pillow. Microsoft Visual C++ Build Tools are required on Windows for building PyUnity from source (if there isn't a wheel available). The PyUnity Editor requires a PyUnity version of at least 0.7.1.

## Running
To run the PyUnity Editor, you run this command from the terminal:

    > pyunity-editor project/

where `project/` is your project folder. The PyUnity Editor will launch with a splash screen, then the editor window will appear.

## Contributing

If you would like to contribute, please
first see the [contributing guidelines](https://github.com/pyunity/pyunity-gui/blob/master/contributing.md),
check out the latest [issues](https://github.com/pyunity/pyunity-gui/issues)
and then make a [pull request](https://github.com/pyunity/pyunity-gui/pulls).
