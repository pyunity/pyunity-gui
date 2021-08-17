from .splash import start, disable_print
from time import strftime
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Please specify a file.")
        return
    elif not os.path.isdir(sys.argv[1]):
        print("Please specify a valid directory.")
        return
    
    from .app import Application
    app = Application(sys.argv[1])
    app.start()

def gui():
    disable_print()
    os.environ["PYUNITY_DEBUG_MODE"] = "0"
    from pyunity import Logger
    directory = os.path.join(os.path.dirname(Logger.folder), "Editor", "Logs")
    os.makedirs(directory, exist_ok=True)
    Logger.SetStream(open(os.path.join(directory, strftime("%Y-%m-%d %H-%M-%S") + ".log"), "w+"))
    start(main)

def run():
    start(main)
