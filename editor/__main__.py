from .app import Application
def main():
    app = Application("Test")
    app.start()

def start_splash():
    from .splash import start
    start(main)

if __name__ == "__main__":
    main()
