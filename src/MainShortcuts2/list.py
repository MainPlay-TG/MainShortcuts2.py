"""Работа со списками"""
import re
from .core import ms
from typing import *


def filter(a: list, whitelist: list = None, blacklist: list = [], regex: str = False, begin: str = None, end: str = None):
  """Фильтровать список"""
  a = list(a)
  if whitelist == None:
    whitelist = a
  if type(whitelist) == str:
    whitelist = [whitelist]
  if type(blacklist) == str:
    blacklist = [blacklist]
  b = []
  for i in a:
    add = True
    if begin != None:
      if str(i).startswith(str(begin)):
        add = True
      else:
        add = False
    if end != None and add:
      if str(i).endswith(str(end)):
        add = True
      else:
        add = False
    if regex and add:
      reW = False
      for i2 in whitelist:
        if re.match(str(i2), str(i)) != None:
          reW = True
          break
      reB = False
      for i2 in blacklist:
        if re.match(str(i2), str(i)) != None:
          reB = True
          break
      if reW and not reB:
        add = True
      else:
        add = False
    if add and not regex:
      if (i in whitelist) and (not i in blacklist):
        add = True
      else:
        add = False
    if add:
      b.append(i)
  return b


def rm_duplicates(a: list, trim: bool = False, case: bool = False, func=lambda i: i):
  """Удалить дублирующиеся элементы"""
  b = set()
  case = str(case).lower()
  trim = str(trim).lower()
  for i in a:
    if trim in ["true", "lr", "rl", "all"]:
      i = i.strip()
    elif trim in ["l", "left"]:
      i = i.lstrip()
    elif trim in ["r", "right"]:
      i = i.rstrip()
    if case in ["l", "lower", "low"]:
      i = i.lower()
    elif case in ["u", "upper", "up"]:
      i = i.upper()
    elif case in ["capitalize", "cap"]:
      i = i.capitalize()
    i = func(i)
    b.add(i)
  return list(b)


def split_evenly_iter(lst: list, n: int):
  """Разделить список на N почти равных частей (итератор)"""
  part_size = len(lst) // n
  remainder = len(lst) % n
  start_idx = 0
  for i in range(n):
    end_idx = start_idx + part_size
    if i < remainder:
      end_idx += 1
    yield lst[start_idx:end_idx]
    start_idx = end_idx


def split_evenly(lst: list, n: int):
  """Разделить список на N почти равных частей"""
  return list(split_evenly_iter(lst, n))


def split_fixed_iter(lst: list, n: int):
  """Разделить список на N равных частей с остатком (итератор)"""
  part_size = len(lst) // n
  start_idx = 0
  for i in range(n):
    end_idx = start_idx + part_size
    yield lst[start_idx:end_idx]
    start_idx = end_idx
  yield lst[end_idx:]


def split_fixed(lst: list, n: int):
  """Разделить список на N равных частей с остатком"""
  return list(split_fixed_iter(lst, n))
