"""Работа только с файлами"""
import builtins
import os
import shutil
from .core import ms
from .path import PATH_TYPES, path2str
from .types import NotAFileError
from typing import *
from warnings import warn
TMP_SUFFIX = ".MS2_TMP"
CHUNK_SIZE = 64 * 1024


def _check(path, real=False, **kw) -> str:
  path = path2str(path, **kw)
  if os.path.exists(path):
    if not os.path.isfile(path):
      raise NotAFileError(path)
    if real:
      return os.path.realpath(path)
  return path


def _write(path, data, mode, mkdir=False, **kw):
  if "use_tmp_file" in kw:
    if not kw.pop("use_tmp_file"):
      # Записывать файл напрямую небезопасно, всегда использовать временный файл
      warn("Argument 'use_tmp_file' is deprecated, always use temporary file", DeprecationWarning)
  file = _check(path, True)
  if mkdir:
    os.makedirs(os.path.dirname(file), exist_ok=True)
  # Запись в временный файл
  tmp_file = file + TMP_SUFFIX
  with builtins.open(tmp_file, mode, **kw) as f:
    result = f.write(data)
  # Замена файла
  os.replace(tmp_file, file)
  return result


def read(path: PATH_TYPES, encoding: str = None, **kw) -> str:
  """Получить текст из файла"""
  kw["encoding"] = ms.encoding if encoding is None else encoding
  with builtins.open(_check(path), "r", **kw) as f:
    return f.read()


def write(path: PATH_TYPES, data: str, encoding: str = None, mkdir: bool = False, **kw) -> int:
  """Записать текст в файл"""
  kw.setdefault("newline", "\n")
  kw["encoding"] = ms.encoding if encoding is None else encoding
  return _write(path, data, "w", mkdir, **kw)


def load(path: PATH_TYPES, **kw) -> bytes:
  """Получить байты из файла"""
  with builtins.open(_check(path), "rb", **kw) as f:
    return f.read()


def save(path: PATH_TYPES, data: bytes, mkdir: bool = False, **kw) -> int:
  """Записать байты в файл"""
  return _write(path, data, "wb", mkdir, **kw)


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Копировать файл"""
  return ms.path.copy(_check(path), dest, **kw)


def delete(path: PATH_TYPES, **kw):
  """Удалить файл"""
  return ms.path.delete(_check(path), **kw)


def in_dir(path: str, dir: str, **kw) -> bool:
  """Находится ли файл в указанной папке"""
  return ms.path.in_dir(_check(path), dir, **kw)


def link(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Сделать символическую ссылку на файл"""
  return ms.path.link(_check(path), dest, **kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  """Переместить файл"""
  return ms.path.move(_check(path), dest, **kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  """Переименовать файл"""
  return ms.path.rename(_check(path), name, **kw)


def compare(path1: PATH_TYPES, path2: PATH_TYPES, method: str = "bin", chunk_size=CHUNK_SIZE) -> bool:
  """Одинаковые ли файлы (сравнение размера и содержимого)"""
  p1 = _check(path1)
  p2 = _check(path2)
  s1 = os.stat(p1)
  s2 = os.stat(p2)
  if os.path.samestat(s1, s2):
    return True
  if s1.st_size != s2.st_size:
    return False
  method = method.lower()
  if method in ["binary", "bin", "bytes"]:  # Сравнение по байтам
    with open(p1, "rb") as f1:
      with open(p2, "rb") as f2:
        while True:
          b1 = f1.read(chunk_size)
          b2 = f2.read(chunk_size)
          if b1 != b2:
            return False
          if not b1:
            break
    return True
  from .ms2hash import HASH_TYPES
  if method in HASH_TYPES:  # Сравнение контрольной суммы
    import hashlib
    with open(p1, "rb") as f1:
      hash1 = hashlib.new(method)
      while True:
        b1 = f1.read(chunk_size)
        if not b1:
          break
        hash1.update(b1)
    with open(p2, "rb") as f2:
      hash2 = hashlib.new(method)
      while True:
        b2 = f2.read(chunk_size)
        if not b2:
          break
        hash2.update(b2)
    return hash1.digest() == hash2.digest()
  raise ValueError("Unknown method: " + repr(method))


cp = copy
ln = link
mv = move
rm = delete
rn = rename
