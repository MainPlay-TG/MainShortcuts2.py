"""Работа с объектами файловой системы и путями к ним"""
import io
import os
import pathlib
import shutil
import stat
import sys
from .core import ms
from datetime import datetime
from typing import *
EXTSEP = "."
FORBIDDEN_SYMBOLS = [":", "!", "?", "@", "*", "\"", "\n", "%", "+", "<", ">", "|"]
PATH_TYPES = Union[io.FileIO, pathlib.Path, str]
PATHSEP = "/"


def _path2str(path) -> str:
  if isinstance(path, str):
    return path
  if isinstance(path, pathlib.Path):
    return path.as_posix()
  if isinstance(path, io.FileIO):
    return path.name
  if isinstance(path, Path):
    return path.path
  return os.fspath(path)


def path2str(path: PATH_TYPES, to_abs: bool = False, replace_forbidden_to: str = None) -> str:
  """Преобразовать объект Python в строковый путь"""
  result = _path2str(path)
  if not replace_forbidden_to is None:
    for i in FORBIDDEN_SYMBOLS:
      if i in replace_forbidden_to:
        raise ValueError("It is impossible to replace the forbidden symbol with another forbidden symbol")
      result = result.replace(i, replace_forbidden_to)
  if to_abs:
    result = os.path.abspath(result)
  result = result.replace("\\", PATHSEP)
  if len(result) > 3 and result[-1] == "/":
    result = result[:-1]
  return result


def cwd(set_to: PATH_TYPES = None, only_set=False) -> str:
  """Получить путь к рабочей папке"""
  if not set_to is None:
    os.chdir(path2str(set_to))
  if not only_set:
    return os.getcwd().replace("\\", PATHSEP)


class Path(os.PathLike):
  """Информация и действия с объектом файловой системы"""

  def __init__(self, path: PATH_TYPES, use_cache: bool = True):
    self._path = path2str(path, to_abs=True)
    self.cp = self.copy
    self.ln = self.link
    self.mv = self.move
    self.reload(full=True)
    self.rm = self.delete
    self.rn = self.rename
    self.use_cache = use_cache

  def __fspath__(self) -> str:
    return self.path

  def __repr__(self):
    cls = type(self)
    if self.use_cache:
      return cls.__module__ + "." + cls.__name__ + "(" + repr(self.path) + ")"
    return cls.__module__ + "." + cls.__name__ + "(" + repr(self.path) + ", use_cache = False)"

  def __str__(self):
    return self.path

  def __lt__(self, other):
    return self.path < path2str(other, to_abs=True)

  def __add__(self, other) -> "Path":
    if isinstance(other, str):
      if not other.startswith("/"):
        other = "/" + other
      return Path(self.path + other, use_cache=self.use_cache)
    return NotImplemented

  def reload(self, full: bool = False):
    """Удаление кешированной информации"""
    if full:
      self._base_name = None
      self._ext = None
      self._full_name = None
      self._parent_dir = None
      self._split = None
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

  @path.setter
  def path(self, v):
    """Абсолютный путь к объекту"""
    self._path = path2str(v, to_abs=True)
    self.reload(full=True)

  @property
  def base_name(self) -> str:
    """Имя объекта без расширения (`example.txt` -> `example`)"""
    if self._base_name is None:
      self._base_name, self._ext = os.path.splitext(self.full_name)
    return self._base_name

  @property
  def created_at(self) -> float:
    """timestamp создания объекта"""
    if self._created_at is None or (not self.use_cache):
      self._created_at = os.path.getctime(self.path)
    return self._created_at

  @property
  def exists(self) -> bool:
    """Существует ли объект"""
    if self._exists is None or (not self.use_cache):
      self._exists = os.path.exists(self.path)
    return self._exists

  @property
  def ext(self) -> str:
    """Расширение объекта включая точку (`example.txt` -> `.txt`)"""
    if self._ext is None:
      self._base_name, self._ext = os.path.splitext(self.full_name)
    return self._ext

  @property
  def full_name(self) -> str:
    """Полное имя объекта включая расширение (`/home/example.txt` -> `example.txt`)"""
    if self._full_name is None:
      self._parent_dir, self._full_name = os.path.split(self.path)
    return self._full_name

  @property
  def is_dir(self) -> bool:
    """Является ли объект папкой"""
    if self._is_dir is None or (not self.use_cache):
      self._is_dir = os.path.isdir(self.path)
      if self._is_dir:
        self._type = "dir"
    return self._is_dir

  @property
  def is_file(self) -> bool:
    """Является ли объект файлом"""
    if self._is_file is None or (not self.use_cache):
      self._is_file = os.path.isfile(self.path)
      if self._is_file:
        self._type = "file"
    return self._is_file

  @property
  def is_link(self) -> bool:
    """Является ли объект ссылкой на другой объект"""
    if self._is_link is None or (not self.use_cache):
      self._is_link = os.path.islink(self.path)
    return self._is_link

  @property
  def modified_at(self) -> float:
    """timestamp изменения объекта"""
    if self._modified_at is None or (not self.use_cache):
      self._modified_at = os.path.getmtime(self.path)
    return self._modified_at

  @property
  def parent_dir(self) -> str:
    """Путь к родительской папке (`/home/exaple.txt` -> `/home`)"""
    if self._parent_dir is None:
      self._parent_dir, self._full_name = os.path.split(self.path)
    return self._parent_dir

  @property
  def realpath(self) -> str:
    """Настоящий путь к объекту, если это ссылка (может быть неправильным)"""
    if self._realpath is None or (not self.use_cache):
      if self.is_link:
        self._realpath = os.readlink(self.path)
      else:
        self._realpath = self.path
    return self._realpath

  @property
  def size(self) -> int:
    """Размер объекта в байтах"""
    if self._size is None or (not self.use_cache):
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
    """Тип объекта (`dir` | `file`)"""
    if self._type is None or (not self.use_cache):
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
    if self._used_at is None or (not self.use_cache):
      self._used_at = os.path.getatime(self.path)
    return self._used_at

  def copy(self, dest: PATH_TYPES, follow: bool = False, **kw) -> str:
    """Копирование объекта"""
    kw["dest"] = dest
    kw["path"] = self.path
    r = copy(**kw)
    if follow:
      self.path = r
    return r

  def delete(self, **kw):
    """Безвозвратное удаление объекта"""
    kw["path"] = self.path
    delete(**kw)
    self.reload()

  def in_dir(self, dir: PATH_TYPES, **kw) -> bool:
    """Находится ли объект в папке"""
    kw["dir"] = dir
    kw["path"] = self.path
    return in_dir(**kw)

  def link(self, dest: PATH_TYPES, follow: bool = False, **kw) -> str:
    """Создать символическую ссылку на объект"""
    kw["dest"] = dest
    kw["path"] = self.path
    r = link(**kw)
    if follow:
      self.path = r
    return r

  def move(self, dest: PATH_TYPES, follow: bool = True, **kw) -> str:
    """Переместить объект"""
    kw["dest"] = dest
    kw["path"] = self.path
    r = move(**kw)
    if follow:
      self.path = r
    return r

  def rename(self, name: str, follow: bool = True, **kw) -> str:
    """Переименовать объект"""
    kw["name"] = name
    kw["path"] = self.path
    r = rename(**kw)
    if follow:
      self.path = r
    return r

  def list_dir(self, **kw):
    """Список содержимого папки"""
    return ms.dir.list(self, **kw)

  def to_dict(self, hashes: list[str] = None) -> dict:
    """Создать словарь с данными объекта (совсестим с JSON)"""
    result = {}
    result["path"] = self.path
    if self.exists:
      result["created_at"] = self.created_at
      result["exists"] = True
      result["hashes"] = self.multi_hash_hex(hashes)
      result["is_link"] = self.is_link
      result["modified_at"] = self.modified_at
      result["realpath"] = self.realpath
      result["size"] = self.size if self.type == "file" else None
      result["type"] = self.type
      result["used_at"] = self.used_at
    else:
      result["exists"] = False
      for i in ("created_at", "hashes", "is_link", "modified_at", "realpath", "size", "type", "used_at"):
        result[i] = None
    return result

  def list_dir_iter(self, **kw):
    """Итератор по списку содержимого папки"""
    return ms.dir.list_iter(self, **kw)

  def open_file(self, mode: str = "r", **kw) -> IO[str] | IO[bytes]:
    """Открыть файл на чтение/запись"""
    return open(self, mode, **kw)

  def hash(self, algorithm: str) -> bytes:
    """Хеш файла в байтах"""
    import hashlib
    hash = hashlib.new(algorithm)
    with self.open_file("rb") as f:
      for i in f:
        hash.update(i)
    return hash.digest()

  def hash_hex(self, algorithm: str) -> str:
    """Хеш файла в HEX строке"""
    return self.hash(algorithm).hex()

  def multi_hash(self, algorithms: list[str]) -> dict[str, bytes]:
    """Хеш файла в байтах для нескольких алгоритмов"""
    if not algorithms:
      return {}
    import hashlib
    hashes = {i: hashlib.new(i) for i in algorithms}
    with self.open_file("rb") as f:
      for i in f:
        for j in hashes.values():
          j.update(i)
    return {i: j.digest() for i, j in hashes.items()}

  def multi_hash_hex(self, algorithms: list[str]) -> dict[str, str]:
    """Хеш файла в HEX строке для нескольких алгоритмов"""
    return {k: v.hex() for k, v in self.multi_hash(algorithms).items()}


class Stat:
  """Состояние объекта на диске"""

  def __init__(self, data: os.stat_result):
    self._atime_dt = None
    self._ctime_dt = None
    self._mtime_dt = None
    self.data = data
    self.atime: float = self.data.st_atime
    self.ctime: float = self.data.st_birthtime if sys.version_info >= (3, 12) and sys.platform == "win32" else self.data.st_ctime
    self.dev: int = self.data.st_dev
    self.group_id: int = self.st_gid
    self.inode: int = self.data.st_ino
    self.is_dir: bool = stat.S_ISDIR(self.data.st_mode)
    self.is_file: bool = stat.S_ISREG(self.data.st_mode)
    self.mtime: float = self.data.st_mtime
    self.size: int = self.data.st_size
    self.user_id: int = self.data.st_uid

  def __eq__(self, other):
    if isinstance(other, Stat):
      return os.path.samestat(self.data, other.data)
    if isinstance(other, os.stat_result):
      return os.path.samestat(self.data, other)
    return NotImplemented

  @property
  def atime_dt(self) -> datetime:
    """Дата последнего доступа к файлу"""
    if self._atime_dt is None:
      self._atime_dt = datetime.fromtimestamp(self.atime)
    return self._atime_dt

  @property
  def ctime_dt(self) -> datetime:
    """Дата создания файла"""
    if self._ctime_dt is None:
      self._ctime_dt = datetime.fromtimestamp(self.ctime)
    return self._ctime_dt

  @property
  def mtime_dt(self) -> datetime:
    """Дата изменения файла"""
    if self._mtime_dt is None:
      self._mtime_dt = datetime.fromtimestamp(self.mtime)
    return self._mtime_dt

  @classmethod
  def load(cls, path: str, **kw):
    """Получить из локального файла"""
    return cls(os.stat(path, **kw))


def copy(path: PATH_TYPES, dest: PATH_TYPES, mkdir: bool = False, **kw) -> str:
  """Копировать объект"""
  kw["dst"] = path2str(dest)
  kw["src"] = path2str(path)
  if mkdir:
    ms.dir.create(os.path.dirname(kw["dst"]))
  if os.path.isfile(kw["src"]):
    shutil.copy(**kw)
    return kw["dst"]
  if os.path.isdir(kw["src"]):
    shutil.copytree(**kw)
    return kw["dst"]


def delete(path: PATH_TYPES, **kw):
  """Удалить объект с содержимым"""
  kw["path"] = path2str(path)
  if os.path.islink(kw["path"]):
    return os.unlink(**kw)
  if os.path.isdir(kw["path"]):
    return shutil.rmtree(**kw)
  if os.path.isfile(kw["path"]):
    return os.remove(**kw)


def exists(path: PATH_TYPES) -> bool:
  """Существует ли объект"""
  return os.path.exists(path2str(path))


def in_dir(path: str, dir: str, recursion_limit: int = 1000) -> bool:
  """Находится ли объект в указанной папке"""
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
  """Является ли объект папкой"""
  return os.path.isdir(path2str(path))


def is_file(path: PATH_TYPES) -> bool:
  """Является ли объект файлом"""
  return os.path.isfile(path2str(path))


def is_link(path: PATH_TYPES) -> bool:
  """Является ли объект ссылкой на другой объект"""
  return os.path.islink(path2str(path))


def link(path: PATH_TYPES, dest: PATH_TYPES, force: bool = False, mkdir: bool = False, **kw) -> str:
  """Сделать символическую ссылку на объект"""
  kw["dst"] = path2str(dest, True)
  kw["src"] = path2str(path, True)
  if force:
    mkdir = True
    if exists(kw["dst"]):
      delete(kw["dst"])
  if mkdir:
    ms.dir.create(os.path.dirname(kw["dst"]))
  os.symlink(**kw)
  return kw["dst"]


def move(path: PATH_TYPES, dest: PATH_TYPES, force: bool = False, mkdir: bool = False, **kw) -> str:
  """Переместить объект"""
  kw["dst"] = path2str(dest)
  kw["src"] = path2str(path)
  if force:
    mkdir = True
    if exists(kw["dst"]):
      delete(kw["dst"])
  if mkdir:
    ms.dir.create(os.path.dirname(kw["dst"]))
  shutil.move(**kw)
  return kw["dst"]


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw) -> str:
  """Переименовать объект"""
  kw["path"] = path
  kw["dest"] = os.path.dirname(path2str(path)) + "/" + name
  return move(**kw)


class TempFiles:
  """Удаление временных файлов по окончании операций с `with`"""

  def __init__(self, *files: PATH_TYPES):
    self.files: list[str] = []
    self.add(*files)

  def __enter__(self):
    return self

  def __exit__(self, a, b, c):
    self.remove_files()

  def __contains__(self, k):
    return k in self.files

  def __delitem__(self, k):
    if type(k) == str:
      k = self.files.index(k)
    del self.files[k]

  def add(self, *files: PATH_TYPES):
    """Добавить файлы в список временных"""
    for i in files:
      path = path2str(i, to_abs=True)
      if not path in self.files:
        self.files.append(path)

  def remove_files(self, ignore_errors: bool = True):
    """Удалить все временные файлы"""
    for i in self.files:
      try:
        delete(i)
      except Exception:
        if not ignore_errors:
          raise


def _rec_readlink(path: str, hist: list[str] = None) -> str:
  if hist is None:
    hist = [path]
  while os.path.islink(path):
    path = os.path.realpath(path).replace("\\", "/")
    if path in hist:
      raise RecursionError()
    hist.append(path)
  return path


def readlink(path: PATH_TYPES, recursive: bool = False) -> str:
  path = path2str(path, True)
  if recursive:
    return _rec_readlink(path)
  if not os.path.islink(path):
    return path
  return os.path.realpath(path)


cp = copy
ln = link
mv = move
rm = delete
rn = rename
