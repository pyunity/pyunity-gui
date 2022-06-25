from PIL import Image
import glob
import os

orig = os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
imgs = []
root = None
for file in glob.glob("editor\\icons\\window\\icon*.png"):
    img = Image.open(file)
    if "256" in file:
        root = img
    else:
        imgs.append(img)
root.save("icons.ico", format="ICO", append_images=imgs)
os.chdir(orig)
