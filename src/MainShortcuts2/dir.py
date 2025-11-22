"""Работа только с папками"""
import builtins
import os
from .core import ms
from .path import Path, PATH_TYPES, path2str
from typing import *


class NotADirError(Exception):
  pass


def _check(path, real=False, **kw) -> str:
  path = path2str(path, **kw)
  if os.path.exists(path):
    if not os.path.isdir(path):
      raise NotADirError(path)
    if real:
      return os.path.realpath(path)
  return path


def create(path: PATH_TYPES, force: bool = False, *, _exists: set[str] = None, **kw):
  """Создать папку если её не существует"""
  exists = set() if _exists is None else _exists
  path = path2str(path)
  if path in exists:
    return ms.path.Path(path)
  if os.path.isdir(path):
    exists.add(path)
    return ms.path.Path(path)
  if force:
    if os.path.isfile(path):
      ms.file.delete(path)
  os.makedirs(_check(path), exist_ok=True, **kw)
  exists.add(path)
  return ms.path.Path(path)


def _list_filter(path: Path, *, exts: Iterable[str] = None, func: Callable[[Path], bool] = None, links: bool = None, type: str = None):
  if not exts is None:
    if not path.ext.lower() in exts:
      return False
  if not func is None:
    if not func(path):
      return False
  if not links is None:
    if path.is_link != links:
      return False
  if not type is None:
    if path.type != type:
      return False
  return True


def _prep_exts(exts: Iterable[str]) -> list[str] | None:
  if exts is None:
    return
  if isinstance(exts, str):
    exts = exts.split(",")
  result = []
  for i in exts:
    if i:
      if not i.startswith("."):
        i = "." + i
      result.append(i.lower())
  return result


def list_iter(path: PATH_TYPES = ".", *, exts: Iterable[str] = None, **kw):
  """Список содержимого папки (итератор)"""
  path = _check(path)
  if not exts is None:
    kw["exts"] = _prep_exts(exts)
    kw["type"] = Path.TYPE_FILE
  for i in os.listdir(path):
    i = Path(path + "/" + i)
    if _list_filter(i, **kw):
      yield i


def list(path: PATH_TYPES = ".", **kw) -> builtins.list[Path]:
  """Список содержимого папки"""
  return builtins.list(list_iter(path, **kw))


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Копировать папку"""
  return ms.path.copy(_check(path), dest, **kw)


def delete(path: PATH_TYPES, **kw):
  """Удалить папку с содержимым"""
  return ms.path.delete(_check(path), **kw)


def in_dir(path: str, dir: str, **kw) -> bool:
  """Находится ли папка в указанной папке"""
  return ms.path.in_dir(_check(path), dir, **kw)


def link(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Сделать символическую ссылку на папку"""
  return ms.path.link(_check(path), dest, **kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Переместить папку"""
  return ms.path.move(_check(path), dest, **kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  """Переименовать папку"""
  return ms.path.rename(_check(path), name, **kw)


class TempDir:
  """Временная папка, которая будет удалена по окончании использования (используйте через `with`)"""

  def __init__(self, path: PATH_TYPES = None, *, create: bool = True, ignore_error: bool = True):
    if path is None:
      import tempfile
      path = tempfile.mkdtemp(suffix="MS2_TMP")
    self.ignore_error = ignore_error
    self.path: str = path2str(path, True)
    if create:
      self.create()

  def __enter__(self):
    self.create()
    return self

  def __exit__(self, type, value, trace):
    if not value is None:
      if not self.ignore_error:
        return
    self.delete()

  def create(self):
    """Создать папку если она не существует"""
    ms.dir.create(self.path)

  def delete(self):
    """Удалить папку вместе с содержимым"""
    ms.path.delete(self.path)


def recursive_list_iter(path: PATH_TYPES, follow_links: bool = False, *, exts: Iterable[str] = None, on_error=None, top_down=True, **kw):
  """Рекурсивный список содержимого папки (итератор)"""
  allow_dirs = True
  allow_files = True
  if not exts is None:
    kw["exts"] = _prep_exts(exts)
    kw["type"] = Path.TYPE_FILE
  if kw.get("type") == Path.TYPE_DIR:
    allow_files = False
  if kw.get("type") == Path.TYPE_FILE:
    allow_dirs = False
  for root, dirnames, filenames in os.walk(path, followlinks=follow_links, onerror=on_error, topdown=top_down):
    if allow_dirs:
      for i in dirnames:
        i = Path(root + "/" + i)
        if _list_filter(i, **kw):
          yield i
    if allow_files:
      for i in filenames:
        i = Path(root + "/" + i)
        if _list_filter(i, **kw):
          yield i


def recursive_list(path: PATH_TYPES = ".", follow_links: bool = False, **kw) -> builtins.list[Path]:
  """Рекурсивный список содержимого папки"""
  return builtins.list(recursive_list_iter(path, follow_links, **kw))


cp = copy
ln = link
mv = move
rm = delete
rn = rename
