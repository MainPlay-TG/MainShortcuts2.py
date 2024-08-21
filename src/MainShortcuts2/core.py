import os
import sys
from logging import Logger
# 2.0.0


class NoLogger:
  def __init__(*a, **b):
    pass

  def __getattr__(self, k):
    return lambda *a, **b: None


class MS2:
  def __init__(self, *,
               __file__: str = None,
               __name__: str = None,
               logger: Logger = None,
               **kw):
    self._cfg = None
    self._dict = None
    self._dir = None
    self._file = None
    self._json = None
    self._list = None
    self._path = None
    self._proc = None
    self._str = None
    self._term = None
    self._utils = None
    self._win = None
    self.encoding = "utf-8"
    self.env = os.environ
    self.log: Logger = NoLogger() if logger is None else logger
    self.prog_file = __file__
    self.prog_name = __name__
    self.reload()

  def reload(self):
    self.args = sys.argv
    self.import_code = "from MainShortcuts2 import ms\nms.prog_file,ms.prog_name=__file__,__name__\nms.reload()"
    self.imported = self.prog_name != "__main__"
    self.pid = os.getpid()
    self.prog_dir = os.path.dirname(self.prog_file)
    self.running = self.prog_name == "__main__"

  @property
  def cfg(self):
    if self._cfg is None:
      from .cfg import cfg
      self._cfg = cfg
      self._cfg.ms = self
    return self._cfg

  @property
  def dict(self):
    if self._dict is None:
      from . import dict
      self._dict = dict
      self._dict.ms = self
    return self._dict

  @property
  def dir(self):
    if self._dir is None:
      from . import dir
      self._dir = dir
      self._dir.ms = self
    return self._dir

  @property
  def file(self):
    if self._file is None:
      from . import file
      self._file = file
      self._file.ms = self
    return self._file

  @property
  def json(self):
    if self._json is None:
      from . import json
      self._json = json
      self._json.ms = self
    return self._json

  @property
  def list(self):
    if self._list is None:
      from . import list
      self._list = list
      self._list.ms = self
    return self._list

  @property
  def path(self):
    if self._path is None:
      from . import path
      self._path = path
      self._path.ms = self
    return self._path

  @property
  def proc(self):
    if self._proc is None:
      from . import proc
      self._proc = proc
      self._proc.ms = self
    return self._proc

  @property
  def str(self):
    if self._str is None:
      from . import str
      self._str = str
      self._str.ms = self
    return self._str

  @property
  def term(self):
    if self._term is None:
      from . import term
      self._term = term
      self._term.ms = self
    return self._term

  @property
  def utils(self):
    if self._utils is None:
      from . import utils
      self._utils = utils
      self._utils.ms = self
    return self._utils

  @property
  def win(self):
    if self._win is None:
      from . import win
      self._win = win
      self._win.ms = self
    return self._win
