"""Работа с компонентами Windows"""
import win32com.client
from .core import ms
from .path import PATH_TYPES, path2str
from typing import *
# 2.0.0
shell = {}
shell["WScript"] = win32com.client.Dispatch("WScript.Shell")
_names = {}
_names["lnk"] = {"args": "Arguments", "cwd": "WorkingDirectory", "desc": "Description", "hotkey": "Hotkey", "icon": "IconLocation", "lnk": "FullName", "target": "TargetPath"}


def read_lnk(path: PATH_TYPES) -> dict:
  """Прочитать ярлык .lnk"""
  r = {}
  lnk = shell["WScript"].CreateShortcut(path2str(path, True).replace("/", "\\"))
  r["src"] = lnk
  for k, v in _names["lnk"].items():
    if hasattr(lnk, v):
      r[k] = getattr(lnk, v)
    else:
      r[k] = None
  return r


def write_lnk(path: PATH_TYPES, target: str, args: str = None, cwd: str = None, desc: str = None, hotkey: str = None, icon: str = None):
  """Создать ярлык .lnk"""
  lnk = shell["WScript"].CreateShortCut(path2str(path, True).replace("/", "\\"))
  lnk.TargetPath = target.replace("/", "\\")
  if args != None:
    lnk.Arguments = args
  if cwd != None:
    lnk.WorkingDirectory = cwd.replace("/", "\\")
  if desc != None:
    lnk.Description = desc
  if hotkey != None:
    lnk.Hotkey = hotkey
  if icon != None:
    lnk.IconLocation = icon.replace("/", "\\")
  lnk.Save()
  return lnk
