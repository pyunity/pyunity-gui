# PyUnity Editor

[![License](https://img.shields.io/pypi/l/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://github.com/pyunity/pyunity-gui/blob/master/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://pypi.python.org/pypi/pyunity-gui)
[![Python version](https://img.shields.io/pypi/pyversions/pyunity-editor.svg?logo=python&logoColor=FBE072)](https://pypi.python.org/pypi/pyunity-gui)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/pyunity/pyunity-gui.svg?logo=lgtm)](https://lgtm.com/projects/g/pyunity/pyunity-gui/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/pyunity/pyunity-gui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/pyunity/pyunity-gui/alerts/)
[![Discord](https://img.shields.io/discord/835911328693616680?logo=discord&label=discord)](https://discord.gg/zTn48BEbF9)
[![Gitter](https://badges.gitter.im/pyunity/community.svg)](https://gitter.im/pyunity/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![GitHub Repo stars](https://img.shields.io/github/stars/pyunity/pyunity-gui?logo=github)](https://github.com/pyunity/pyunity-gui/stargazers)

This is a pure Python editor to make [PyUnity](https://github.com/pyunity/pyunity) projects.
PyUnity is a pure Python Game Engine that is only inspired by Unity and does not contain or is not a binding for Unity itself.
Therefore, PyUnity Editor is also completely seperate from UnityEditor.

## Installing

The PyPi package does not work with the latest releases of PyUnity, and as such the best way
to use this editor is to clone this editor and regularly run `git pull` to update. From the repo,
running `python -m pyunity_editor ProjectPath/` will work. To create a new project, run
`python -m pyunity_editor --new ProjectPath/`. Note that this editor also relies on the `develop` branch
of PyUnity, which can be fetched with `install.py`. Run this periodically in case of any errors.

A full run would look something like this:

```
git clone https://github.com/pyunity/pyunity-gui/
cd pyunity-gui/
python install.py
python -m pip install -r requirements.txt
python -m pyunity_editor --new ProjectPath/
```

## Contributing

If you would like to contribute, please
first see the [contributing guidelines](https://github.com/pyunity/pyunity-gui/blob/master/contributing.md),
check out the latest [issues](https://github.com/pyunity/pyunity-gui/issues)
and then make a [pull request](https://github.com/pyunity/pyunity-gui/pulls).
