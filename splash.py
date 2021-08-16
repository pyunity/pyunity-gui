import sys
sys.argv.append("Test")

from editor.splash import start

def main():
    from editor.app import Application
    app = Application("Test")
    app.start()

start(main)