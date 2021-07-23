from .splash import start

def main():
    from .app import Application
    app = Application("Test")
    app.start()

def run():
    start(main)
