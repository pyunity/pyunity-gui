from .splash import start, redirect_out
from time import strftime
import os
import io
import sys

def check():
    if len(sys.argv) < 2:
        print("Please specify a project.")
        return False
    elif not os.path.isdir(sys.argv[1]):
        print("Please specify a valid directory.")
        return False
    return True

def run():
    from .app import Application
    app = Application(sys.argv[1])
    app.start()

def main():
    if not check():
        return
    start(run())

def gui():
    if not check():
        return
    
    temp_stream = io.StringIO()
    redirect_out(temp_stream)

    os.environ["PYUNITY_DEBUG_MODE"] = "0"
    from pyunity import Logger
    directory = os.path.join(os.path.dirname(Logger.folder), "Editor", "Logs")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, strftime("%Y-%m-%d %H-%M-%S") + ".log")
    f = open(path, "w+")

    temp_stream.seek(0)
    f.write(temp_stream.read())
    temp_stream.close()
    redirect_out(f)
    Logger.SetStream(f)
    start(run)
