import os
import sys
from . import _module_info
from logging import Logger
from typing import Union


def _get_main_file():
  def func():
    if hasattr(sys, "frozen"):
      if sys.frozen:
        return sys.executable
    if "__main__" in sys.modules:
      if hasattr(sys.modules["__main__"], "__file__"):
        return sys.modules["__main__"].__file__
  result = func()
  if result is None:
    return
  return os.path.abspath(result).replace("\\", "/")


class NoLogger(Logger):
  def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
    pass


class MS2:
  version = _module_info.version

  def __init__(self, *,
               __file__: str = None,
               __name__: str = None,
               logger: Logger = None,
               **kw):
    self._advanced = None
    self._any2json = None
    self._cfg = None
    self._dict = None
    self._dir = None
    self._file = None
    self._json = None
    self._list = None
    self._path = None
    self._proc = None
    self._regex = None
    self._special_chars = None
    self._str = None
    self._term = None
    self._types = None
    self._utils = None
    self._win = None
    self.args: list[str] = sys.argv
    self.encoding: str = "utf-8"
    self.env: dict[str, str] = os.environ
    self.import_code: str = "from MainShortcuts2 import ms\nms.prog_file,ms.prog_name=__file__,__name__\nms.reload()"
    self.log: Logger = NoLogger("MainShortcuts2") if logger is None else logger
    self.MAIN_FILE: Union[None, str] = _get_main_file()
    self.MAIN_DIR: Union[None, str] = None if self.MAIN_FILE is None else os.path.dirname(self.MAIN_FILE)
    self.prog_dir: Union[None, str] = None
    self.prog_file: Union[None, str] = __file__
    self.prog_name: Union[None, str] = __name__
    self.use_tmp_file: bool = False
    self.reload()

  def reload(self):
    self.pid = os.getpid()
    if not self.prog_file is None:
      self.prog_dir = os.path.dirname(self.prog_file)
    if not self.prog_name is None:
      self.imported: bool = self.prog_name != "__main__"
      self.running: bool = self.prog_name == "__main__"

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
  def advanced(self):
    if self._advanced is None:
      from . import advanced
      self._advanced = advanced
    return self._advanced

  @property
  def any2json(self):
    if self._any2json is None:
      from . import any2json
      self._any2json = any2json
    return self._any2json

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
  def regex(self):
    if self._regex is None:
      from . import regex
      self._regex = regex
    return self._regex

  @property
  def special_chars(self):
    if self._special_chars is None:
      from . import special_chars
      self._special_chars = special_chars
    return self._special_chars

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
