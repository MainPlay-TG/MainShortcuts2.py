import subprocess
import os
from PIL import Image
def _sudo(*args:str):
  return ["su","-c",*args]
def screenshot_png(path:str)
  subprocess.run(_sudo("screencap","-p",os.path.realpath(path),check=True))
def screenshot_pil():
  with subprocess.Popen(_sudo("screencap","-p"),stdout=subprocess.PIPE) as p:
    img=Image.open(p.stdout)
    img.load()
    p.wait()
  return img