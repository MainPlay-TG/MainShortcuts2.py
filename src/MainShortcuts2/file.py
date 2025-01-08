"""Работа только с файлами"""
import builtins
import os
import shutil
from .core import ms
from .path import PATH_TYPES, path2str
from .types import NotAFileError
from typing import *
TMP_SUFFIX = ".MS2_TMP"


def _check(path, **kw) -> str:
  kw["path"] = path
  path = path2str(**kw)
  if os.path.exists(path):
    if not os.path.isfile(path):
      raise NotAFileError(path)
    path = os.path.realpath(path)
  return path


def read(path: PATH_TYPES, encoding: str = None, **kw) -> str:
  """Получить текст из файла"""
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = _check(path)
  kw["mode"] = "r"
  with builtins.open(**kw) as f:
    return f.read()


def write(path: PATH_TYPES, data: str, encoding: str = None, mkdir: bool = False, use_tmp_file: bool = None, **kw) -> int:
  """Записать текст в файл"""
  file = _check(path)
  if use_tmp_file is None:
    use_tmp_file = ms.use_tmp_file
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = file
  kw["mode"] = "w"
  if mkdir:
    dir = os.path.dirname(kw["file"])
    if not os.path.isdir(dir):
      os.makedirs(dir)
  if use_tmp_file:
    kw["file"] += TMP_SUFFIX
  with builtins.open(**kw) as f:
    result = f.write(data)
  if use_tmp_file:
    os.remove(file)
    shutil.move(kw["file"], file)
  return result


def load(path: PATH_TYPES, **kw) -> bytes:
  """Получить байты из файла"""
  kw["file"] = _check(path)
  kw["mode"] = "rb"
  with builtins.open(**kw) as f:
    return f.read()


def save(path: PATH_TYPES, data: bytes, mkdir: bool = False, use_tmp_file: bool = None, **kw) -> int:
  """Записать байты в файл"""
  file = _check(path)
  if use_tmp_file is None:
    use_tmp_file = ms.use_tmp_file
  kw["file"] = file
  kw["mode"] = "wb"
  if mkdir:
    dir = os.path.dirname(kw["file"])
    if not os.path.isdir(dir):
      os.makedirs(dir)
  if use_tmp_file:
    kw["file"] += TMP_SUFFIX
  with builtins.open(**kw) as f:
    result = f.write(data)
  if use_tmp_file:
    os.remove(file)
    shutil.move(kw["file"], file)
  return result


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


def compare(path1: PATH_TYPES, path2: PATH_TYPES, method: str = "bin") -> bool:
  """Одинаковые ли файлы (сравнение размера и содержимого)"""
  p1 = _check(path1)
  p2 = _check(path2)
  if os.path.getsize(p1) != os.path.getsize(p2):
    return False
  method = method.lower()
  if method in ["binary", "bin", "bytes"]:  # Сравнение по байтам
    with open(p1, "rb") as f1:
      with open(p2, "rb") as f2:
        for b1 in f1:
          l = len(b1)
          b2 = f2.read(l)
          if b1 != b2:
            return False
        return True
  from .__main__ import HASH_TYPES
  if method in HASH_TYPES:  # Сравнение контрольной суммы
    import hashlib
    Hash = hashlib.new(method)
    with open(p1, "rb") as f1:
      hash1 = Hash()
      for b1 in f1:
        hash1.update(b1)
    with open(p2, "rb") as f2:
      hash2 = Hash()
      for b2 in f2:
        hash2.update(b2)
    return hash1.digest() == hash2.digest()
  raise ValueError("Unknown method: " + repr(method))


cp = copy
ln = link
mv = move
rm = delete
rn = rename
