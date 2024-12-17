"""Работа с терминалом"""
import builtins
import os
import sys
from .core import ms
from typing import *
try:
  import colorama
  colorama.init()
except Exception:
  colorama = None
COLOR_NAMES = ["BG_BLACK", "BG_BLUE", "BG_GREEN", "BG_LIGHTBLACK", "BG_LIGHTBLUE", "BG_LIGHTGREEN", "BG_LIGHTPINK", "BG_LIGHTRED", "BG_LIGHTWHITE", "BG_LIGHTYELLOW", "BG_PINK", "BG_RED", "BG_WHITE", "BG_YELLOW", "BLACK", "BLUE", "GREEN", "HIGH", "LIGHTBLACK", "LIGHTBLUE", "LIGHTGREEN", "LIGHTPINK", "LIGHTRED", "LIGHTWHITE", "LIGHTYELLOW", "LOW", "PINK", "RED", "RESET", "WHITE", "YELLOW"]
COLORS: dict[str, str] = {}
for i in COLOR_NAMES:
  COLORS[i] = ""


def disable_colors():
  for i in COLOR_NAMES:
    COLORS[i] = ""


def enable_colors():
  COLORS["BG_BLACK"] = colorama.Back.BLACK
  COLORS["BG_BLUE"] = colorama.Back.BLUE
  COLORS["BG_GREEN"] = colorama.Back.GREEN
  COLORS["BG_LIGHTBLACK"] = colorama.Back.LIGHTBLACK_EX
  COLORS["BG_LIGHTBLUE"] = colorama.Back.LIGHTBLUE_EX
  COLORS["BG_LIGHTGREEN"] = colorama.Back.LIGHTGREEN_EX
  COLORS["BG_LIGHTPINK"] = colorama.Back.LIGHTMAGENTA_EX
  COLORS["BG_LIGHTRED"] = colorama.Back.LIGHTRED_EX
  COLORS["BG_LIGHTWHITE"] = colorama.Back.LIGHTWHITE_EX
  COLORS["BG_LIGHTYELLOW"] = colorama.Back.LIGHTYELLOW_EX
  COLORS["BG_PINK"] = colorama.Back.MAGENTA
  COLORS["BG_RED"] = colorama.Back.RED
  COLORS["BG_WHITE"] = colorama.Back.WHITE
  COLORS["BG_YELLOW"] = colorama.Back.YELLOW
  COLORS["BLACK"] = colorama.Fore.BLACK
  COLORS["BLUE"] = colorama.Fore.BLUE
  COLORS["GREEN"] = colorama.Fore.GREEN
  COLORS["HIGH"] = colorama.Style.BRIGHT
  COLORS["LIGHTBLACK"] = colorama.Fore.LIGHTBLACK_EX
  COLORS["LIGHTBLUE"] = colorama.Fore.LIGHTBLUE_EX
  COLORS["LIGHTGREEN"] = colorama.Fore.LIGHTGREEN_EX
  COLORS["LIGHTPINK"] = colorama.Fore.LIGHTMAGENTA_EX
  COLORS["LIGHTRED"] = colorama.Fore.LIGHTRED_EX
  COLORS["LIGHTWHITE"] = colorama.Fore.LIGHTWHITE_EX
  COLORS["LIGHTYELLOW"] = colorama.Fore.LIGHTYELLOW_EX
  COLORS["LOW"] = colorama.Style.DIM
  COLORS["PINK"] = colorama.Fore.MAGENTA
  COLORS["RED"] = colorama.Fore.RED
  COLORS["RESET"] = colorama.Style.RESET_ALL
  COLORS["WHITE"] = colorama.Fore.WHITE
  COLORS["YELLOW"] = colorama.Fore.YELLOW


if not colorama is None:
  enable_colors()


def cformat(text: str, *, end: str = None, format: str = "$COLOR_%s", start: str = None) -> str:
  """Сделать цветной текст"""
  for i in COLORS:
    text = text.replace(format % i, COLORS[i])
  if not start is None:
    text = COLORS[start] + text
  if not end is None:
    text = text + COLORS[end]
  return text


def cprint(*texts, format: str = None, reset: bool = True, start: str = None, **kw):
  """Напечатать цветной текст"""
  fm_kw = {}
  if not format is None:
    fm_kw["format"] = format
  args = []
  for i in texts:
    if start is None:
      fm_kw["start"] = None
    else:
      fm_kw["start"] = start
      start = None
    fm_kw["text"] = i
    args.append(cformat(**fm_kw))
  if reset:
    args[-1] += COLORS["RESET"]
  print(*args, **kw)


def color_test(colors: list[str] = None):
  """Тестирование цветов"""
  if colors is None:
    colors = COLOR_NAMES
  for i in colors:
    cprint("$COLOR_RESET%s: $COLOR_%sEXAMPLE \u2591\u2592\u2593 \u2588\u2588\u2588" % (i, i))


def _clear():  # type: ignore
  """Если функция недоступна для ОС, дать ошибку"""
  raise OSError("The function is not available on %s" % sys.platform)


if sys.platform == "win32":
  def _clear():
    """Windows"""
    os.system("clear")
if sys.platform == "linux":
  def _clear():
    """Linux"""
    os.system("cls")


def clear():
  """Очистить терминал (только Windows и Linux)"""
  _clear()


def set_title(title: str):
  """Установить заголовок окна"""
  # Не работает на bpython: AssertionError
  print("\u001b]2;" + title + "\u0007", end="")


def set_displayhook(func):
  """Изменить `sys.displayhook`"""
  if func is None:
    def func(obj):
      """Стандартный `displayhook` от Python"""
      if not obj is None:
        print(repr(obj))
  setattr(sys, "displayhook", func)
  return func


def patch_shell(style: int):
  """Изменить стиль консоли Python"""
  displayhook = None
  ps1 = ">>> "
  ps2 = "... "
  if style == 1:
    def displayhook(obj):
      if not obj is None:
        print("%s: %r" % (type(obj), obj))
    ps1 = "=> "
    ps2 = "|> "
  set_displayhook(displayhook)
  setattr(sys, "ps1", ps1)
  setattr(sys, "ps2", ps2)


def iter_line(lines: Iterable[str], end: str = "\n", interval: float = None, **kw):
  """Изменять последнюю строку в терминале"""
  if interval is None:
    sleep = ms.utils.return_None
  else:
    from datetime import timedelta
    from time import sleep
    if isinstance(interval, timedelta):
      interval = interval.total_seconds()
  kw["end"] = ""
  maxlen = 0
  for line in lines:
    line = str(line)
    lline = len(line)
    if lline > maxlen:
      maxlen = lline
    print("\r" + line + " " * (maxlen - lline), **kw)
    sleep(interval)
  print(end, **kw)


def countful_countdown(time: float, interval: float = 1, format: str = None, round: int = 2, **kw):
  """Обратный отсчёт в терминале"""
  if format is None:
    format = "Осталось %s сек."
  nums: list[float] = []
  while time > 0:
    time -= interval if time > interval else time
    nums.append(time)

  def generator():
    for num in nums:
      yield (format % builtins.round(num, round))
  kw["interval"] = interval
  kw["lines"] = generator()
  return iter_line(**kw)


cls = clear
