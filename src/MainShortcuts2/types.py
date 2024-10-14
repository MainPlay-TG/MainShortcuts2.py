"""Различные объекты и исключения"""
from typing import Union


class Base:
  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    self.type = type(self)


class UserError(Exception):
  pass
  """Ошибка, которую допустил пользователь. Например неправильно указал входные данные"""


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


class Action:
  def __init__(self, func, *args, **kwargs):
    self._closed = False
    self._completed = False
    self._error = None
    self._launched = False
    self._result = None
    self.args: tuple = args
    self.func = func
    self.kwargs: dict = kwargs

  def __enter__(self):
    return self

  def __exit__(self, a, b, c):
    self.close()

  def _check(self, launched: bool = None, completed: bool = None, closed: bool = None):
    if not launched is None:
      if launched:
        if not self.launched:
          raise RuntimeError("The action has not yet been launched")
      else:
        if self.launched:
          raise RuntimeError("The action has already been launched")
    if not completed is None:
      if completed:
        if not self.completed:
          raise RuntimeError("The action has not yet been completed")
      else:
        if self.completed:
          raise RuntimeError("The action has already been completed")
    if not closed is None:
      if closed:
        if not self.closed:
          raise RuntimeError("The action has not yet been closed")
      else:
        if self.closed:
          raise RuntimeError("The action has already been closed")

  def close(self):
    self._closed = True
    self._error = None
    self._result = None
    self.args = None
    self.func = None
    self.kwargs = None

  @property
  def launched(self) -> bool:
    return self._launched

  @property
  def completed(self) -> bool:
    return self._completed

  @property
  def exception(self) -> Union[None, Exception]:
    self._check(launched=True, completed=True, closed=False)
    return self._error

  @property
  def result(self):
    self._check(launched=True, completed=True, closed=False)
    if not self._error is None:
      raise self._error  # type: ignore
    return self._result

  @property
  def closed(self) -> bool:
    return self._closed

  def run(self):
    self._check(launched=False, completed=False, closed=False)
    self._launched = True
    try:
      self._result = self.func(*self.args, **self.kwargs)  # type: ignore
    except Exception as err:
      self._error = err
    self._completed = True


class OnlyOneInstanceError(BaseException):
  """Ошибка для `.utils.OnlyOneInstance`"""

  def __init__(self, *args):
    if len(args) == 0:
      args = ("Another instance is already running",)
    BaseException.__init__(self, *args)


Error401 = AccessDeniedError
Error403 = AccessDeniedError
Error404 = NotFoundError
Inf = Infinity
NaN = NotANumber
