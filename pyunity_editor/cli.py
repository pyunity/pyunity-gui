from .splash import start
from .local import fixPackage, redirect_out, restore_out
from time import strftime
import argparse
import sys
import os
import io

class Parser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        kwargs["prog"] = os.path.basename(sys.argv[0])
        if kwargs["prog"] == "__main__.py":
            kwargs["prog"] = "editor"
        super(Parser, self).__init__(**kwargs)
        self.add_argument("-n", "--new",
                            action="store_true", help="Create a new PyUnity project")
        self.add_argument("-S", "--no-splash", action="store_false", dest="splash",
                            help="Disable the splash image on launch")
        self.add_argument("project", help="Path to PyUnity project", nargs="?")
        self.gui = False

    def parse_args(self, args=None, namespace=None):
        args = super(Parser, self).parse_args(args, namespace)
        if args.project is None:
            restore_out()
            self.print_help()
            self.exit(0)
        if not args.new and not os.path.isdir(args.project):
            if self.gui:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, "Project not found", "Help", 0x10)
                self.exit(1)
            else:
                raise Exception("Project not found")
        return args

    def print_help(self):
        if self.gui:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, self.format_help(), "Help", 0x40)
        else:
            print(self.format_help())

    def error(self, message):
        msg = f"{self.prog}: error: {message}"
        if self.gui:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "Error", 0x10)
        else:
            self.print_usage(sys.stderr)
            sys.stderr.write(msg + "\n")
        self.exit(2)

parser = Parser(description="Launch the PyUnity editor")

def run(args=None):
    if args is None:
        args = parser.parse_args()

    fixPackage()
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
    if args.splash:
        start(run, args=[args])
    else:
        run(args)

def gui():
    parser.gui = True
    args = parser.parse_args()

    def inner():
        temp_stream = io.StringIO()
        redirect_out(temp_stream)
        from pyunity import Logger
        Logger.SetStream(temp_stream)
        fixPackage()

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
    if args.splash:
        start(inner)
    else:
        inner()
