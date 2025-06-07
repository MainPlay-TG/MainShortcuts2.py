"""Работа только с папками"""
import builtins
import os
from .core import ms
from .path import Path, PATH_TYPES, path2str
from typing import *
# 2.0.0


class NotADirError(Exception):
  pass


def _check(path, **kw) -> str:
  kw["path"] = path
  path = path2str(**kw)
  if os.path.exists(path):
    if not os.path.isdir(path):
      raise NotADirError(path)
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
      ms.path.delete(path)
  kw["name"] = _check(path)
  os.makedirs(**kw)
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


def list_iter(path: PATH_TYPES = ".", *, exts: Iterable[str] = None, **kw):
  """Список содержимого папки (итератор)"""
  path = _check(path)
  kw["exts"] = None if exts is None else [(i if i.startswith(".") else "." + i).lower() for i in exts]
  for i in os.listdir(path):
    i = Path(path + "/" + i)
    if _list_filter(i, **kw):
      yield i


def list(path: PATH_TYPES = ".", **kw) -> builtins.list[Path]:
  """Список содержимого папки"""
  return builtins.list(list_iter(path, **kw))


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Копировать папку"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.copy(**kw)


def delete(path: PATH_TYPES, **kw):
  """Удалить папку с содержимым"""
  kw["path"] = _check(path)
  return ms.path.delete(**kw)


def in_dir(path: str, dir: str, **kw) -> bool:
  """Находится ли папка в указанной папке"""
  kw["dir"] = dir
  kw["path"] = _check(path)
  return ms.path.in_dir(**kw)


def link(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Сделать символическую ссылку на папку"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.link(**kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Переместить папку"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.move(**kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  """Переименовать папку"""
  kw["name"] = name
  kw["path"] = _check(path)
  return ms.path.rename(**kw)


class TempDir:
  """Временная папка, которая будет удалена по окончании использования (используйте через `with`)"""

  def __init__(self, path: PATH_TYPES, *, create: bool = True, ignore_error: bool = True):
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


def recursive_list_iter(path: PATH_TYPES, follow_links: bool = False, *, on_error=None, top_down=True, exts: Iterable[str] = None, **kw):
  """Рекурсивный список содержимого папки (итератор)"""
  kw["exts"] = None if exts is None else [(i if i.startswith(".") else "." + i).lower() for i in exts]
  for dirpath, dirnames, filenames in os.walk(path, followlinks=follow_links, onerror=on_error, topdown=top_down):
    for i in dirnames:
      i = Path(dirpath + "/" + i)
      if _list_filter(i, **kw):
        yield i
    for i in filenames:
      i = Path(dirpath + "/" + i)
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
