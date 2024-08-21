import os
from .core import MS2
from .path import Path, PATH_TYPES, path2str
from typing import *
ms: MS2 = None
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


def create(path: PATH_TYPES, force: bool = True, **kw):
  path = path2str(path)
  if os.path.isdir(path):
    return
  if force:
    if os.path.isfile(path):
      ms.path.delete(path)
  kw["name"] = _check(path)
  os.makedirs(**kw)


def _list_filter(path: Path, *, exts: Iterable[str], func: Callable[[Path], bool], links: bool, type: str):
  if not exts is None:
    if not path.ext in exts:
      return False
  if not func is None:
    if not func(path):
      return False
  if not links is None:
    if os.path.islink(path.path) != links:
      return False
  if not type is None:
    if path.type != type:
      return False
  return True


def list(path: PATH_TYPES = ".", *, exts: Iterable[str] = None, func: Callable[[Path], bool] = None, links: bool = None, type: str = None) -> list[Path]:
  r = []
  kw = {}
  kw["exts"] = list(exts)
  kw["func"] = func
  kw["links"] = bool(links)
  kw["type"] = type
  for i in os.listdir(_check(path)):
    i = Path(i)
    if _list_filter(i, **kw):
      r.append(i)
  return i


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
