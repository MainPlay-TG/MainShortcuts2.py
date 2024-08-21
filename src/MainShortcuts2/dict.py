from .core import MS2
from typing import *
ms: MS2 = None
# 2.0.0


def merge(old: dict, new: dict) -> dict:
  """Рекурсиво объединить словари"""
  out = old.copy()
  for k, v in new.items():
    if k in out:
      if type(out[k]) == dict and type(v) == dict:
        out[k] = merge(out[k], v)
      else:
        out[k] = v
    else:
      out[k] = v
  return out


def reverse(d: dict) -> dict:
  """Развернуть порядок ключей"""
  keys = list(d.keys())[::-1]
  r = {}
  for k in keys:
    r[k] = d[k]
  return r


def sort(d: dict, *, key: None = None, reverse: bool = False) -> dict:
  """Сортировать порядок ключей"""
  keys = list(d.keys)
  keys.sort(key=key, reverse=reverse)
  r = {}
  for k in keys:
    r[k] = d[k]
  return r


def swap(d: dict) -> dict:
  """Вывернуть словарь (повторяющиеся значения будут перезаписаны)"""
  r = {}
  for k, v in d.items():
    r[v] = k
  return r
