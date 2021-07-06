import os
import tkinter
import time
import threading

def main():
    from editor.app import Application
    app = Application("Test")
    app.start()

def splash():
    a = tkinter.Tk()
    while True:
        if os.getenv("PYUNITY_EDITOR_LOADED") == "1":
            break
        a.update()
        time.sleep(0.2)
    a.destroy()

def start(func, args=[], kwargs={}):
    t = threading.Thread(target=splash)
    t.start()
    func(*args, **kwargs)

start(main)