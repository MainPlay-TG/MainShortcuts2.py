"""Работа с JSON"""
import atexit
import builtins
import json
from .core import ms
from .path import PATH_TYPES
from typing import *
try:
  import json5
except Exception:
  json5 = None
JSON_TYPES = Union[bool, dict, float, int, list, None, str]
MODES = ["c", "compress", "mainplay_tg", "mainplay", "max", "min", "mp_tg", "mp", "p", "pretty", "print", "zip"]


def decode(text: str, *, like_json5: bool = False, **kw) -> JSON_TYPES:
  """Прочитать текстовый JSON"""
  kw["s"] = text
  if like_json5:
    if not json5 is None:
      return json5.loads(**kw)
  return json.loads(**kw)


def encode(data: JSON_TYPES, mode: str = "c", **kw):
  """Создать текстовый JSON"""
  kw["obj"] = data
  mode = mode.lower()
  if "force" in kw:
    del kw["force"]
    import warnings
    warnings.warn("The argument 'force' is no longer used", DeprecationWarning)
  if "sort" in kw:
    kw["sort_keys"] = kw.pop("sort")
  if mode in ["c", "compress", "min", "zip"]:  # Сжатый
    kw.setdefault("indent", None)
    kw.setdefault("separators", [",", ":"])
  if mode in ["p", "pretty", "max", "print"]:  # Развёрнутый
    kw.setdefault("indent", 2)
    kw.setdefault("separators", [",", ": "])
    if mode == "print":
      kw.setdefault("ensure_ascii", False)
  if mode in ["mp", "mp_tg", "mainplay", "mainplay_tg"]:  # Стиль MainPlay TG
    kw.setdefault("indent", 2)
    kw.setdefault("separators", [",", ":"])
  return json.dumps(**kw)


def print(data: JSON_TYPES, **kw):
  """Напечатать данные в виде текстового JSON"""
  pr_kw = {}
  for i in ["end", "file", "flush", "sep"]:
    if i in kw:
      pr_kw[i] = kw.pop(i)
  kw["data"] = data
  kw.setdefault("mode", "print")
  builtins.print(encode(**kw), **pr_kw)


def read(path: PATH_TYPES, **kw) -> JSON_TYPES:
  """Прочитать JSON файл"""
  f_kw = {}
  if "encoding" in kw:
    f_kw["encoding"] = kw.pop("encoding")
  f_kw["path"] = path
  kw["text"] = ms.file.read(**f_kw)
  return decode(**kw)


def rebuild(text: str, **kw) -> str:
  """Перестроить текстовый JSON"""
  de_kw = {}
  if "like_json5" in kw:
    de_kw["like_json5"] = kw.pop("like_json5")
  de_kw["text"] = text
  kw["data"] = decode(**de_kw)
  return encode(**kw)


def rewrite(path: PATH_TYPES, **kw) -> int:
  """Перестроить JSON файл"""
  de_kw = {}
  if "encoding" in kw:
    de_kw["encoding"] = kw["encoding"]
  if "like_json5" in kw:
    de_kw["like_json5"] = kw.pop("like_json5")
  de_kw["path"] = path
  kw["path"] = path
  kw["data"] = read(**de_kw)
  return write(**kw)


def write(path: PATH_TYPES, data: JSON_TYPES, **kw) -> int:
  """Прочитать JSON файл"""
  f_kw = {}
  kw["data"] = data
  for i in ["encoding", "force", "use_tmp_file"]:
    if i in kw:
      f_kw[i] = kw.pop(i)
  f_kw["path"] = path
  f_kw["data"] = encode(**kw)
  return ms.file.write(**f_kw)


class JsonFile:
  def __init__(self, path: str, autoload: bool = True, save_at_exit: bool = False, **kw):
    atexit.register(self.__exit__)
    self._data = None
    self._loaded = False
    self._path = None
    self.load_kw = {}
    self.save_kw = kw
    self.path = ms.path.Path(path)
    self.save_at_exit = save_at_exit
    if "like_json5" in self.save_kw:
      self.load_kw["like_json5"] = self.save_kw.pop("like_json5")
    if autoload:
      self.load()

  def __contains__(self, k) -> bool:
    return k in self.data

  def __delitem__(self, k):
    del self.data[k]

  def __enter__(self):
    return self

  def __exit__(self, *a):
    if self.save_at_exit:
      self.save()

  def __getitem__(self, k):
    return self.data[k]

  def __setitem__(self, k, v):
    self.data[k] = v

  @property
  def path(self) -> ms.path.Path:
    return self._path

  @path.setter
  def path(self, v):
    self._path = ms.path.Path(v)
    self.load_kw["path"] = self._path.path
    self.save_kw["path"] = self._path.path

  @property
  def data(self):
    if not self._loaded:
      self.load()
    return self._data

  @data.setter
  def data(self, v):
    self._data = v
    self._loaded = True

  def load(self):
    self._data = read(**self.load_kw)
    self._loaded = True

  def save(self):
    self.save_kw["data"] = self.data
    return write(**self.save_kw)
