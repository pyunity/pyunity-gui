import os
import time
import threading
import sys

def redirect_out(stream):
    sys.stdout = stream
    sys.stderr = stream

def restore_out():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

def splash():
    import tkinter
    from PIL import ImageTk, Image
    root = tkinter.Tk()
    root.overrideredirect(1)
    root.attributes("-topmost", True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    size = int(screen_height // 2)
    x = int((screen_width / 2) - (size / 2))
    y = int((screen_height / 2) - (size / 2))
    root.geometry(str(size) + "x" + str(size) + "+" + str(x) + "+" + str(y))

    canvas = tkinter.Canvas(root, width=size, height=size,
        bd=0, highlightthickness=0, relief='ridge')
    canvas.pack()
    splash_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "splash.png")
    img = ImageTk.PhotoImage(Image.open(splash_img).resize((size, size)))
    canvas.create_image(0, 0, anchor=tkinter.NW, image=img)
    while True:
        if os.getenv("PYUNITY_EDITOR_LOADED") == "1":
            break
        root.update()
        time.sleep(0.2)
    root.destroy()

def start(func, args=[], kwargs={}):
    t = threading.Thread(target=splash)
    t.daemon = True
    t.start()
    func(*args, **kwargs)
