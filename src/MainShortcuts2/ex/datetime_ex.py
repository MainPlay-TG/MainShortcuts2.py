from datetime import timedelta
from functools import cached_property, total_ordering


def to_td(obj):
  if isinstance(obj, timedelta):
    return obj
  if isinstance(obj, (float, int)):
    return timedelta(seconds=obj)
  if isinstance(obj, dict):
    return timedelta(**obj)
  if isinstance(obj, TDInfo):
    return obj.timedelta
  raise TypeError(f"Unsupported type {type(obj)}")


@total_ordering
class TDInfo:
  _replace_keys = ("days", "hours", "microseconds", "minutes", "seconds")
  _letters = ["d", "h", "m", "s"]

  def __init__(self, td: timedelta):
    self._td = td
    self._override_letters = self._letters.copy()

  def __add__(self, other):
    return type(self)(self.timedelta + to_td(other))

  def __sub__(self, other):
    return type(self)(self.timedelta - to_td(other))

  def __eq__(self, other):
    if isinstance(other, TDInfo):
      return self.timedelta == other.timedelta
    return False

  def __lt__(self, other):
    if isinstance(other, TDInfo):
      return self.timedelta < other.timedelta
    return NotImplemented

  def __str__(self):
    l = self._override_letters
    parts = []
    if self.days:
      parts.append(f"{self.days}{l[0]}")
    if self.hours:
      parts.append(f"{self.hours}{l[1]}")
    if self.minutes:
      parts.append(f"{self.minutes}{l[2]}")
    if self.seconds:
      parts.append(f"{self.seconds}{l[3]}")
    if parts:
      return " ".join(parts)
    return f"0{l[3]}"

  @cached_property
  def days(self) -> int:
    """Кол-во дней (не ограничено)"""
    return self._td.days

  @cached_property
  def hours(self) -> int:
    """Кол-во часов (`range(24)`)"""
    return self._td.seconds // 3600

  @cached_property
  def minutes(self) -> int:
    """Кол-во минут (`range(60)`)"""
    return self._td.seconds // 60 % 60

  @cached_property
  def seconds(self) -> int:
    """Кол-во секунд (`range(60)`)"""
    return self._td.seconds % 60

  @cached_property
  def microseconds(self) -> int:
    """Кол-во микросекунд (`range(1000000)`)"""
    return self._td.microseconds

  @cached_property
  def timedelta(self) -> timedelta:
    """Оригинальный `timedelta`"""
    return self._td

  @cached_property
  def total_days(self) -> float:
    """Общее кол-во дней"""
    return self.total_seconds / 86400

  @cached_property
  def total_hours(self) -> float:
    """Общее кол-во часов"""
    return self.total_seconds / 3600

  @cached_property
  def total_minutes(self) -> float:
    """Общее кол-во минут"""
    return self.total_seconds / 60

  @cached_property
  def total_seconds(self) -> float:
    """Общее кол-во секунд"""
    return self._td.total_seconds()

  @classmethod
  def create(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0, **kw):
    """Создать с параметрами как у `timedelta`"""
    return cls(timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks, **kw))

  def replace(self, **kw):
    """Создать с заменой параметров"""
    for k in self._replace_keys:
      if not k in kw:
        kw[k] = getattr(self, k)
    return type(self)(timedelta(**kw))
