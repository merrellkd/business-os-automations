# utils/filesystem.py
import os, shutil

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def move_file(src, dst):
    shutil.move(src, dst)

def create_file(path, content=""):
    with open(path, "w") as f:
        f.write(content)
