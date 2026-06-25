"""Работа со строками"""
import typing


def list2str(a: typing.Iterable[str]):
  """Преобразовать каждый элемент списка в строку"""
  return [str(i) for i in a]


def dict2str(a: dict) -> dict:
  """Преобразовать каждое значение словаря в строку"""
  b = {}
  for key, value in a.items():
    b[key] = str(value)
  return b


class replace:
  """Функции для замены текста"""
  @classmethod
  def multi(cls, text: str, d: dict = None, **kw) -> str:
    """Мульти-замена {"что заменить":"чем заменить"}"""
    if not d is None:
      kw.update(d)
    t = str(text)
    for k, v in d.items():
      t = t.replace(k, str(v))
    return t

  @classmethod
  def all(cls, text: str, fr: str, to: str) -> str:
    """Замена пока заменяемый текст не исчезнет"""
    t = str(text)
    a = str(fr)
    b = str(to)
    if a in b:
      raise RecursionError('%r is contained in %r, this causes an infinite loop' % (a, b))
    while a in t:
      t = t.replace(a, b)
    return t


def join_list(lst: typing.Iterable[str], midsep=", ", lastsep=" и "):
  """Объединить список в строку с отличающимся последним разделителем"""
  lst = [str(i) for i in lst]
  if len(lst) < 3:
    return lastsep.join(lst)
  return midsep.join(lst[:-1]) + lastsep + lst[-1]
