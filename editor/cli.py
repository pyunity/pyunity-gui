from .splash import start, redirect_out
from time import strftime
import argparse
import os
import io
import sys

parser = argparse.ArgumentParser(
    prog="editor", description="Launch the PyUnity editor")
parser.add_argument("-n", "--new",
                    action="store_true", help="Create a new PyUnity project")
parser.add_argument("project", help="Path to PyUnity project")
args = parser.parse_args()

def check():
    if len(sys.argv) < 2:
        print("Please specify a project.")
        return False
    elif not os.path.isdir(args.project):
        print("Please specify a valid directory.")
        return False
    return True

def run():
    from .app import Application
    app = Application(args.project)
    app.start()

def main():
    if not check():
        return
    start(run)

def gui():
    if not args.new and not os.path.isdir(args.project):
        raise Exception("Project not found")

    def inner():
        temp_stream = io.StringIO()
        redirect_out(temp_stream)

        from pyunity import Logger, SceneManager, Loader
        if args.new:
            SceneManager.AddScene("Scene")
            Loader.GenerateProject(args.project)
            SceneManager.RemoveAllScenes()

        directory = os.path.join(os.path.dirname(Logger.folder), "Editor", "Logs")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, strftime("%Y-%m-%d %H-%M-%S") + ".log")
        f = open(path, "w+", buffering=1)

        temp_stream.seek(0)
        f.write(temp_stream.read())
        temp_stream.close()
        redirect_out(f)
        Logger.SetStream(f)
        run()
    start(inner)
