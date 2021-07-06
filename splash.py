loaded = []

def main():
    global loaded
    from editor.app import Application
    app = Application("Test")
    app.start(loaded)

def splash():
    import tkinter, time
    a = tkinter.Tk()
    while True:
        if len(loaded):
            break
        a.update()
        time.sleep(0.1)
    a.destroy()

import threading
t = threading.Thread(target=splash)
t.start()

main()