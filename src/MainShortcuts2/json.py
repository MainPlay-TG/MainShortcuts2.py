"""Работа с JSON"""
import json
import builtins
from .core import ms
from .path import PATH_TYPES
from typing import *
try:
  import json5
except Exception:
  json5 = None
JSON_TYPES = Union[bool, dict, float, int, list, None, str]


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
  if "sort" in kw:
    kw["sort_keys"] = kw.pop("sort")
  if mode in ["c", "compress", "min", "zip"]:  # Сжатый
    kw["indent"] = None
    kw["separators"] = [",", ":"]
  if mode in ["p", "pretty", "max", "print"]:  # Развёрнутый
    if not "indent" in kw:
      kw["indent"] = 2
    kw["separators"] = None
  if mode in ["mp", "mp_tg", "mainplay", "mainplay_tg"]:  # Стиль MainPlay TG
    kw["indent"] = 2
    kw["separators"] = [",", ":"]
  return json.dumps(**kw)


def print(data: JSON_TYPES, **kw):
  """Напечатать данные в виде текстового JSON"""
  pr_kw = {}
  for i in ["end", "file", "flush", "sep"]:
    if i in kw:
      pr_kw[i] = kw.pop(i)
  kw["data"] = data
  kw["mode"] = mode
  if not "ensure_ascii" in kw:
    kw["ensure_ascii"] = False
  if not "mode" in kw:
    kw["mode"] = "p"
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
  for i in ["encoding", "force"]:
    if i in kw:
      f_kw[i] = kw.pop(i)
  f_kw["path"] = path
  f_kw["data"] = encode(**kw)
  return ms.file.write(**f_kw)
