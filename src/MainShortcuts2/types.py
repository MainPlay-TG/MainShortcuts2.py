"""Различные объекты и исключения"""
from typing import Union


class Base:
  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    self.type = type(self)


class UserError(Exception):
  """Ошибка, которую допустил пользователь. Например неправильно указал входные данные"""
  pass


class AccessDeniedError(UserError):
  """Ошибка доступа"""


class Empty(Base):
  """Пустота (не равно `None`)"""

  def __bool__(self):
    return False


class Infinity(Base):
  """Бесконечное число"""

  def __bool__(self):
    return True


class NotAFileError(Exception):
  """Ошибка 'это не файл'"""


class NotANumber(Base):
  """Не число"""


class NotFound(Base):
  """Не найдено"""

  def __bool__(self):
    return False


class NotFoundError(Exception):
  """Ошибка 'не найдено'"""


class Action:
  """Запланированный запуск функции"""

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
    """Была ли запущена функция"""
    return self._launched

  @property
  def completed(self) -> bool:
    """Завершена ли функция"""
    return self._completed

  @property
  def exception(self) -> None | Exception:
    """Ошибка, возникшая при выполнении функции"""
    self._check(launched=True, completed=True, closed=False)
    return self._error

  @property
  def result(self):
    """Результат выполнения функции"""
    self._check(launched=True, completed=True, closed=False)
    if not self._error is None:
      raise self._error  # type: ignore
    return self._result

  @property
  def closed(self) -> bool:
    return self._closed

  def run(self):
    """Запустить функцию"""
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


class DotDict:
  def __init__(self, data: dict = None):
    self._data = {}
    for k in data:
      self[k] = data[k]

  def __delattr__(self, k: str):
    if k.startswith("_"):
      return object.__delattr__(self, k)
    del self.data[k]

  def __getattr__(self, k: str):
    if k.startswith("_"):
      return object.__getattr__(self, k)
    return self[k]

  def __setattr__(self, k: str, v):
    if k.startswith("_"):
      return object.__setattr__(self, k, v)
    self[k] = v

  def __contains__(self, k: str):
    return k in self._data

  def __delitem__(self, k: str):
    del self._data[k]

  def __getitem__(self, k: str):
    return self._data[k]

  def __setitem__(self, k: str, v):
    if "." in k:
      k, subk = k.split(".", 1)
      v = {subk: v}
    if isinstance(v, dict):
      v = type(self)(v)
    self._data[k] = v


class Color:
  """Значение цвета"""

  def __init__(self, *args,
               ahex: str = None,
               hex: str = None,
               hexa: str = None,
               rgb: tuple[int, int, int] = None,
               rgba: tuple[int, int, int, int] = None,
               ):
    self._init_complete = False
    self._readonly = False
    self._red = None
    self._green = None
    self._blue = None
    self._alpha = 255
    largs = len(args)
    if largs == 0:
      pass
    elif largs == 3:
      self._check_init()
      self.rgb = args
    elif largs == 4:
      self._check_init()
      self.rgba = args
    else:
      raise TypeError("Give from 3 to 4 positional arguments or 1 keyword argument")
    if not ahex is None:
      self._check_init()
      self.ahex = ahex
    if not hex is None:
      self._check_init()
      self.hex = hex
    if not hexa is None:
      self._check_init()
      self.hexa = hexa
    if not rgb is None:
      self._check_init()
      self.rgb = rgb
    if not rgba is None:
      self._check_init()
      self.rgba = rgba
    if not self._init_complete:
      raise TypeError("Give from 3 to 4 positional arguments or 1 keyword argument")

  def __repr__(self):
    cls = type(self)
    return "%s.%s(rgba=%r)" % (cls.__module__, cls.__name__, self.rgba)

  @property
  def red(self) -> int:
    """Уровень красного от 0 до 255"""
    return self._red

  @red.setter
  def red(self, v):
    self._check_ro()
    self._red = self._check_num(v)
    self._reset()

  @property
  def green(self) -> int:
    """Уровень зелёного от 0 до 255"""
    return self._green

  @green.setter
  def green(self, v):
    self._check_ro()
    self._green = self._check_num(v)
    self._reset()

  @property
  def blue(self) -> int:
    """Уровень синего от 0 до 255"""
    return self._blue

  @blue.setter
  def blue(self, v):
    self._check_ro()
    self._blue = self._check_num(v)
    self._reset()

  @property
  def alpha(self) -> int:
    """Уровень прозрачности от 0 до 255"""
    return self._alpha

  @alpha.setter
  def alpha(self, v):
    self._check_ro()
    self._alpha = self._check_num(v)
    self._reset()

  @property
  def ahex(self) -> str:
    """Цвет в формате AHEX (`aarrggbb`)"""
    if self._ahex is None:
      self._ahex = ("%02x" % self.alpha) + self.hex
    return self._ahex

  @ahex.setter
  def ahex(self, v):
    self.alpha, self.red, self.green, self.blue = self._split_hex(v, 4)

  @property
  def hex(self) -> str:
    """Цвет в формате HEX (`rrggbb`). **Без прозрачности**"""
    if self._hex is None:
      self._hex = "%02x%02x%02x" % self.rgb
    return self._hex

  @hex.setter
  def hex(self, v):
    self.rgb = self._split_hex(v, 3)

  @property
  def hexa(self) -> str:
    """Цвет в формате HEXA (`rrggbbaa`)"""
    if self._hexa is None:
      self._hexa = self.hex + ("%02x" % self.alpha)
    return self._hexa

  @hexa.setter
  def hexa(self, v):
    self.rgba = self._split_hex(v, 4)

  @property
  def rgb(self) -> tuple[int, int, int]:
    """Цвет в формате RGB. **Без прозрачности**"""
    if self._rgb is None:
      self._rgb = (self.red, self.green, self.blue)
    return self._rgb

  @rgb.setter
  def rgb(self, v):
    self.red, self.green, self.blue = v

  @property
  def rgba(self) -> tuple[int, int, int, int]:
    """Цвет в формате RGBA"""
    if self._rgba is None:
      self._rgba = (self.red, self.green, self.blue, self.alpha)
    return self._rgba

  @rgba.setter
  def rgba(self, v):
    self.red, self.green, self.blue, self.alpha = v

  def _check_init(self):
    if self._init_complete:
      raise TypeError("Give from 3 to 4 positional arguments or 1 keyword argument")
    self._init_complete = True

  def _check_num(self, num: int):
    if not isinstance(num, int):
      raise TypeError(type(num), int)
    if (num < 0) or (num > 255):
      raise ValueError("The number should be in the range from 0 to 255, not %i" % num)
    return num

  def _check_ro(self):
    if self._readonly:
      raise RuntimeError("Read-only object")

  def _reset(self):
    self._ahex = None
    self._hex = None
    self._hexa = None
    self._rgb = None
    self._rgba = None

  def _split_hex(self, hex: str, n: int) -> list[int]:
    if hex[0] == "#":
      hex = hex[1:]
    lhex = len(hex)
    if lhex != n * 2:
      raise ValueError("Invalid HEX string")
    nums = [int(num, 16) for num in [hex[i:i + 2] for i in range(0, lhex, 2)]]
    return nums

  @classmethod
  def from_random(cls, red: int | range | slice = None, green: int | range | slice = None, blue: int | range | slice = None, alpha: int | range | slice = 255):
    """Случайный цвет"""
    from random import randint, randrange

    def random(num: int | range | slice):
      if num is None:
        return randint(0, 255)
      if isinstance(num, range) or isinstance(num, slice):
        return randrange(num.start, num.stop, num.step)
      return num
    return cls(random(red), random(green), random(blue), random(alpha))


class _COLORS:
  BLACK = 0, 0, 0
  BLUE = 0, 0, 255
  CYAN = 0, 255, 255
  GREEN = 0, 255, 0
  NULL = 0, 0, 0, 0
  RED = 255, 0, 0
  VIOLET = 255, 0, 255
  WHITE = 255, 255, 255
  YELLOW = 255, 255, 0

  def __init__(self):
    self._colors = {}
    for name in dir(self):
      if name[0] != "_":
        color = Color(*getattr(self, name))
        color._readonly = True
        self._colors[name] = color
        setattr(self, name, color)

  def __contains__(self, k) -> bool:
    return k.upper() in self._colors

  def __getitem__(self, k) -> Color:
    return self._colors[k.upper()]


class AutoaddDict(dict):
  def __init__(self, *args, default_value=None, **kwargs):
    dict.__init__(self, *args, **kwargs)
    self.default_value = default_value

  def __getitem__(self, k):
    if not k in self:
      self[k] = self.default_value
    return dict.__getitem__(self, k)


COLORS = _COLORS()
Error401 = AccessDeniedError
Error403 = AccessDeniedError
Error404 = NotFoundError
Inf = Infinity
NaN = NotANumber
