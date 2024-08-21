import builtins
import os
from .core import ms
from .path import PATH_TYPES, path2str
from typing import *
# 2.0.0


class NotAFileError(Exception):
  pass


def _check(path, **kw) -> str:
  kw["path"] = path
  path = path2str(**kw)
  if os.path.exists(path):
    if not os.path.isfile(path):
      raise NotAFileError(path)
  return path


def read(path: PATH_TYPES, encoding: str = None, **kw) -> str:
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = _check(path)
  kw["mode"] = "r"
  with builtins.open(**kw) as f:
    return f.read()


def write(path: PATH_TYPES, data: str, encoding: str = None, **kw) -> int:
  kw["encoding"] = ms.encoding if encoding is None else encoding
  kw["file"] = _check(path)
  kw["mode"] = "w"
  with builtins.open(**kw) as f:
    return f.write(data)


def load(path: PATH_TYPES, **kw) -> bytes:
  kw["file"] = _check(path)
  kw["mode"] = "rb"
  with builtins.open(**kw) as f:
    return f.read()


def save(path: PATH_TYPES, data: bytes, **kw) -> int:
  kw["file"] = _check(path)
  kw["mode"] = "wb"
  with builtins.open(**kw) as f:
    return f.write(data)


def copy(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.copy(**kw)


def delete(path: PATH_TYPES, **kw):
  kw["path"] = _check(path)
  return ms.path.delete(**kw)


def in_dir(path: str, dir: str, **kw) -> bool:
  kw["dir"] = dir
  kw["path"] = _check(path)
  return ms.path.in_dir(**kw)


def link(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.link(**kw)


def move(path: PATH_TYPES, dest: PATH_TYPES, **kw):
  kw["dest"] = dest
  kw["path"] = _check(path)
  return ms.path.move(**kw)


def rename(path: PATH_TYPES, name: PATH_TYPES, **kw):
  kw["name"] = name
  kw["path"] = _check(path)
  return ms.path.rename(**kw)


cp = copy
ln = link
mv = move
rm = delete
rn = rename
