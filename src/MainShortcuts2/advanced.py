import re
from .core import ms
from .path import Path
from typing import Any, Union


def _check_count(data):
  if len(data) == 0:
    raise ValueError("The list is empty")


class MultiLang:
  FORMAT = 1

  def __init__(self, default_lang: Union[dict, Path, str]):
    self.cache: dict[tuple[str, str, str], str] = {}
    self.cache_builders: dict = {}
    self.files: dict[str, Path] = {}
    self.langs: dict[Union[None, str], dict[str, dict[str, Any]]] = {}

    @self.add_cache_builder("lines")
    def _(text: list[str]) -> str:
      return "\n".join(text)

    @self.add_cache_builder("normal")
    def _(text: str) -> str:
      assert type(text) == str
      return text
    self.add_lang(None, default_lang, load=True)

  def add_cache_builder(self, name: str):
    def deco(func):
      self.cache_builders[name] = func
      return func
    return deco

  def add_langs(self, langs: dict[str, Union[dict, Path, str]], check_count: bool = True, load: bool = True):
    """Добавить языки (`dict`) или пути к языковым файлам (`str`, `ms.path.Path`)"""
    if check_count:
      _check_count(langs)
    for k, v in langs.items():
      self.add_lang(k, v, load=load)

  def add_lang(self, lang_name: str, lang: Union[dict, Path, str], load: bool = True):
    """Добавить один язык из словаря или пути к файлу"""
    if type(lang) == dict:
      for cat_name, cat in lang.items():
        assert type(cat_name) == str
        assert type(cat) == dict
        for text_name, text in cat.items():
          assert type(text_name) == str
          if type(text) == dict:
            if not "allow_cache" in text:
              text["allow_cache"] = True
            if not "type" in text:
              text["type"] = "normal"
      self.langs[lang_name] = lang
      return
    if type(lang) == str:
      lang = Path(lang)
    if type(lang) == Path:
      self.files[lang_name] = lang
      if load:
        self.load(lang_name)
      return

  def load(self, *names: Union[None, str], check_count: bool = True):
    """Загрузить языковые файлы"""
    if check_count:
      _check_count(names)
    for i in names:
      path = self.files[i].path
      data = ms.json.read(path)
      self.add_lang(i, data["texts"])

  def save(self, *names: Union[None, str], check_count: bool = True, **kw) -> int:
    """Сохранить языковые файлы"""
    if check_count:
      _check_count(names)
    data = {"format": "MainShortcuts2.advanced.MultiLang/%i" % self.FORMAT}
    sum = 0
    for i in names:
      data["texts"] = self.langs[i]
      kw["data"] = data
      kw["path"] = self.files[i].path
      sum += ms.json.write(**kw)
    return sum

  def build_cache(self, lang_name: Union[None, str], cat_name: str, text_name: str):
    cache_name = (lang_name, cat_name, text_name)
    if cache_name in self.cache:
      return
    text = self.langs[lang_name][cat_name][text_name]
    if type(text) == str:
      self.cache[cache_name] = text
      return
    builder = self.cache_builders[text["type"]]
    result = builder(text)
    assert type(result) == str
    self.cache[cache_name] = result

  def get_text(self, cat: str, name: str, values=None, *, lang: str = None) -> str:
    if not lang in self.langs:
      self.load(lang)
    raw = self.langs[cat][name]
    if type(raw) == str:
      text = raw
    else:
      if raw.get("allow_cache") == False:
        text = self.cache_builders[raw["type"]](raw)
      else:
        self.build_cache(lang, cat, raw)
        text = self.cache[lang, cat, name]
    if values is None:
      return text
    return text % values


class PermissionSystem:
  FORMAT = 1

  def __init__(self, path: str):
    self.path = Path(path)
    self.load()

  def load(self):
    data = ms.json.read(self.path.path)
    self.default_groups = data["default_groups"] if "default_groups" in data else []
    self.default_perms = data["default_perms"] if "default_perms" in data else {}
    self.groups = {}
    self.users = {}
    for i in ["all", "group", "user"]:
      if not i in self.default_perms:
        self.default_perms[i] = {}
    if "groups" in data:
      for name, item in data["groups"].items():
        if not "admin" in item:
          item["admin"] = False
        if not "perms" in item:
          item["perms"] = self.default_perms["all"].copy()
          item["perms"].update(self.default_perms["groups"])
        if not "priority" in item:
          item["priority"] = 0
        self.groups[name] = item
    if "users" in data:
      for name, item in data["users"].items():
        if not "admin" in item:
          item["admin"] = False
        if not "groups" in item:
          item["groups"] = self.default_groups
        if not "perms" in item:
          item["perms"] = self.default_perms["all"].copy()
          item["perms"].update(self.default_perms["users"])
        self.groups[name] = item

  def save(self, **kw):
    kw["path"] = self.path.path
    kw["data"] = {"format": "MainShortcuts2.advanced.PermissionSystem/%i" % self.FORMAT}
    kw["data"]["default_groups"] = self.default_groups
    kw["data"]["default_perms"] = self.default_perms
    kw["data"]["groups"] = self.groups
    kw["data"]["users"] = self.users
    return ms.json.write(**kw)

  def _i_compare(self, perms: dict[str, bool], perm: str) -> bool:
    for k, v in perms:
      if re.match(k, perm):
        return v

  def _verify(self, username: str, permname: str) -> bool:
    if not username in self.users:
      return False
    user = self.users[username]
    if user["admin"]:
      return True
    if permname in user["perms"]:
      return user["perms"][permname]
    group = None
    for i in user["groups"]:
      if i in self.groups:
        if self.groups[i]["admin"]:
          return True
        if permname in self.groups[i]["perms"]:
          if group is None:
            group = self.groups[i]
            continue
          if self.groups[i]["priority"] > group["priority"]:
            group = self.groups[i]
            continue
    if group is None:
      return False
    return group["perms"][permname]

  def verify(self, username: str, permname: str, raise_error: bool = True) -> bool:
    """Проверить есть ли у пользователя данное право. Если пользователь является админом или одна из его групп даёт разрешения админа, права есть. Если права не указаны в пользователе, используются права группы с наивысшим приоритетом, в которой указано это право. Если ни у одной группы нет права, значит права отсутствуют"""
    result = self._verify(username, permname)
    if raise_error:
      if not result:
        raise ms.types.AccessDeniedError(username, permname)
    return result

  def add_group(self, name: str, perms: dict[str, bool] = None, *, add_defaults_perms: bool = True, admin: bool = False, priority: int = 0):
    group = {
        "admin": admin,
        "perms": {} if perms is None else perms.copy(),
        "priority": priority,
    }
    if add_defaults_perms:
      for i in self.default_perms["all"]:
        if not i in group["perms"]:
          group["perms"][i] = self.default_perms["all"][i]
      for i in self.default_perms["group"]:
        if not i in group["perms"]:
          group["perms"][i] = self.default_perms["group"][i]
    self.groups[name] = group

  def add_user(self, name: str, perms: dict[str, bool] = None, *, add_defaults_perms: bool = True, admin: bool = False, groups: list[str] = None):
    user = {
        "admin": admin,
        "groups": [] if groups is None else groups,
        "perms": {} if perms is None else perms.copy(),
    }
    if add_defaults_perms:
      for i in self.default_perms["all"]:
        if not i in user["perms"]:
          user["perms"][i] = self.default_perms["all"][i]
      for i in self.default_perms["user"]:
        if not i in user["perms"]:
          user["perms"][i] = self.default_perms["user"][i]
    self.users[name] = user

  def edit_group(self, name: str, *, admin: bool = None, perms: dict[str, Union[None, bool]] = None, priority: int = None):
    group = self.groups[name]
    if not admin is None:
      group["admin"] = bool(admin)
    if not priority is None:
      group["priority"] = int(priority)
    if not perms is None:
      for k, v in perms.items():
        if v is None:
          if k in group["perms"]:
            del group["perms"][k]
          else:
            group["perms"][k] = v

  def edit_user(self, name: str, *, admin: bool = None, groups: list[str] = None, perms: dict[str, Union[None, bool]] = None):
    user = self.users[name]
    if not admin is None:
      user["admin"] = bool(admin)
    if not groups is None:
      for i in groups:
        assert type(i) == str
      user["groups"] = groups
    if not perms is None:
      for k, v in perms.items():
        if v is None:
          if k in user["perms"]:
            del user["perms"][k]
          else:
            user["perms"][k] = v


class DictScriptAction:
  def __init__(self, name: str, args: list = None, kwargs: dict = None, save_to: str = None, comment: str = None):
    self.__getitem__ = self.__getattr__
    self.args: list = args
    self.comment: str = comment
    self.kwargs: dict = kwargs
    self.name: str = name
    self.save_to: str = save_to

  @classmethod
  def from_dict(cls, data: dict):
    kw = {}
    for k in ["args", "comment", "kwargs", "name", "save_to"]:
      kw[k] = data.get(k)
    return cls(**kw)

  def to_dict(self) -> dict:
    result = {}
    for k in ["args", "comment", "kwargs", "name", "save_to"]:
      v = getattr(self, k)
      if not v is None:
        result[k] = v
    return result


class DictScriptVariable:
  def __init__(self, name: str):
    self.name: str = name


@ms.any2json.reg_decoder(DictScriptVariable)
def _(obj):
  return DictScriptVariable(obj)


@ms.any2json.reg_encoder(DictScriptVariable)
def _(obj: DictScriptVariable):
  if isinstance(obj, DictScriptVariable):
    return obj.name


class DictScriptRunner:
  VERSION = 1

  def __init__(self, functions: dict = None, add_default_functions: bool = True):
    self.globals = {}
    if add_default_functions:
      import time
      for i in [bool, bytes, dict, float, int, list, str, tuple]:
        self.reg_class()(i)
      self.reg_function("sleep")(time.sleep)
      self.reg_function("sum")(sum)
      self.reg_function("time.sleep")(time.sleep)
      self.reg_function("time.time")(time.time)
    if not functions is None:
      for name, func in functions.items():
        self.reg_function(name)(func)

  def reg_class(self, name: str = None, overwrite: bool = False):
    if not name is None:
      import warnings
      warnings.warn("The argument 'name' temporarily does not work", FutureWarning)

    def deco(cls: type) -> type:
      name = cls.__module__ + "." + cls.__name__
      if callable(cls):
        self.reg_function(name, overwrite=overwrite)(cls)
      for k in dir(cls):
        v = getattr(cls, k)
        if callable(v):
          self.reg_function(name + "." + k, overwrite=overwrite)
      return cls
    return deco

  def reg_function(self, name: str, overwrite: bool = False):
    if not overwrite:
      if name in self.globals:
        raise ValueError("The %r function already exists. Perhaps you wanted to overwrite it?" % name)

    def deco(func):
      if not callable(func):
        raise TypeError("Function %r is not callable" % name)
      self.globals[name] = func
      return func
    return deco

  def run_script(self, script: list[dict]) -> dict:
    """Выполнить скрипт (список действий)"""
    for act in script:
      if not act["name"] in self.globals:
        raise KeyError("Function %r not exists" % act["name"])
    locals = self.globals.copy()
    for act in script:
      if act["name"] == "exit":
        break
      args = act["args"] if "args" in act else []
      func = locals[act["name"]]
      kwargs = act["kwargs"] if "kwargs" in act else {}
      result = func(*args, **kwargs)
      if "save_to" in act:
        locals[act["save_to"]] = result
    return locals


class CodeModule:
  """Импорт модуля из исходного кода. Могут быть баги"""

  def __init__(self, source: str, globals: dict = None, locals: dict = None):
    if globals is None:
      globals = {}
    if locals is None:
      locals = {}
    args = (source, globals, locals)
    exec(*args)
    self.__dict__["source"] = args[0]
    self.__dict__["globals"] = args[1]
    self.__dict__["globals"].update(args[2])

  def __delattr__(self, k):
    del self.__dict__["globals"][k]

  def __dir__(self) -> list[str]:
    return list(self.__dict__["globals"])

  def __getattr__(self, k):
    return self.__dict__["globals"][k]

  def __hasattr__(self, k) -> bool:
    return k in self.__dict__["globals"]

  def __setattr__(self, k, v):
    self.__dict__["globals"][k] = v
