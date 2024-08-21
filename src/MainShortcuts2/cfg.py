import os
from .core import MS2
from .path import PATH_TYPES, path2str
from typing import *
ms: MS2 = None
# 2.0.0
types = ["json", "json5", "pickle", "toml"]
ext2type = {
    "json": "json",
    "json5": "json5",
    "pickle": "pickle",
    "pkl": "pickle",
    "toml": "toml",
}


def _check_type(path: str, type: Union[str, None]):
  type = type.lower()
  if not type is None:
    if not type in types:
      raise Exception("Type %r not supported" % type)
    return type
  _, ext = os.path.splitext(path).lower()
  if ext in ext2type:
    return ext2type[ext]
  raise Exception("Cannot determine type by extension %r" % ext)


def _load_type(cfg):
  path: str = cfg.path
  type: str = cfg.type
  if type == "json":
    def load(**kw):
      kw["like_json5"] = False
      kw["path"] = path
      return ms.json.read(**kw)

    def save(**kw):
      kw["data"] = cfg.data
      kw["path"] = path
      return ms.json.write(**kw)
  if type == "json5":
    def load(**kw):
      kw["like_json5"] = True
      kw["path"] = path
      return ms.json.read(**kw)

    def save(**kw):
      kw["data"] = cfg.data
      kw["path"] = path
      return ms.json.write(**kw)
  if type == "pickle":
    import pickle

    def load(**kw):
      with open(path, "rb") as f:
        kw["file"] = f
        return pickle.load(**kw)

    def save(**kw):
      buf = pickle.dumps(**kw)
      with open(path, "wb") as f:
        return f.write(buf)
  if type == "toml":
    import toml

    def load(encoding="utf-8", **kw):
      with open(path, "r", encoding=encoding) as f:
        kw["f"] = f
        return toml.load(**kw)

    def save(encoding="utf-8", **kw):
      kw["o"] = cfg.data
      buf = toml.dumps(**kw)
      with open(path, "w", encoding=encoding) as f:
        return f.write(buf)
  return load, save


class cfg:
  # 2.0.0
  def __init__(self, path: PATH_TYPES, data: dict = None, default: dict = None, type=None):
    self.data = {} if data is None else data
    self.default = {} if default is None else default
    self.path = path2str(path, True)
    self.type = _check_type(path, type)
    self._load_func, self._save_func = _load_type(self)

  def load(self, **kw):
    self.data = self._load_func(**kw)
  read = load

  def save(self, **kw) -> int:
    return self._save_func(**kw)
  write = save

  def fill_defaults(self):
    for i in self.default:
      if not i in self:
        self[i] = self.default[i]

  def dload(self, **kw):
    self.load(**kw)
    self.fill_defaults()

  def __contains__(self, k):
    return k in self.data

  def __delitem__(self, k):
    del self.data[k]

  def __getitem__(self, k):
    return self.data[k]

  def __setitem__(self, k, v):
    self.data[k] = v

  def items(self):
    return self.data.items()

  def keys(self):
    return self.data.keys()

  def values(self):
    return self.data.values()
