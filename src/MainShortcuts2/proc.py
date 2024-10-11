"""Работа с процессами"""
import subprocess
from .core import ms
from functools import wraps
from typing import *
Popen_kw = {
    "stderr": subprocess.PIPE,
    "stdin": subprocess.PIPE,
    "stdout": subprocess.PIPE,
}


@wraps(subprocess.Popen)
def Popen(*args, **kw) -> subprocess.Popen:
  """Запустить процесс"""
  for i in Popen_kw:
    if not i in kw:
      kw[i] = Popen_kw[i]
  kw["args"] = list(args)
  p = subprocess.Popen(**kw)
  return p


@wraps(subprocess.Popen)
def call(*args, **kw) -> subprocess.Popen:
  """Запустить процесс и ожидать его завершения"""
  p = Popen(*args, **kw)
  p.wait()
  return p
