"""Различные объекты, которые не имеют функционала"""


class Base:
  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    self.type = type(self)


class AccessDeniedError(UserError):
  pass
  """Ошибка доступа"""


class Empty(Base):
  pass
  """Пустота (не равно `None`)"""


class Infinity(Base):
  pass
  """Бесконечное число"""


class NotAFileError(Exception):
  pass
  """Ошибка 'это не файл'"""


class NotANumber(Base):
  pass
  """Не число"""


class NotFound(Base):
  pass
  """Не найдено"""


class NotFoundError(Exception):
  pass
  """Ошибка 'не найдено'"""


class UserError(Exception):
  pass
  """Ошибка, которую допустил пользователь. Например неправильно указал входные данные"""


Error401 = AccessDeniedError
Error403 = AccessDeniedError
Error404 = NotFoundError
Inf = Infinity
NaN = NotANumber
