from .splash import start, redirect_out
from time import strftime
import argparse
import os
import io

parser = argparse.ArgumentParser(
    prog="editor", description="Launch the PyUnity editor")
parser.add_argument("-n", "--new",
                    action="store_true", help="Create a new PyUnity project")
parser.add_argument("project", help="Path to PyUnity project")

def check(args):
    if not os.path.isdir(args.project):
        print("Please specify a valid directory.")
        return False
    return True

def run(args=None):
    if args is None:
        args = parser.parse_args()
        if not check(args):
            return
        if not args.new and not os.path.isdir(args.project):
            raise Exception("Project not found")

    from pyunity import SceneManager, Loader
    if args.new:
        SceneManager.AddScene("Scene")
        Loader.GenerateProject(args.project)
        SceneManager.RemoveAllScenes()

    from .app import Application
    app = Application(args.project)
    app.start()

def main():
    args = parser.parse_args()
    if not check(args):
        return
    if not args.new and not os.path.isdir(args.project):
        raise Exception("Project not found")
    start(run, [args])

def gui():
    args = parser.parse_args()
    if not check(args):
        return
    if not args.new and not os.path.isdir(args.project):
        raise Exception("Project not found")

    def inner():
        temp_stream = io.StringIO()
        redirect_out(temp_stream)

        from pyunity import Logger
        directory = os.path.join(os.path.dirname(Logger.folder), "Editor", "Logs")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, strftime("%Y-%m-%d %H-%M-%S") + ".log")
        f = open(path, "w+", buffering=1)

        temp_stream.seek(0)
        f.write(temp_stream.read())
        temp_stream.close()
        redirect_out(f)
        Logger.SetStream(f)
        run(args)
    start(inner)
