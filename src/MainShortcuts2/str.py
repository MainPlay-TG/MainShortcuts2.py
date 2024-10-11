"""Работа со строками"""
from .core import ms
from typing import *


def list2str(a: Union[Iterable]) -> list:
  """Преобразовать каждый элемент списка в строку"""
  b = []
  for i in a:
    b.append(str(i))
  return b


def dict2str(a: dict) -> dict:
  """Преобразовать каждое значение словаря в строку"""
  b = {}
  for key, value in a.items():
    b[key] = str(value)
  return b


class _Replace:
  """Функции для замены текста"""

  def __init__(self):
    pass

  def multi(self, text: str, d: dict = None, **kw) -> str:
    """Мульти-замена {"что заменить":"чем заменить"}"""
    if not d is None:
      kw.update(d)
    t = str(text)
    for k, v in d.items():
      t = t.replace(k, str(v))
    return t

  def all(self, text: str, fr: str, to: str) -> str:
    """Замена пока заменяемый текст не исчезнет"""
    t = str(text)
    a = str(fr)
    b = str(to)
    if a in b:
      raise RecursionError('%r is contained in %r, this causes an infinite loop' % (a, b))
    while a in t:
      t = t.replace(a, b)
    return t


replace = _Replace()
