from datetime import time as TimeType
CIRCLE_EMOJI = {"black": "⚫", "blue": "🔵", "brown": "🟤", "green": "🟢", "orange": "🟠", "red": "🔴", "violet": "🟣", "white": "⚪", "yellow": "🟡"}
CLOCK_EMOJI = {"00:00": "🕛", "00:30": "🕧", "01:00": "🕐", "01:30": "🕜", "02:00": "🕑", "02:30": "🕝", "03:00": "🕒", "03:30": "🕞", "04:00": "🕓", "04:30": "🕟", "05:00": "🕔", "05:30": "🕠", "06:00": "🕕", "06:30": "🕡", "07:00": "🕖", "07:30": "🕢", "08:00": "🕗", "08:30": "🕣", "09:00": "🕘", "09:30": "🕤", "10:00": "🕙", "10:30": "🕥", "11:00": "🕚", "11:30": "🕦"}
FONT_EMOJI = {"*": "*️⃣", "#": "#️⃣", "0": "0️⃣", "1": "1️⃣", "10": "🔟", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "a": "🅰️", "ab": "🆎", "abc": "🔤", "atm": "🏧", "b": "🅱️", "cl": "🆑", "cool": "🆒", "free": "🆓", "i": "ℹ️", "m": "Ⓜ️", "new": "🆕", "ng": "🆖", "o": "🅾️", "ok": "🆗", "p": "🅿️", "sos": "🆘", "up!": "🆙", "vs": "🆚", "wc": "🚾"}
FONT_LOWER = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"}
FONT_UPPER = {"-": "⁻", "(": "⁽", ")": "⁾", "+": "⁺", "=": "⁼", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "n": "ⁿ"}
HEART_EMOJI = {"black": "🖤", "blue": "💙", "brown": "🤎", "green": "💚", "orange": "🧡", "red": "❤️", "violet": "💜", "white": "🤍", "yellow": "💛"}
LANG_EN = "abcdefghijklmnopqrstuvwxyz"
LANG_EN_UPPER = LANG_EN.upper()
LANG_NUM = "0123456789"
LANG_RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
LANG_RU_UPPER = LANG_RU.upper()
SQUARE_EMOJI = {"black": "⬛", "blue": "🟦", "brown": "🟫", "green": "🟩", "orange": "🟧", "red": "🟥", "violet": "🟪", "white": "⬜", "yellow": "🟨"}
for i in range(26):
  FONT_EMOJI[chr(ord("A") + i)] = chr(ord("🇦") + i)


def replace2emoji(text: str, *, _chars=FONT_EMOJI) -> str:
  """Заменить текст на эмодзи"""
  result = []
  for char in text.upper():
    if char in _chars:
      result.append(_chars[char])
    elif char == " ":
      result.append(" ")
    else:
      raise ValueError("Char not found: " + char)
  return "".join(result)


def upper_time(time: TimeType | tuple[int, int]) -> str:
  """Преобразовать время в стиль `15³⁰` (минуты вверх)"""
  if isinstance(time, TimeType):
    time = time.hour, time.minute
  return str(time[0]) + replace2emoji(f"{time[1]:02d}", _chars=FONT_UPPER)


def upper_time_seconds(time: TimeType | tuple[int, int, int]) -> str:
  """Преобразовать время в стиль `15:30²⁵` (секунды вверх)"""
  if isinstance(time, TimeType):
    time = time.hour, time.minute, time.second
  return str(time[0]) + ":" + upper_time(time[1:])


def clock_emoji(time: TimeType | tuple[int, int]) -> str:
  """Выбрать ближайший емодзи часов 🕒"""
  if isinstance(time, TimeType):
    time = time.hour, time.minute
  hour = int(time[0])
  minute = int(time[1])
  if minute < 15:  # :00 - :15
    minute = 0
  elif minute < 45:  # :15 - :45
    minute = 30
  else:  # :45 - :60 (добавить час)
    hour += 1
    minute = 0
  return CLOCK_EMOJI[f"{hour % 12:02d}:{minute:02d}"]
