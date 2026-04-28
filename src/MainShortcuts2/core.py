import os
import sys
from . import _module_info
from datetime import datetime
from functools import cached_property
from logging import Logger
from time import time
try:
  from datetime import timezone
except Exception:
  timezone = None


def _get_main_file():
  def func():
    if getattr(sys, "frozen", False):
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
               logger: Logger = None,
               **kw):
    self.args = sys.argv
    self.encoding: str = "utf-8"
    self.env = os.environ
    self.import_code = "from MainShortcuts2 import ms"
    self.log: Logger = NoLogger("MainShortcuts2") if logger is None else logger
    self.MAIN_FILE: str | None = _get_main_file()
    self.MAIN_DIR: str | None = None if self.MAIN_FILE is None else os.path.dirname(self.MAIN_FILE)
    self.use_tmp_file = True
    self.reload()

  def reload(self):
    self.pid = os.getpid()

  @cached_property
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

  @cached_property
  def advanced(self):
    from . import advanced
    return advanced

  @cached_property
  def any2json(self):
    from . import any2json
    return any2json

  @cached_property
  def cfg(self):
    from .cfg import cfg
    return cfg

  @cached_property
  def dict(self):
    from . import dict
    return dict

  @cached_property
  def dir(self):
    from . import dir
    return dir

  @cached_property
  def file(self):
    from . import file
    return file

  @cached_property
  def json(self):
    from . import json
    return json

  @cached_property
  def list(self):
    from . import list
    return list

  @cached_property
  def ms2app(self):
    from . import ms2app
    return ms2app

  @cached_property
  def ms2hash(self):
    from . import ms2hash
    return ms2hash

  @cached_property
  def path(self):
    from . import path
    return path

  @cached_property
  def proc(self):
    from . import proc
    return proc

  @cached_property
  def regex(self):
    from . import regex
    return regex

  @cached_property
  def special_chars(self):
    from . import special_chars
    return special_chars

  @cached_property
  def str(self):
    from . import str
    return str

  @cached_property
  def term(self):
    from . import term
    return term

  @cached_property
  def types(self):
    from . import types
    return types

  @cached_property
  def utils(self):
    from . import utils
    return utils

  @cached_property
  def win(self):
    from . import win
    return win

  class ObjectBase(object):
    def __new__(cls, *a, **b):
      self = object.__new__(cls)
      return self

    def __init__(self, *a, **b):
      pass

    def __bool__(self):
      return True

    def __enter__(self):
      return self

    def __exit__(self, *a):
      if callable(getattr(self, "close", None)):
        self.close()

    def __repr__(self, args_string="..."):
      cls = type(self)
      return "%s.%s(%s)" % (cls.__module__, cls.__name__, args_string)

    @classmethod
    def _from_kw(cls, kw):
      return cls(**kw)

  @property
  def now(self):
    """Текущее локальное время (`timestamp`)"""
    return time()

  @property
  def now_dt(self):
    """Текущее локальное время (`datetime`)"""
    return datetime.fromtimestamp(time())

  @property
  def utcnow(self):
    """Текущее время по UTC (`timestamp`)"""
    return self.utcnow_dt.timestamp()
  if timezone is None:
    @property
    def utcnow_dt(self):
      """Текущее время по UTC (`datetime`)"""
      return datetime.utcfromtimestamp(time())
  else:
    @property
    def utcnow_dt(self):
      """Текущее время по UTC (`datetime`)"""
      return datetime.fromtimestamp(time(), timezone.utc)

  @cached_property
  def ms2dat_v1(self):
    from . import ms2dat1
    return ms2dat1

  @cached_property
  def ms2dat(self):
    """Авто выбор при загрузке, последняя версия при сохранении"""
    from . import _ms2dat_auto
    return _ms2dat_auto


ms = MS2()
