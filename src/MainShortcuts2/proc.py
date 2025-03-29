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


class Popen(subprocess.Popen):
  def __init__(self, *args, **kw):
    if len(args) == 1:
      if isinstance(args[0], (list, tuple)):
        args = args[0]
    for k, v in Popen_kw.items():
      kw.setdefault(k, v)
    kw["args"] = list(args)
    self.launch_kw = kw
    subprocess.Popen.__init__(self, **kw)

  def force_wait(self):
    """Ожидать завершения процесса игнорируя прерывания"""
    while True:
      try:
        return self.wait()
      except:
        pass

  @ms.utils.riot(daemon=True)
  def wait_on_bg(self):
    """Ожидать завершения процесса в фоне (для Linux)"""
    self.force_wait()


@wraps(subprocess.Popen)
def call(*args, **kw) -> subprocess.Popen:
  """Запустить процесс и ожидать его завершения"""
  p = Popen(*args, **kw)
  p.wait()
  return p
