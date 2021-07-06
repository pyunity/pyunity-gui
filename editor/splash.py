import os
import tkinter
import time
import threading
import builtins
import sys
from PIL import ImageTk, Image

_print = builtins.print
sys._stderr = sys.stderr

def disable_print():
    def wrapper(*args, **kwargs):
        pass
    builtins.print = wrapper
    sys.stderr = os.devnull

def enable_print():
    builtins.print = _print
    sys.stderr = sys._stderr

def splash():
    root = tkinter.Tk()
    root.overrideredirect(1)
    root.attributes("-topmost", True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (256 / 2))
    y = int((screen_height / 2) - (256 / 2))
    root.geometry("256x256+" + str(x) + "+" + str(y))

    canvas = tkinter.Canvas(root, width=256, height=256,
        bd=0, highlightthickness=0, relief='ridge')
    canvas.pack()
    img = ImageTk.PhotoImage(Image.open("../pyunity.png").resize((256, 256)))
    canvas.create_image(0, 0, anchor=tkinter.NW, image=img)
    while True:
        if os.getenv("PYUNITY_EDITOR_LOADED") == "1":
            break
        root.update()
        time.sleep(0.2)
    root.destroy()

def start(func, args=[], kwargs={}):
    t = threading.Thread(target=splash)
    t.start()
    func(*args, **kwargs)
