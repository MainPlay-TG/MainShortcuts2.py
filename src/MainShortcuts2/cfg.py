import os
from .core import ms
from .path import PATH_TYPES, path2str
from typing import *
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
  if not type is None:
    type = type.lower()
    if not type in types:
      raise Exception("Type %r not supported" % type)
    return type
  _, ext = os.path.splitext(path)
  ext = ext[1:].lower()
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
  """Загрузка, использование и сохранение конфигов"""
  # 2.0.0

  def __init__(self, path: PATH_TYPES, data: dict = None, default: dict = None, type: str = None):
    self.data = {} if data is None else data
    self.default = {} if default is None else default
    self.path = path2str(path, True)
    self.type = _check_type(path, type)
    self._load_func, self._save_func = _load_type(self)

  def load(self, **kw):
    """Загрузить конфиг из файла"""
    self.data = self._load_func(**kw)
  read = load

  def save(self, **kw) -> int:
    """Сохранить конфиг в файл"""
    return self._save_func(**kw)
  write = save

  def fill_defaults(self, save_if_edited: bool = False):
    """Заполнить пустые значения значениями по умолчанию"""
    edited = False
    for i in self.default:
      if not i in self:
        edited = True
        self[i] = self.default[i]
    if edited and save_if_edited:
      self.save()

  def dload(self, save_if_edited: bool = False, **kw):
    """Загрузить конфиг если файл существует, и заполнить пустые значения"""
    if os.path.isfile(self.path):
      self.load(**kw)
    else:
      self.data = {}
    self.fill_defaults(save_if_edited)

  def __contains__(self, k):
    return k in self.data

  def __delitem__(self, k):
    del self.data[k]

  def __getitem__(self, k):
    return self.data[k]

  def __setitem__(self, k, v):
    self.data[k] = v

  def get(self, k, default=None):
    """Если значение существует, получить его"""
    return self[k] if k in self else default

  def items(self):
    """dict.items()"""
    return self.data.items()

  def keys(self):
    """dict.keys()"""
    return self.data.keys()

  def values(self):
    """dict.values()"""
    return self.data.values()
