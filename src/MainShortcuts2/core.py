import os
import sys
from . import _module_info
from logging import Logger
# 2.0.0


class NoLogger:
  def __init__(*a, **b):
    pass

  def __getattr__(self, k):
    return lambda *a, **b: None


class MS2:
  version = _module_info.version

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
    self._types = None
    self._utils = None
    self._win = None
    self.args = sys.argv
    self.encoding = "utf-8"
    self.env = os.environ
    self.import_code = "from MainShortcuts2 import ms\nms.prog_file,ms.prog_name=__file__,__name__\nms.reload()"
    self.log: Logger = NoLogger() if logger is None else logger
    self.prog_file = __file__
    self.prog_name = __name__
    self.reload()

  def reload(self):
    self.pid = os.getpid()
    if not self.prog_file is None:
      self.prog_dir = os.path.dirname(self.prog_file)
    if not self.prog_name is None:
      self.imported = self.prog_name != "__main__"
      self.running = self.prog_name == "__main__"

  @property
  def credits(self) -> str:
    line = "------------------------------------------------"
    l = []
    l.append(line)
    l.append(("MainShortcuts2 %s" % self.version).center(len(line)))
    l.append("https://github.com/MainPlay-TG/MainShortcuts2.py")
    l.append(line)
    l.append("Разработчик: MainPlay TG")
    l.append("- Telegram - https://t.me/MainPlay_TG")
    l.append("- GitHub - https://github.com/MainPlay-TG")
    l.append("- Пожертвования - https://www.donationalerts.com/r/mainplay_tg (не знаю зачем, всё равно никто и копейки не даст)")
    l.append(line)
    l.append("Тестеры:")
    l.append("- MainPlay TG (https://t.me/MainPlay_TG)")
    l.append("- Кларк (https://t.me/Klark_Anthrofox)")
    l.append("- FOX (https://t.me/black_fox404)")
    l.append("- Ты (напиши мне в Telegram и в ближайшем обновлении тут будет твоя ссылка)")
    l.append(line)
    l.append("Спасибо за использование моей библиотеки".center(len(line)))
    return "\n".join(l)

  @property
  def cfg(self):
    if self._cfg is None:
      from .cfg import cfg
      self._cfg = cfg
    return self._cfg

  @property
  def dict(self):
    if self._dict is None:
      from . import dict
      self._dict = dict
    return self._dict

  @property
  def dir(self):
    if self._dir is None:
      from . import dir
      self._dir = dir
    return self._dir

  @property
  def file(self):
    if self._file is None:
      from . import file
      self._file = file
    return self._file

  @property
  def json(self):
    if self._json is None:
      from . import json
      self._json = json
    return self._json

  @property
  def list(self):
    if self._list is None:
      from . import list
      self._list = list
    return self._list

  @property
  def path(self):
    if self._path is None:
      from . import path
      self._path = path
    return self._path

  @property
  def proc(self):
    if self._proc is None:
      from . import proc
      self._proc = proc
    return self._proc

  @property
  def str(self):
    if self._str is None:
      from . import str
      self._str = str
    return self._str

  @property
  def term(self):
    if self._term is None:
      from . import term
      self._term = term
    return self._term

  @property
  def types(self):
    if self._types is None:
      from . import types
      self._types = types
    return self._types

  @property
  def utils(self):
    if self._utils is None:
      from . import utils
      self._utils = utils
    return self._utils

  @property
  def win(self):
    if self._win is None:
      from . import win
      self._win = win
    return self._win


ms = MS2()
