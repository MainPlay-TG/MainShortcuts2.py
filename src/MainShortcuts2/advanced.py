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

    def cb_lines(text: list[str]) -> str:
      return "\n".join(text)

    def cb_normal(text: str) -> str:
      assert type(text) == str
      return text
    self.cache_builders["lines"] = cb_lines
    self.cache_builders["normal"] = cb_normal
    self.add_lang(None, default_lang, load=True)

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
