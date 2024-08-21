import os
import subprocess
import sys
from .core import ms
from functools import wraps
from typing import *
# 2.0.0
Popen_kw = {
    "stderr": subprocess.PIPE,
    "stdin": subprocess.PIPE,
    "stdout": subprocess.PIPE,
}


@wraps(subprocess.Popen)
def Popen(*args, **kw) -> subprocess.Popen:
  for i in Popen_kw:
    if not i in kw:
      kw[i] = Popen_kw[i]
  kw["args"] = list(args)
  p = subprocess.Popen(**kw)
  return p


@wraps(subprocess.Popen)
def call(*args, **kw) -> subprocess.Popen:
  p = Popen(*args, **kw)
  p.wait()
  return p
