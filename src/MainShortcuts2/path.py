import io
import os
import pathlib
import shutil
from .core import ms
from typing import *
# 2.0.0
EXTSEP = "."
FORBIDDEN_SYMBOLS = [":", "!", "?", "@", "*", "\"", "\n", "%", "+", "<", ">", "|"]
PATH_TYPES = Union[io.FileIO, pathlib.Path, str]
PATHSEP = "/"


def _path2str(path):
  if type(path) == str:
    return path
  if type(path) == pathlib.Path:
    return path.as_posix()
  if type(path) == io.FileIO:
    return path.name
  if type(path) == Path:
    return path.path


def path2str(path: PATH_TYPES, to_abs: bool = False, replace_forbidden_to: str = None) -> str:
  result = _path2str(path).replace("\\", PATHSEP)
  if not replace_forbidden_to is None:
    for i in FORBIDDEN_SYMBOLS:
      if i in replace_forbidden_to:
        raise ValueError("It is impossible to replace the forbidden symbol with another forbidden symbol")
      result = result.replace(i, replace_forbidden_to)
  if to_abs:
    result = os.path.abspath(result)
  return result


@property
def cwd():
  return os.getcwd().replace("\\", PATHSEP)


@cwd.setter
def cwd(v):
  os.chdir(path2str(v))


class Path:
  # 2.0.0
  def __init__(self, path: PATH_TYPES):
    self._base_name = None
    self._ext = None
    self._full_name = None
    self._parent_dir = None
    self._path = path2str(path, True)
    self._split = None
    self.cp = self.copy
    self.ln = self.link
    self.mv = self.move
    self.rm = self.delete
    self.rn = self.rename
    self.reload()

  def reload(self):
    """Обнуление кешированной информации"""
    self._created_at = None
    self._exists = None
    self._is_dir = None
    self._is_file = None
    self._is_link = None
    self._modified_at = None
    self._realpath = None
    self._size = None
    self._type = None
    self._used_at = None

  @property
  def path(self) -> str:
    """Абсолютный путь к объекту"""
    return self._path

  @property
  def base_name(self) -> str:
    """Имя объекта без расширения"""
    if self._base_name is None:
      self._base_name, self._ext = os.path.splitext(self.full_name)
    return self._base_name

  @property
  def created_at(self) -> float:
    """timestamp создания объекта"""
    if self._created_at is None:
      self._created_at = os.path.getctime(self.path)
    return self._created_at

  @property
  def exists(self) -> bool:
    """Существует ли объект"""
    if self._exists is None:
      self._exists = os.path.exists(self.path)

  @property
  def ext(self) -> str:
    """Расширение объекта (включая точку)"""
    if self._ext is None:
      self._base_name, self._ext = os.path.splitext(self.full_name)
    return self._ext

  @property
  def full_name(self) -> str:
    """Полное имя объекта (включая расширение)"""
    if self._full_name is None:
      self._parent_dir, self._full_name = os.path.split(self.path)
    return self._full_name

  @property
  def is_dir(self) -> bool:
    """Является ли объект папкой"""
    if self._is_dir is None:
      self._is_dir = os.path.isdir(self.path)
      if self._is_dir:
        self._type = "dir"
    return self._is_dir

  @property
  def is_file(self) -> bool:
    """Является ли объект файлом"""
    if self._is_file is None:
      self._is_file = os.path.isfile(self.path)
      if self._is_file:
        self._type = "file"
    return self._is_file

  @property
  def is_link(self) -> bool:
    """Является ли объект ссылкой на другой объект"""
    if self._is_link is None:
      self._is_link = os.path.islink(self.path)
    return self._is_link

  @property
  def modified_at(self) -> float:
    """timestamp изменения объекта"""
    if self._modified_at is None:
      self._modified_at = os.path.getmtime(self.path)
    return self._modified_at

  @property
  def parent_dir(self) -> str:
    """Путь к родительской папке"""
    if self._parent_dir is None:
      self._parent_dir, self._full_name = os.path.split(self.path)
    return self._parent_dir

  @property
  def realpath(self) -> str:
    """Настоящий путь к объекту, если это ссылка (может быть неправильным)"""
    if self._realpath is None:
      if self.is_link:
        self._realpath = os.readlink(self.path)
      else:
        self._realpath = self.path
    return self._realpath

  @property
  def size(self) -> int:
    """Размер объекта в байтах"""
    if self._size is None:
      self._size = os.path.getsize(self.path)
    return self._size

  @property
  def split(self) -> tuple:
    """Разбитый путь к объекту"""
    if self._split is None:
      self._split = self.path.split(PATHSEP)
    return self._size

  @property
  def type(self) -> str:
    """Тип объекта ('dir'|'file')"""
    if self._type is None:
      if self.is_dir:
        self._type = "dir"
      if self.is_file:
        self._type = "file"
      if self._type is None:
        raise TypeError("Unknown type")
    return self._type

  @property
  def used_at(self) -> float:
    """timestamp последнего использования объекта"""
    if self._used_at is None:
      self._used_at = os.path.getatime(self.path)
    return self._used_at

  def copy(self, dest: PATH_TYPES, **kw):
    kw["dest"] = dest
    kw["path"] = self.path
    return copy(**kw)

  def delete(self, **kw):
    kw["path"] = self.path
    return delete(**kw)

  def in_dir(self, dir: PATH_TYPES, **kw) -> bool:
    kw["dir"] = self.dir
    kw["path"] = self.path
    return in_dir(**kw)

  def link(self, dest: PATH_TYPES, **kw):
    kw["dest"] = dest
    kw["path"] = self.path
    return link(**kw)

  def move(self, dest: PATH_TYPES, **kw):
    kw["dest"] = dest
    kw["path"] = self.path
    return move(**kw)

  def rename(self, name: str, **kw):
    kw["name"] = name
    kw["path"] = self.path
    return rename(**kw)


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  kw["src"] = path2str(path)
  kw["dst"] = path2str(dest)
  if os.path.isfile(kw["src"]):
    return shutil.copy(**kw)
  if os.path.isdir(kw["src"]):
    return shutil.copytree(**kw)


def delete(path: PATH_TYPES, **kw):
  kw["path"] = path2str(path)
  if os.path.islink(kw["path"]):
    os.unlink(**kw)
  if os.path.isdir(kw["path"]):
    shutil.rmtree(**kw)
  if os.path.isfile(kw["path"]):
    os.remove(**kw)


def exists(path: PATH_TYPES):
  return os.path.exists(path2str(path))


def in_dir(path: str, dir: str, recursion_limit: int = 1000) -> bool:
  dir = path2str(dir, True)
  path = path2str(path, True)
  while True:
    pdir = os.path.dirname(path)
    if path == pdir:
      return False
    if dir == pdir:
      return True
    path = pdir
    recursion_limit -= 1
    if recursion_limit < 0:
      raise RecursionError()


def is_dir(path: PATH_TYPES) -> bool:
  return os.path.isdir(path2str(path))


def is_file(path: PATH_TYPES) -> bool:
  return os.path.isfile(path2str(path))


def is_link(path: PATH_TYPES) -> bool:
  return os.path.islink(path2str(path))


def link(path: PATH_TYPES, dest: PATH_TYPES, force: bool = False, **kw):
  kw["dst"] = path2str(dest, True)
  kw["src"] = path2str(path, True)
  if force:
    if exists(kw["dst"]):
      delete(kw["dst"])
  return os.symlink(**kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, force: bool = False, **kw):
  kw["dst"] = path2str(dest, True)
  kw["src"] = path2str(path, True)
  if force:
    if exists(kw["dst"]):
      delete(kw["dst"])
  return shutil.move(**kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  kw["path"] = path
  kw["dest"] = os.path.dirname(path2str(path)) + "/" + name
  return move(**kw)


cp = copy
ln = link
mv = move
rm = delete
rn = rename
