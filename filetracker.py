import os, glob

directory = "editor"
files = set(glob.glob(os.path.join(directory, "**/*"), recursive=True))
times = {file: os.stat(file)[8] for file in files}
try:
    while True:
        files2 = set(glob.glob(os.path.join(directory, "**/*"), recursive=True))
        for file in files:
            if file not in files2:
                print("Removed " + file)
            elif times[file] < os.stat(file)[8]:
                print("Modified " + file)
                times[file] = os.stat(file)[8]
        for file in files2 - files:
            print("Created " + file)
            times[file] = os.stat(file)[8]
        files = files2
except KeyboardInterrupt:
    pass
