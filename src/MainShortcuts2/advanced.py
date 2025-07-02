import inspect
import os
import re
import subprocess
import sys
from .core import ms
from .path import Path
from typing import IO, Any, Union


def _check_count(data):
  if len(data) == 0:
    raise ValueError("The list is empty")
  return data


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
    if isinstance(lang, dict):
      for cat_name, cat in lang.items():
        assert isinstance(cat_name, str)
        assert isinstance(cat, dict)
        for text_name, text in cat.items():
          assert isinstance(text_name, str)
          if isinstance(text, dict):
            if not "allow_cache" in text:
              text["allow_cache"] = True
            if not "type" in text:
              text["type"] = "normal"
      self.langs[lang_name] = lang
      return
    if isinstance(lang, str):
      lang = Path(lang)
    if isinstance(lang, Path):
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


class FileDownloader(ms.ObjectBase):
  """Функциональное скачивание данных по HTTP"""
  EVENT_STARTING = 0
  """Перед отправкой запроса"""
  EVENT_STARTED = 1
  """После отправки запроса"""
  EVENT_DOWNLOADING = 2
  """Во время скачивания"""
  EVENT_COMPLETE = 3
  """Успешно завершено"""
  EVENT_ERROR = 4
  """Завершено с ошибкой"""
  EVENT_END = 5
  """Завершено (в любом случае)"""
  EVENT_NAMES = {0: "STARTING", 1: "STARTED", 2: "DOWNLOADING", 3: "COMPLETE", 4: "ERROR", 5: "END"}

  class CancelError(BaseException):
    pass

  def __init__(self, *, log=ms.log, **req_kw):
    import requests
    self.chunk_size = 16384  # 16 KB
    self.handlers: dict[int, list] = {}
    self.log = log
    self.req_kw = req_kw
    if not "session" in self.req_kw:
      self.req_kw["session"] = requests.Session()

  def _run_handlers(self, event: int, data: dict):
    if not data["enable_handlers"]:
      return
    data["event"] = event
    for func in self.handlers.get(event, []):
      try:
        func(**data)
      except self.CancelError:
        self.log.error("Handler %s canceled downloading on event %s", func, self.EVENT_NAMES.get(event, event))
      except Exception as exc:
        self.log.exception("Exception in handler %s on event %r", func, self.EVENT_NAMES.get(event, event), exc_info=exc)
    if event in {self.EVENT_COMPLETE, self.EVENT_ERROR}:
      self._run_handlers(self.EVENT_END, data)

  def add_handler(self, event: int):
    """Добавить обработчик евента"""
    self.handlers.setdefault(event, [])

    def deco(func):
      spec = inspect.getfullargspec(func)
      if not spec.varkw:
        raise TypeError("Handler should have an argument like **kwargs")
      self.handlers[event].append(func)
      return func
    return deco

  def _check_resume_support(self, data=None, func=None, io=None, **kw):
    return ms.utils.http_check_range_support(**kw)

  def download2file(self, url: str, path: str, *, resume: bool = False, **kw):
    """Скачать данные в файл"""
    real_path = ms.path.path2str(path)
    kw.setdefault("data", {})
    kw["data"]["real_path"] = real_path
    kw["url"] = url
    if resume and os.path.exists(real_path):
      if not self._check_resume_support(**kw):
        kw["path"] = real_path
        kw["resume"] = False
        return self.download2file(**kw)
      kw.setdefault("headers", {})
      kw["headers"]["Range"] = "bytes=%s-" % os.path.getsize(real_path)
      with open(real_path, "ab") as f:
        kw["io"] = f
        return self.download2io(**kw)
    tmp_path = real_path + ".ms2downloading"
    kw["data"]["tmp_path"] = tmp_path
    with open(tmp_path, "wb") as f:
      kw["io"] = f
      self.download2io(**kw)
    ms.file.move(tmp_path, real_path)
    return kw["data"]

  def download2io(self, url: str, io: IO[bytes], **kw):
    """Скачать данные в объект типа BytesIO"""
    kw.setdefault("data", {})
    kw["data"]["io"] = io
    kw["func"] = io.write
    kw["url"] = url
    return self.download2func(**kw)

  def download2null(self, url: str, **kw):
    """Скачать данные в пустоту"""
    kw["func"] = ms.utils.return_None
    kw["url"] = url
    return self.download2func(**kw)

  def download2func(self, url: str, func, *, data: dict = None, enable_handlers: bool = True, **kw):
    """Скачать данные в функцию, которая принимает чанки байтов"""
    for k, v in self.req_kw.items():
      if k in {"headers", "params"}:
        if not v is None:
          kw.setdefault(k, {})
          for k2, v2 in v.items():
            kw[k].setdefault(k2, v2)
      else:
        kw.setdefault(k, v)
    if data is None:
      data = {}
    data["chunk_count"] = 0
    data["data"] = data
    data["downloaded"] = 0
    data["downloader"] = self
    data["enable_handlers"] = enable_handlers
    data["errored"] = False
    data["func"] = func
    data["req_kw"] = kw
    data["started_at"] = ms.now
    data["url"] = url
    kw.setdefault("method", "GET")
    kw["stream"] = True
    kw["url"] = url
    self._run_handlers(self.EVENT_STARTING, data)
    try:
      with ms.utils.sync_request(**kw) as resp:
        data["connected_at"] = ms.now
        data["resp"] = resp
        data["total_size"] = resp.headers.get("Content-Length")  # None|int
        self._run_handlers(self.EVENT_STARTED, data)
        for chunk in resp.iter_content(self.chunk_size):
          data["chunk_count"] += 1
          data["chunk"] = chunk
          data["downloaded"] += len(chunk)
          func(chunk)
          self._run_handlers(self.EVENT_DOWNLOADING, data)
    except BaseException as exc:
      data["errored_at"] = ms.now
      data["errored"] = True
      data["exception"] = exc
      self.log.error("Failed to download")
      self._run_handlers(self.EVENT_ERROR, data)
      raise
    data["completed_at"] = ms.now
    self._run_handlers(self.EVENT_COMPLETE, data)
    return data

  def h_limit_size(self, max_size: int):
    @self.add_handler(self.EVENT_STARTED)
    def h_limit_size_start(total_size: None | int, **kw):
      if total_size:
        if total_size > max_size:
          raise self.CancelError()

    @self.add_handler(self.EVENT_DOWNLOADING)
    def h_limit_size_progress(downloaded: int, **kw):
      if downloaded > max_size:
        raise self.CancelError()

  def h_hash(self, hash_name: str, data_name: str = None, **hash_kw):
    import hashlib
    hash_type: type[hashlib._Hash] = getattr(hashlib, hash_name.lower())
    if data_name is None:
      data_name = hash_name
    data_name_h = data_name + "_h"

    @self.add_handler(self.EVENT_STARTED)
    def h_hash_start(**kw):
      kw[data_name_h] = hash_type(**hash_kw)

    @self.add_handler(self.EVENT_DOWNLOADING)
    def h_hash_update(chunk: bytes, **kw):
      kw[data_name_h].update(chunk)

    @self.add_handler(self.EVENT_COMPLETE)
    def h_hash_complete(data: dict, **kw):
      digest = kw[data_name_h].digest()
      data[data_name] = digest.hex()
      data[data_name + "_b"] = digest
    return data_name

  def h_progressbar(self, data_name="h_progressbar", **pbar_kw):
    import progressbar
    pbar_kw.setdefault("min_poll_interval", 0.5)

    @self.add_handler(self.EVENT_STARTED)
    def h_pbar_start(total_size: None | int, data: dict, **kw):
      data[data_name] = progressbar.ProgressBar(**pbar_kw).start(total_size)

    @self.add_handler(self.EVENT_DOWNLOADING)
    def h_pbar_update(downloaded: int, **kw):
      kw[data_name].update(downloaded)

    @self.add_handler(self.EVENT_END)
    def h_pbar_complete(errored: bool, **kw):
      kw[data_name].finish(dirty=errored)
    return data_name


class PlatformInfo(ms.ObjectBase):
  def __init__(self):
    import platform
    self.is_linux: bool = sys.platform == "linux"
    self.is_macos: bool = sys.platform == "darwin"
    self.is_windows: bool = sys.platform == "win32"
    self.is_android: bool = self.is_linux and "ANDROID_ROOT" in os.environ
    self.is_termux: bool = self.is_linux and "TERMUX_VERSION" in os.environ
    self.arch = platform.machine().lower()
    self.cpu = platform.processor().lower()
    self.home = ms.path.Path(os.path.expanduser("~"))
    self.name = platform.system().lower()
    self.version = platform.version().lower()


class _Platform(PlatformInfo):
  def __init__(self):
    PlatformInfo.__init__(self)
    self._created_dirs = set()

  def _run(self, *args, **kw):
    kw.setdefault("check", True)
    kw.setdefault("shell", True)
    kw["args"] = args
    return subprocess.run(**kw)

  def hibernate(self) -> None:
    """Перевести устройство в режим гиберации"""
    raise RuntimeError("Unsupported platform")

  def poweroff(self) -> None:
    """Отключить устройство"""
    raise RuntimeError("Unsupported platform")

  def reboot(self) -> None:
    """Перезагрузить устройство"""
    raise RuntimeError("Unsupported platform")

  def sleep(self) -> None:
    """Перевести устройство в спящий режим"""
    raise RuntimeError("Unsupported platform")


class PlatformLinux(_Platform):
  @property
  def root_dir(self):
    return ms.path.Path("/")

  @property
  def system_bin_dir(self):
    return ms.dir.create(self.root_dir + "/usr/local/bin", _exists=self._created_dirs)

  @property
  def system_cache_dir(self):
    return ms.dir.create(self.root_dir + "/var/cache", _exists=self._created_dirs)

  @property
  def system_config_dir(self):
    return ms.dir.create(self.root_dir + "/etc", _exists=self._created_dirs)

  @property
  def system_data_dir(self):
    return ms.dir.create(self.root_dir + "/usr/share", _exists=self._created_dirs)

  @property
  def system_lib_dir(self):
    return ms.dir.create(self.root_dir + "/lib", _exists=self._created_dirs)

  @property
  def system_log_dir(self):
    return ms.dir.create(self.root_dir + "/var/log", _exists=self._created_dirs)

  @property
  def user_bin_dir(self):
    return ms.dir.create(self.home + "/.local/bin", _exists=self._created_dirs)

  @property
  def user_cache_dir(self):
    return ms.dir.create(self.home + "/.cache", _exists=self._created_dirs)

  @property
  def user_config_dir(self):
    return ms.dir.create(self.home + "/.config", _exists=self._created_dirs)

  @property
  def user_data_dir(self):
    return ms.dir.create(self.home + "/.local/share", _exists=self._created_dirs)

  @property
  def user_lib_dir(self):
    return ms.dir.create(self.home + "/.local/lib", _exists=self._created_dirs)

  @property
  def user_log_dir(self):
    return ms.dir.create(self.home + "/.local/log", _exists=self._created_dirs)

  def hibernate(self):
    self._run("systemctl", "hibernate")

  def poweroff(self):
    self._run("poweroff")

  def reboot(self):
    self._run("reboot")

  def sleep(self):
    self._run("systemctl", "suspend")


class PlatformMacOS(_Platform):
  """На 100% сгенерирован GigaCode, потому что я не знаю как устроен MacOS"""
  @property
  def root_dir(self):
    return ms.path.Path("/")

  @property
  def system_bin_dir(self):
    return ms.dir.create(self.root_dir + "/usr/bin", _exists=self._created_dirs)

  @property
  def system_cache_dir(self):
    return ms.dir.create(self.root_dir + "/private/var/cache", _exists=self._created_dirs)

  @property
  def system_config_dir(self):
    return ms.dir.create(self.root_dir + "/private/etc", _exists=self._created_dirs)

  @property
  def system_data_dir(self):
    return ms.dir.create(self.root_dir + "/usr/share", _exists=self._created_dirs)

  @property
  def system_lib_dir(self):
    return ms.dir.create(self.root_dir + "/usr/lib", _exists=self._created_dirs)

  @property
  def system_log_dir(self):
    return ms.dir.create(self.root_dir + "/private/var/log", _exists=self._created_dirs)

  @property
  def user_bin_dir(self):
    return ms.dir.create(self.home + "/bin", _exists=self._created_dirs)

  @property
  def user_cache_dir(self):
    return ms.dir.create(self.home + "/Library/Caches", _exists=self._created_dirs)

  @property
  def user_config_dir(self):
    return ms.dir.create(self.home + "/Library/Preferences", _exists=self._created_dirs)

  @property
  def user_data_dir(self):
    return ms.dir.create(self.home + "/Library/Application Support", _exists=self._created_dirs)

  @property
  def user_lib_dir(self):
    return ms.dir.create(self.home + "/Library/Application Support", _exists=self._created_dirs)

  @property
  def user_log_dir(self):
    return ms.dir.create(self.home + "/Library/Logs", _exists=self._created_dirs)


class PlatformTermux(PlatformLinux):
  @property
  def root_dir(self):
    return ms.path.Path("/data/data/com.termux/files")


class PlatformWindows(_Platform):
  @property
  def root_dir(self):
    return ms.path.Path("C:/")
  # Спасибо GigaCode за все эти пути, но я всё проверил

  @property
  def system_bin_dir(self):
    return self.root_dir + "/Windows/System32"

  @property
  def system_cache_dir(self):
    return ms.dir.create(self.root_dir + "/Windows/Temp", _exists=self._created_dirs)

  @property
  def system_config_dir(self):
    return ms.dir.create(self.root_dir + "/Windows/System32/config", _exists=self._created_dirs)

  @property
  def system_data_dir(self):
    return ms.dir.create(self.root_dir + "/ProgramData", _exists=self._created_dirs)

  @property
  def system_lib_dir(self):
    return self.system_bin_dir

  @property
  def system_log_dir(self):
    return ms.dir.create(self.root_dir + "/Windows/System32/LogFiles", _exists=self._created_dirs)

  @property
  def user_bin_dir(self):
    return ms.dir.create(self.user_data_dir + "/Microsoft/WindowsApps", _exists=self._created_dirs)

  @property
  def user_cache_dir(self):
    return ms.dir.create(self.user_data_dir + "/Temp", _exists=self._created_dirs)

  @property
  def user_config_dir(self):
    return ms.dir.create(self.home + "/AppData/Roaming", _exists=self._created_dirs)

  @property
  def user_data_dir(self):
    return ms.dir.create(self.home + "/AppData/Local", _exists=self._created_dirs)

  @property
  def user_lib_dir(self):
    return ms.dir.create(self.user_data_dir + "/Microsoft/Windows/Libraries", _exists=self._created_dirs)

  @property
  def user_log_dir(self):
    return ms.dir.create(self.user_data_dir + "/Microsoft/Windows/Logs", _exists=self._created_dirs)

  @property
  def win_dir(self):
    return self.root_dir + "/Windows"

  def hibernate(self):
    self._run("shutdown", "/h")

  def poweroff(self):
    self._run("shutdown", "/s", "/t", "0")

  def reboot(self):
    self._run("shutdown", "/r", "/t", "0")


def get_platform() -> _Platform:
  info = PlatformInfo()
  if info.is_termux:
    return PlatformTermux()
  if info.is_linux:
    return PlatformLinux()
  if info.is_macos:
    return PlatformMacOS()
  if info.is_windows:
    return PlatformWindows()
  return _Platform()
