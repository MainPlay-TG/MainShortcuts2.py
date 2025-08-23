"""Работа с компонентами Windows"""
import json
import os
import subprocess
import win32com.client
import winreg
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
def path2win(path:PATH_TYPES,**kw)->str:
  kw.setdefault("to_abs",True)
  return path2str(path,**kw).replace("/","\\")

class LnkFile:
  """Открыть/создать файл `.lnk`"""

  def __init__(self, path: PATH_TYPES, readonly: bool = True):
    path = path2win(path)
    if readonly:
      if not os.path.isfile(path):
        raise ms.file.NotAFileError(path)
    self.obj: win32com.client.CDispatch = shell["WScript"].CreateShortcut(path)
    self.readonly = readonly

  def __getitem__(self, k):
    result = getattr(self.obj, k, None)
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
      return
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
    self["TargetPath"] = path2win(v)

  @property
  def window_style(self) -> int:
    return self["WindowStyle"]

  @window_style.setter
  def window_style(self, v):
    self["WindowStyle"] =v

  @property
  def working_dir(self) -> None | str:
    return self["WorkingDirectory"]

  @working_dir.setter
  def working_dir(self, v):
    self["WorkingDirectory"] =path2win(v)

# XXX

# Названия и номера локаций
REG_LOC_BY_NAME={
  "~":winreg.HKEY_CURRENT_USER,
  "CLASSES_ROOT":winreg.HKEY_CLASSES_ROOT,
  "CURRENT_CONFIG":winreg.HKEY_CURRENT_CONFIG,
  "CURRENT_USER":winreg.HKEY_CURRENT_USER,
  "DYN_DATA":winreg.HKEY_DYN_DATA,
  "HKCC":winreg.HKEY_CURRENT_CONFIG,
  "HKCR":winreg.HKEY_CLASSES_ROOT,
  "HKCU":winreg.HKEY_CURRENT_USER,
  "HKDD":winreg.HKEY_DYN_DATA,
  "HKLM":winreg.HKEY_LOCAL_MACHINE,
  "HKPD":winreg.HKEY_PERFORMANCE_DATA,
  "HKU":winreg.HKEY_USERS,
  "LOCAL_MACHINE":winreg.HKEY_LOCAL_MACHINE,
  "PERFORMANCE_DATA":winreg.HKEY_PERFORMANCE_DATA,
  "USERS":winreg.HKEY_USERS,
}
REG_LOC_BY_NUM={}
# Названия окружений
ENV_SYSTEM="system"
ENV_SYSTEM64="system64"
ENV_USER="user"
# Добавить локации с исходными названиями
for k in dir(winreg):
  if k.startswith("HKEY_"):
    v=getattr(winreg,k)
    REG_LOC_BY_NAME[k]=v
    REG_LOC_BY_NUM[v]=k
# Часто используемые локации
class RegFastLocations:
  SYSTEM_WINDOWS="/HKLM/SOFTWARE/Microsoft/Windows/CurrentVersion"
  SYSTEM64_WINDOWS="/HKLM/SOFTWARE/WOW6432Node/Microsoft/Windows/CurrentVersion"
  USER_WINDOWS="/HKCU/SOFTWARE/Microsoft/Windows/CurrentVersion"
  #
  SYSTEM_AUTORUN_ONCE=SYSTEM_WINDOWS+"/RunOnce"
  SYSTEM_AUTORUN=SYSTEM_WINDOWS+"/Run"
  SYSTEM_ENV="HKLM/SYSTEM/CurrentControlSet/Control/Session Manager/Environment"
  SYSTEM_PROG_LIST=SYSTEM_WINDOWS+"/Uninstall"
  SYSTEM64_AUTORUN_ONCE=SYSTEM64_WINDOWS+"/RunOnce"
  SYSTEM64_AUTORUN=SYSTEM64_WINDOWS+"/Run"
  SYSTEM64_PROG_LIST=SYSTEM64_WINDOWS+"/Uninstall"
  USER_AUTORUN_ONCE=USER_WINDOWS+"/RunOnce"
  USER_AUTORUN=USER_WINDOWS+"/Run"
  USER_ENV="HKCU/Environment"
  USER_PROG_LIST=USER_WINDOWS+"/Uninstall"
# Функции для работы с путями
def reg_prep_path(path:str,lstrip=False)->str:
  if not path:
    return "" if lstrip else "\\"
  path=path.replace("/","\\").rstrip("\\")
  if not path:
    return "" if lstrip else "\\"
  if lstrip:
    return path.lstrip("\\")
  return path
def reg_path2loc(path:str)->tuple[int,str]:
  path=reg_prep_path(path)
  if path.startswith("~"):
    path="\\"+path
  assert path.startswith("\\")
  parts=path.split("\\",2)
  return REG_LOC_BY_NAME[parts[1].upper()],("\\" if len(parts)==2 else parts[2])
def reg_loc2path(loc:int|str,loc_path:str=None)->str:
  if isinstance(loc,int):
    loc=REG_LOC_BY_NUM[loc]
  return ("\\"+loc.upper()+"\\"+reg_prep_path(loc_path,True)).rstrip("\\")
# Различные варианты для работы с значениями реестра
class RegFolder:
  """Папка реестра. С обязательным указанием типов значений"""
  def __init__(self,loc:int|str,loc_path:str,**kw):
    if isinstance(loc,str):
      loc=REG_LOC_BY_NAME[loc.upper()]
    assert loc in REG_LOC_BY_NUM
    self._loc_num=loc
    self._loc_path=loc_path
    self._opened_key=None
    self._path=None
    self._use_count=0
    self.open_kw=kw
  def __enter__(self):
    if not self._opened_key:
      self._opened_key=winreg.OpenKeyEx(self.loc_num,self.loc_path+"\\",**self.open_kw)
    self._use_count+=1
    return self
  def __exit__(self,*a):
    self._use_count-=1
    if self._opened_key: # Если ключ открыт
      if self._use_count<1: # и никем не используется
        self._opened_key.Close() # он будет закрыт
  def __contains__(self,k)->bool:
    with self:
      try:
        winreg.QueryValueEx(self._opened_key,k)
      except FileNotFoundError:
        return False
    return True
  def __delitem__(self,k):
    with self:
      winreg.DeleteValue(self._opened_key,k)
  def __getitem__(self,k):
    """`value,type`"""
    with self:
      try:
        return winreg.QueryValueEx(self._opened_key,k)
      except FileNotFoundError:
        raise KeyError(k)
  def __setitem__(self,k,v):
    if not isinstance(v,(list,tuple)):
      raise ValueError("Value must be a tuple with a value and a type")
    if not len(v)==2:
      raise ValueError("Value must be a tuple with a value and a type")
    if not isinstance(v[1],int):
      raise ValueError("Second value must be the registry value type")
    value,type=v
    with self:
      winreg.SetValueEx(self._opened_key,k,0,type,value)
  @property
  def auto(self):
    """Тип значений определяется автоматически"""
    return RegFolderAuto(self.loc_num,self.loc_path,**self.open_kw)
  @property
  def json(self):
    """Все значения в реестре хранятся в виде JSON"""
    return RegFolderJson(self.loc_num,self.loc_path,**self.open_kw)
  @property
  def loc_name(self)->str:
    """Название локации в реестре (пример: `HKEY_CURRENT_USER`)"""
    return REG_LOC_BY_NUM[self._loc_num]
  @property
  def loc_num(self)->int:
    """Номер локации в реестре"""
    return self._loc_num
  @property
  def loc_path(self)->str:
    """Путь без названия локации (пример: `SOFTWARE\\Microsoft\\Windows`)"""
    return self._loc_path
  @property
  def loc_tuple(self)->tuple[int,str]:
    """Номер локации и путь раздельно (`loc_num` и `loc_path`)"""
    return self._loc_num,self._loc_path
  @property
  def normal(self):
    return self
  @property
  def path(self)->str:
    """Путь с названием локации (пример: `\\HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows`)"""
    if self._path is None:
      self._path=reg_loc2path(self._loc_num,self._loc_path)
    return self._path
  @classmethod
  def create(cls,loc,loc_path,**kw):
    self=cls(loc,loc_path,**kw)
    self._opened_key=winreg.CreateKeyEx(self.loc_num,self.loc_path+"\\",**kw)
    return self
  @classmethod
  def create_from_path(cls,path:str,**kw):
    return cls.create(*reg_path2loc(path),**kw)
  @classmethod
  def from_path(cls,path:str,**kw):
    return cls(*reg_path2loc(path),**kw)
  def get(self,key:str,default=None):
    with self:
      try:
        return winreg.QueryValueEx(self._opened_key,k)
      except FileNotFoundError:
        return default
  def setdefault(self,key,value,type:int=None):
    if not key in self:
      self[key]=value if type is None else (value,type)
  def pop(self,key:str,default=Ellipsis):
    try:
      value=winreg.QueryValueEx(self._opened_key,k)
      del self[key]
    except FileNotFoundError:
      if default is Ellipsis:
        raise KeyError(key)
      value=default
    return value
class RegFolderAuto(RegFolder):
  """Папка реестра. Тип значений определяется автоматически"""
  def __getitem__(self,k):
    with self:
      try:
        return winreg.QueryValueEx(self._opened_key,k)[0]
      except FileNotFoundError:
        raise KeyError(k)
  def __setitem__(self,k,v):
    if isinstance(v,float):
      int_v=int(v)
      if v==int_v:
        v=int_v
    with self:
      winreg.SetValueEx(self._opened_key,k,0,self._detect_type(v),v)
  def _detect_type(self,v):
    if v is None:
      return winreg.REG_NONE
    if isinstance(v,bytes):
      return winreg.REG_BINARY
    if isinstance(v,float):
      raise ValueError("float cannot be written to the registry")
    if isinstance(v,int):
      if v<0:
        raise ValueError("Number must be positive")
      if v>0xffffffff:
        if v>0xffffffffffffffff:
          raise ValueError("Number is too big")
        return winreg.REG_QWORD
      return winreg.REG_DWORD
    if isinstance(v,str):
      return winreg.REG_MULTI_SZ if "\n" in v else winreg.REG_SZ
    raise ValueError("Failed to detect type")
  @property
  def auto(self):
    return self
  @property
  def normal(self):
    return RegFolder(self.loc_num,self.loc_path,**self.open_kw)
  def setdefault(self,key:str,value):
    if not key in self:
      self[key]=value
class RegFolderJson(RegFolderAuto):
  """Папка реестра. Все значения в реестре хранятся в виде JSON"""
  def __getitem__(self,k):
    return json.loads(RegFolderAuto.__getitem__(self,k))
  def __setitem__(self,k,v,**kw):
    kw.setdefault("separators",(",",":"))
    RegFolderAuto.__setitem__(self,k,json.dumps(v,**kw))
  @property
  def json(self):
    return self
# Проводник реестра (с поддержкой рабочей папки)
class RegExplorer:
  def __init__(self,cwd:str=None):
    self.cwd=cwd
    self.folder_cls:type[RegFolder|RegFolderAuto|RegFolderJson]=RegFolder
    self._opened_keys={}
  def _resolve(self,path) -> tuple[int, str]:
    path=reg_prep_path(path) if path else ""
    if not path.startswith("\\"):
      path=self.cwd+"\\"+path
    return reg_path2loc(path)
  @property
  def cwd(self)->str:
    """Current Working Dir"""
    return self._cwd
  @cwd.setter
  def cwd(self,v):
    if v is None:
      self._cwd="\\"
    else:
      v=reg_prep_path(v) if v else ""
      assert v.startswith("\\")
      self._cwd=v
  def chdir(self,path):
    self.cwd=self._resolve(path)
  def create_folder(self,path,**kw):
    if isinstance(path,RegFolder):
      return path
    return self.folder_cls.create(*self._resolve(path),**kw)
  def open_folder(self,path,**kw):
    if isinstance(path,RegFolder):
      return path
    return self.folder_cls(*self._resolve(path),**kw)
  def get_value(self,path,key,**kw):
    return self.open_folder(path,**kw)[key]
  def set_value(self,path,key,value,type=None,*,mkdir=False,**kw):
    if not type is None:
      value=value,type
    (self.create_folder(path,**kw) if mkdir else self.open_folder(path,**kw))[key]=value
  def del_value(self,path,key,**kw):
    del self.open_folder(path,**kw)[key]
# Утилиты
class utils:
  @staticmethod
  def add_autorun(env:str,name:str,cmd:str,*,expand=True,once=False):
    """Зарегистрировать программу для автозапуска"""
    path=getattr(RegFastLocations,env.upper()+"AUTORUN")
    if once:
      path+="Once"
    RegFolder.create_from_path(path)[name]=cmd,(winreg.REG_EXPAND_SZ if expand else winreg.REG_SZ)
  @staticmethod
  def add_system_autorun(name:str,cmd:str,**kw):
    utils.add_autorun(ENV_SYSTEM,name,cmd,**kw)
  @staticmethod
  def add_system64_autorun(name:str,cmd:str,**kw):
    utils.add_autorun(ENV_SYSTEM64,name,cmd,**kw)
  @staticmethod
  def add_user_autorun(name:str,cmd:str,**kw):
    utils.add_autorun(ENV_USER,name,cmd,**kw)
