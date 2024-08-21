import os
import sys
from .core import MS2
from typing import *
try:
  import colorama
  colorama.init()
except Exception:
  colorama = None
ms: MS2 = None
# 2.0.0
COLOR_NAMES = ["BG_BLACK", "BG_BLUE", "BG_GREEN", "BG_LIGHTBLACK", "BG_LIGHTBLUE", "BG_LIGHTGREEN", "BG_LIGHTPINK", "BG_LIGHTRED", "BG_LIGHTWHITE", "BG_LIGHTYELLOW", "BG_PINK", "BG_RED", "BG_WHITE", "BG_YELLOW", "BLACK", "BLUE", "GREEN", "HIGH", "LIGHTBLACK", "LIGHTBLUE", "LIGHTGREEN", "LIGHTPINK", "LIGHTRED", "LIGHTWHITE", "LIGHTYELLOW", "LOW", "PINK", "RED", "RESET", "WHITE", "YELLOW"]
COLORS: dict[str, str] = {}
for i in COLOR_NAMES:
  COLORS[i] = ""
if not colorama is None:
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


def cformat(text: str, *, end: str = None, format: str = "$COLOR_%s", start: str = None) -> str:
  for i in COLORS:
    text = text.replace(format % i, COLORS[i])
  if not start is None:
    text = COLORS[start] + text
  if not end is None:
    text = text + COLORS[end]
  return text


def cprint(*texts, format: str = None, reset: bool = True, start: str = None, **kw):
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
  if colors is None:
    colors = COLOR_NAMES
  for i in colors:
    cprint("$COLOR_RESET%s: $COLOR_%sEXAMPLE ░▒▓ ███" % (i, i))


def clear():
  if sys.platform == "win32":
    return os.system("clear")
  if sys.platform == "linux":
    return os.system("cls")
  raise OSError("The function is not available on %s" % sys.platform)


cls = clear
