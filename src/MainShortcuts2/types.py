"""Различные объекты, которые не имеют функционала"""


class Base:
  def __init__(self):
    self.type = type(self)


class UserError(Exception):
  """Ошибка, которую допустил пользователь. Например неправильно указал входные данные"""


class Empty(Base):
  pass


class Infinity(Base):
  pass


class NotANumber(Base):
  pass


class NotFound(Base):
  pass


Inf = Infinity
NaN = NotANumber
