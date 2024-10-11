"""Работа только с файлами"""
import builtins
import os
from .core import ms
from .path import PATH_TYPES, path2str
from .types import NotAFileError
from typing import *


def _check(path, **kw) -> str:
  kw["path"] = path
  path = path2str(**kw)
  if os.path.exists(path):
    if not os.path.isfile(path):
      raise NotAFileError(path)
  return path


def read(path: PATH_TYPES, encoding: str = None, **kw) -> str:
  """Получить текст из файла"""
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = _check(path)
  kw["mode"] = "r"
  with builtins.open(**kw) as f:
    return f.read()


def write(path: PATH_TYPES, data: str, encoding: str = None, mkdir: bool = False, **kw) -> int:
  """Записать текст в файл"""
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = _check(path)
  kw["mode"] = "w"
  if mkdir:
    ms.dir.create(os.path.dirname(kw["file"]))
  with builtins.open(**kw) as f:
    return f.write(data)


def load(path: PATH_TYPES, **kw) -> bytes:
  """Получить байты из файла"""
  kw["file"] = _check(path)
  kw["mode"] = "rb"
  with builtins.open(**kw) as f:
    return f.read()


def save(path: PATH_TYPES, data: bytes, mkdir: bool = False, **kw) -> int:
  """Записать байты в файл"""
  kw["file"] = _check(path)
  kw["mode"] = "wb"
  if mkdir:
    ms.dir.create(os.path.dirname(kw["file"]))
  with builtins.open(**kw) as f:
    return f.write(data)


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Копировать файл"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.copy(**kw)


def delete(path: PATH_TYPES, **kw):
  """Удалить файл"""
  kw["path"] = _check(path)
  return ms.path.delete(**kw)


def in_dir(path: str, dir: str, **kw) -> bool:
  """Находится ли файл в указанной папке"""
  kw["dir"] = dir
  kw["path"] = _check(path)
  return ms.path.in_dir(**kw)


def link(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Сделать символическую ссылку на файл"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.link(**kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Переместить файл"""
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.move(**kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  """Переименовать файл"""
  kw["name"] = name
  kw["path"] = _check(path)
  return ms.path.rename(**kw)


cp = copy
ln = link
mv = move
rm = delete
rn = rename
