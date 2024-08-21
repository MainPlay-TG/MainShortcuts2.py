import re
from .core import ms
from typing import *
# 2.0.0


def filter(a: list, whitelist: list = None, blacklist: list = [], regex: str = False, begin: str = None, end: str = None):
  """Фильтровать список
  whitelist - удалить всё, чего нет в этом списке
  blacklist - удалить всё, что есть в этом списке
  regex - сортировка с регулярным выражением (строки)"""
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
  """Удалить дублирующиеся элементы
  trim - True: использовать strip()
         l: использовать lstrip()
         r: использовать rstrip()
  case - lower/upper/capitalize
  func - обработать каждый элемент этой функцией"""
  b = []
  trim = str(trim).lower()
  case = str(case).lower()
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
    if not i in b:
      b.append(i)
  return b
