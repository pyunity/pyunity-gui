import os
import time
import threading
import pkgutil
from .local import getPath

splashPath = getPath("icons/splash.png")

def tksplash():
    print("Loading tkinter splash image")
    import tkinter
    from PIL import ImageTk, Image
    img = ImageTk.PhotoImage(Image.open(splashPath).resize((size, size)))

    root = tkinter.Tk()
    root.overrideredirect(1)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    size = int(screen_height // 2)
    x = int(screen_width / 2 - size / 2)
    y = int(screen_height / 2 - size / 2)
    root.geometry(str(size) + "x" + str(size) + "+" + str(x) + "+" + str(y))

    canvas = tkinter.Canvas(root, width=size, height=size,
        bd=0, highlightthickness=0, relief="ridge")
    canvas.pack()
    canvas.create_image(0, 0, anchor=tkinter.NW, image=img)

    while True:
        if os.getenv("PYUNITY_EDITOR_LOADED") == "1":
            break
        root.update()
        time.sleep(0.2)
    root.destroy()

def sdlsplash():
    print("Loading SDL2 splash image")
    import warnings
    import ctypes

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        from sdl2.ext import Window
        from sdl2 import sdlimage
        import sdl2

    sdlimage.IMG_Init(sdlimage.IMG_INIT_PNG)
    img = sdlimage.IMG_Load(splashPath.encode())

    sdl2.ext.init()
    dispMode = sdl2.SDL_DisplayMode()
    sdl2.SDL_GetCurrentDisplayMode(0, ctypes.byref(dispMode))
    size = int(min(dispMode.w, dispMode.h) / 2)
    x = int(dispMode.w / 2 - size / 2)
    y = int(dispMode.h / 2 - size / 2)
    window = Window(
        "PyUnity Editor is loading...",
        (size, size),
        (x, y),
        sdl2.SDL_WINDOW_SHOWN
            | sdl2.SDL_WINDOW_BORDERLESS
            | sdl2.SDL_WINDOW_ALWAYS_ON_TOP
    )
    window.create()
    window.show()

    renderer = sdl2.SDL_CreateRenderer(window.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, img)

    event = sdl2.SDL_Event()
    while True:
        if os.getenv("PYUNITY_EDITOR_LOADED") == "1":
            break
        sdl2.SDL_WaitEvent(ctypes.byref(event))
        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_RenderCopy(renderer,
                            texture,
                            None,
                            None)
        sdl2.SDL_RenderPresent(renderer)
    sdl2.SDL_DestroyTexture(texture)
    sdl2.SDL_DestroyRenderer(renderer)
    window.close()

def splash():
    if pkgutil.find_loader("sdl2") is not None:
        sdlsplash()
    elif pkgutil.find_loader("tkinter") is not None:
        tksplash()
    else:
        print("Could not find splash screen window provider")

def start(func, args=[], kwargs={}):
    t = threading.Thread(target=splash)
    t.daemon = True
    t.start()
    func(*args, **kwargs)
