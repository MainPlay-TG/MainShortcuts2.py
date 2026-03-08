import sys
from argparse import ArgumentParser
from logging import getLogger, Logger
from MainShortcuts2 import ms
from MainShortcuts2.utils import mini_log
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
S_B = 1
S_KB = S_B
S_MB = S_KB * 1024
S_GB = S_MB * 1024
S_TB = S_GB * 1024


def humanize_filesize(size: int):
  if S_KB > size:
    return f"{size} B"
  if S_MB > size:
    return f"{size / S_KB:.2f} KB"
  if S_GB > size:
    return f"{size / S_MB:.2f} MB"
  if S_TB > size:
    return f"{size / S_GB:.2f} GB"
  return f"{size / S_TB:.2f} TB"


class QApplication(QtWidgets.QApplication):
  def __init__(self, *a, **kw):
    super().__init__(*a, **kw)
    self.logger = getLogger(type(self).__name__)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_val is not None:
      self.logger.exception("Unhandled exception", exc_info=exc_val)


def main_func(_name_):
  def deco(func):
    if _name_ != "__main__":
      return func

    def wrapper(*args, **kwargs):
      with QApplication(sys.argv) as app:
        kwargs["qapp"] = app
        func(*args, **kwargs)
        sys.exit(app.exec())
    return wrapper
  return deco
