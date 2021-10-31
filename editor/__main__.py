from .app import Application
import sys

def main():
    app = Application(sys.argv[1])
    app.start()

if __name__ == "__main__":
    main()
