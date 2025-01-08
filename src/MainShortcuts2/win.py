"""Работа с компонентами Windows"""
import os
import subprocess
import win32com.client
from .core import ms
from .path import PATH_TYPES, path2str
from typing import *
shell: dict[str, win32com.client.CDispatch] = {}
shell["WScript"] = win32com.client.Dispatch("WScript.Shell")
_names = {}
_names["lnk"] = {"args": "Arguments", "cwd": "WorkingDirectory", "desc": "Description", "hotkey": "Hotkey", "icon": "IconLocation", "lnk": "FullName", "target": "TargetPath"}


def read_lnk(path: PATH_TYPES) -> dict:
  """Прочитать ярлык .lnk"""
  r = {}
  lnk = shell["WScript"].CreateShortcut(path2str(path, True).replace("/", "\\"))
  r["src"] = lnk
  for k, v in _names["lnk"].items():
    r[k] = getattr(lnk, v, None)
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


def hide_file(path: PATH_TYPES, *, recursive: bool = False, unhide: bool = False):
  """Скрыть файл используя системную команду `attrib`"""
  args = ["attrib"]
  args.append("-H" if unhide else "+H")
  args.append(path2str(path, True).replace("/", "\\"))
  if recursive:
    args += ["/S", "/D"]
  subprocess.run(args, check=True)


def unhide_file(path: PATH_TYPES, *, recursive: bool = False, hide: bool = False):
  """Противоположность функции скрытия файла"""
  return hide_file(path, recursive=recursive, unhide=not hide)


class LnkFile:
  """Открыть/создать файл `.lnk`"""

  def __init__(self, path: PATH_TYPES, readonly: bool = True):
    path = path2str(path, True).replace("/", "\\")
    if readonly:
      if not os.path.isfile(path):
        raise ms.file.NotAFileError(path)
    self.obj: win32com.client.CDispatch = shell["WScript"].CreateShortcut(path)
    self.readonly = readonly

  def __getitem__(self, k):
    result = getattr(self, k, None)
    if result == "":
      return None
    return result

  def __setitem__(self, k, v):
    if self.readonly:
      raise RuntimeError("Read-only shortcut")
    if v is None:
      v = ""
    setattr(self.obj, k, v)

  def save(self):
    """Сохранить изменения"""
    if self.readonly:
      raise RuntimeError("Read-only shortcut")
    self.obj.Save()

  @property
  def args_str(self) -> None | str:
    return self["Arguments"]

  @args_str.setter
  def args_str(self, v):
    self["Arguments"] = v

  @property
  def args(self) -> None | list[str]:
    line = self.args_str
    if line is None:
      return None
    import shlex
    return shlex.split(line, posix=False)

  @args.setter
  def args(self, v):
    if v is None:
      self["Arguments"] = None
      return
    import shlex
    self["Arguments"] = shlex.join(v)

  @property
  def description(self) -> None | str:
    return self["Description"]

  @description.setter
  def description(self, v):
    self["Description"] = v

  @property
  def hot_key(self) -> None | str:
    return self["Hotkey"]

  @hot_key.setter
  def hot_key(self, v):
    self["Hotkey"] = v

  @property
  def icon_loc(self) -> None | str:
    return self["IconLocation"]

  @icon_loc.setter
  def icon_loc(self, v):
    self["IconLocation"] = v

  @property
  def path(self) -> str:
    return self["FullName"]

  @property
  def target_path(self) -> None | str:
    return self["TargetPath"]

  @target_path.setter
  def target_path(self, v):
    self["TargetPath"] = path2str(v, True).replace("/", "\\")

  @property
  def window_style(self) -> int:
    return self["WindowStyle"]

  @window_style.setter
  def window_style(self, v):
    self["WindowStyle"] = v

  @property
  def working_dir(self) -> None | str:
    return self["WorkingDirectory"]

  @working_dir.setter
  def working_dir(self, v):
    self["WorkingDirectory"] = v
