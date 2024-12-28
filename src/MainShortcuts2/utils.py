"""Различные утилиты, требующие сторонних модулей"""
import os
import sys
from .core import ms
from functools import wraps
from typing import *
cache = {}


def return_False(*a, **b):
  """Вернуть False при любых аргументах"""
  return False


def return_None(*a, **b):
  """Вернуть None при любых аргументах"""
  return None


def return_True(*a, **b):
  """Вернуть True при любых аргументах"""
  return True


class MiddlewareBase:
  """middleware для функции"""

  def __init__(self, func):
    self._init(func)

  def _init(self, func):
    self._args = None
    self._exception = None
    self._kwargs = None
    self._result = None
    self._time = None
    self._traceback = None
    self.completed_with_exc: Union[None, bool] = None
    self.completed: bool = False
    self.func = func
    self.launched: bool = False
    if not hasattr(self, "ignore_exceptions"):
      self.ignore_exceptions: bool = False

  def _check_completed(self):
    if not self.completed:
      raise RuntimeError("The function has not yet been completed")

  def _check_launched(self):
    if not self.launched:
      raise RuntimeError("The function has not yet been launched")

  def _run(self, args, kwargs):
    from time import time
    if self.launched:
      raise RuntimeError("You can only start a function once once")
    self._args = args
    self._kwargs = kwargs
    self.launched = True
    try:
      self.before()
    except Exception:
      if not self.ignore_exceptions:
        raise
    started_at = time()
    try:
      self._result = self.func(*self.args, **self.kwargs)
      self.completed_with_exc = False
    except Exception as e:
      from traceback import format_exc
      self._exception = e
      self._traceback = format_exc()
      self.completed_with_exc = True
    self._time = time() - started_at
    self.completed = True
    try:
      self.after()
    except Exception:
      if not self.ignore_exceptions:
        raise
    return self.result

  @property
  def args(self) -> tuple:
    """Аргументы, переданные функции"""
    self._check_launched()
    return self._args

  @args.setter
  def args(self, value: Iterable):
    if value is None:
      value = []
    self._args = tuple(value)

  @property
  def exception(self) -> None | Exception:
    """Исключение, возникшее в процессе работы функции"""
    self._check_completed()
    return self._exception

  @property
  def kwargs(self) -> dict[str, Any]:
    """Именованные аргументы, переданные функции"""
    self._check_launched()
    return self._kwargs

  @kwargs.setter
  def kwargs(self, value: dict[str, Any]):
    if value is None:
      value = {}
    for k in value.keys():
      assert type(k) == str
    self._kwargs = value

  @property
  def result(self) -> Any:
    """Результат работы функции"""
    self._check_completed()
    if self.completed_with_exc:
      raise self.exception  # type: ignore
    return self._result

  @property
  def time(self) -> float:
    """Продолжительность работы функции (сек)"""
    self._check_completed()
    return self._time

  @property
  def traceback(self) -> None | str:
    self._check_completed()
    return self._traceback

  def before(self):
    """Перед запуском функции. Можно обработать/изменить аргументы"""
    pass

  def after(self):
    """После запуска функции. Можно обработать результат или исключение"""
    pass


def args2kwargs(func: Callable, args: Iterable = (), kwargs: dict[str, Any] = {}) -> tuple[tuple, dict[str, Any]]:
  """Преобразовать `args` в `kwargs` | `inspect`"""
  import inspect
  kw = kwargs.copy()
  args = list(args)
  spec = inspect.getfullargspec(func)
  for i in inspect.signature(func).parameters:
    if i != spec.varargs:
      if i != spec.varkw:
        if not i in kw:
          kw[i] = args.pop(0)
  if len(args) > 0:
    if spec.varargs != None:
      raise TypeError("Too many arguments")
  return tuple(args), kw


async def async_download_file(url: str, path: str, *, cb_end=return_None, cb_progress=return_None, cb_start=return_None, chunk_size: int = 1024, delete_on_error: bool = True, **kw) -> int:
  """Асинхронная функция для скачивания файла | `aiohttp`"""
  kw["url"] = url
  if not "method" in kw:
    kw["method"] = "GET"
  async with async_request(**kw) as resp:  # type: ignore
    if callable(getattr(path, "write", None)):
      f: IO[bytes] = path
    else:
      f = open(path, "wb")
    with f:
      size = 0
      await cb_start(f, resp, size)
      try:
        async for chunk in resp.content.iter_chunked(chunk_size):
          size += f.write(chunk)
          await cb_progress(f, resp, size)
      except:
        if delete_on_error:
          if os.path.isfile(path):
            os.remove(path)
        raise
      cb_end(f, resp, size)
  return size


async def async_request(method: str, url: str, *, ignore_status: bool = False, session=None, **kw):
  """Асинхронный HTTP запрос | `aiohttp`"""
  from importlib import import_module
  aiohttp = import_module("aiohttp")
  # import aiohttp
  resp = None
  if isinstance(method, aiohttp.ClientResponse):
    resp = method
  if isinstance(url, aiohttp.ClientResponse):
    if not resp is None:
      raise TypeError("Only one argument can be `Response`")
    resp = url
  if resp is None:
    if session is None:
      session = aiohttp.ClientSession()
    kw["method"] = method
    kw["url"] = url
    resp = await session.request(**kw)
  if not ignore_status:
    resp.raise_for_status()
  return resp


def async2sync(func: Callable) -> Callable:
  """Превратить асинхронную функцию в синхронную | `asyncio`, `concurrent`"""
  import asyncio
  import concurrent.futures
  pool = concurrent.futures.ThreadPoolExecutor()

  def wrapper(*args, **kwargs):
    return pool.submit(asyncio.run, func(*args, **kwargs)).result()
  return wrapper


def get_my_ip() -> str:
  """Получить глобальный IP | `requests`"""
  with sync_request("GET", "https://api.ipify.org?format=json") as resp:
    ip = resp.json()["ip"]
  return ip


def is_async(func: Callable) -> bool:
  """Является ли функция асинхронной | `inspect`"""
  import inspect
  return inspect.iscoroutinefunction(func)


def is_sync(func: Callable) -> bool:
  """Является ли функция синхронной | `inspect`"""
  return not is_async(func)


def middleware(cls: type[MiddlewareBase]):
  """middleware для функции в виде декоратора"""
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      return cls(func)._run(args, kwargs)
    return wrapper
  return decorator


def randfloat(min: float, max: float = None) -> float:
  """Случайное число | `random`"""
  from random import random
  if max == None:
    max = min
    min = 0
  return min + (random() * (max - min))


def randstr(length: int, symbols: str = "0123456789abcdefghijklmnopqrstuvwxyz") -> str:
  """Случайная строка | `random`"""
  from random import choice
  t = ""
  while len(t) < length:
    t += choice(symbols)
  return t


def riop(**p_kw):
  """Запустить функцию в отдельном процессе | `multiprocessing`"""
  import multiprocessing
  if not "daemon" in p_kw:
    p_kw["daemon"] = False

  def decorator(func):
    p_kw["target"] = func

    @wraps(func)
    def wrapper(*args, **kwargs) -> multiprocessing.Process:
      p_kw["args"] = args
      p_kw["kwargs"] = kwargs
      p = multiprocessing.Process(**p_kw)
      p.start()
      return p
    return wrapper
  return decorator


def riot(**t_kw):
  """Запустить функцию в отдельном потоке | `threading`"""
  import threading
  if not "daemon" in t_kw:
    t_kw["daemon"] = False

  def decorator(func):
    t_kw["target"] = func

    @wraps(func)
    def wrapper(*args, **kwargs) -> threading.Thread:
      t_kw["args"] = args
      t_kw["kwargs"] = kwargs
      t = threading.Thread(**t_kw)
      t.start()
      return t
    return wrapper
  return decorator


def sync_download_file(url: str, path: str, *, cb_end=return_None, cb_progress=return_None, cb_start=return_None, chunk_size: int = 1024, delete_on_error: bool = True, **kw) -> int:
  """Синхронная функция для скачивания файла | `requests`"""
  kw["stream"] = True
  kw["url"] = url
  if not "method" in kw:
    kw["method"] = "GET"
  resp = sync_request(**kw)
  with resp:
    if callable(getattr(path, "write", None)):
      f: IO[bytes] = path
    else:
      f = open(path, "wb")
    with f:
      size = 0
      cb_start(f, resp, size)
      try:
        for chunk in resp.iter_content(chunk_size):
          size += f.write(chunk)
          cb_progress(f, resp, size)
      except:
        f.close()
        if delete_on_error:
          if os.path.isfile(path):
            os.remove(path)
        raise
      cb_end(f, resp, size)
  return size


def sync_request(method: str, url: str, *, ignore_status: bool = False, session=None, **kw):
  """Синхронный HTTP запрос | `requests`"""
  try:
    import requests
  except ImportError as err:
    try:
      from pip._vendor import requests
    except ImportError:
      raise err
  resp = None
  if isinstance(method, requests.Response):
    resp = method
  if isinstance(url, requests.Response):
    if not resp is None:
      raise TypeError("Only one argument can be `Response`")
    resp = url
  if resp is None:
    if session is None:
      session = requests.Session()
    kw["method"] = method
    kw["url"] = url
    resp = session.request(**kw)
  if not ignore_status:
    resp.raise_for_status()
  return resp


def sync2async(func: Callable) -> Callable:
  """Превратить синхронную функцию в асинхронную"""
  async def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
  return wrapper


def uuid(format=None, *args, **kwargs) -> str:
  """Сгенерировать UUID | `uuid`"""
  import uuid
  if format is None:
    cls = uuid.uuid4
  else:
    cls = getattr(uuid, f"uuid{format}")
  return str(cls(*args, **kwargs))


def timedelta(time: Union[int, float, dict]):
  """Превратить число/словарь в `timedelta` | `datetime`"""
  import datetime
  if isinstance(time, datetime.timedelta):
    return time
  if isinstance(time, dict):
    return datetime.timedelta(**time)
  return datetime.timedelta(seconds=time)


def shebang_code(code: str, *, exe_name: Union[None, str] = None, exe_path: Union[None, str] = None, none_if_no_changes: bool = False, use_env: bool = True) -> Union[None, str]:
  """Вставить/заменить шебанг в коде. Если указать имя интерпретатора, путь будет найден с помощью `shutil.which`"""
  if (exe_name is None) and (exe_path is None):
    raise TypeError("Specify exe_name or exe_path")
  if not exe_name is None:
    if not exe_path is None:
      raise TypeError("exe_name and exe_path cannot be used together")
  if exe_path is None:
    if use_env:
      exe_path = "/bin/env " + exe_name
    else:
      import shutil
      exe_path = shutil.which(exe_name)
      if exe_path is None:
        raise Exception("Command %s not found in PATH" % exe_name)
  lines = code.split("\n")
  if none_if_no_changes:
    if lines[0] == "#!" + exe_path:
      return None
  while len(lines[0].strip()) == 0 or lines[0].startswith("#!"):
    del lines[0]
  return "#!" + exe_path + "\n" + "\n".join(lines)


def shebang_file(path: str, **kw) -> int:
  """Вставить/заменить шебанг в файле кода"""
  kw["code"] = ms.file.read(path)
  kw["none_if_no_changes"] = True
  result = shebang_code(**kw)
  if result is None:
    return 0
  return ms.file.write(path, result)


def remove_ANSI(text: str) -> str:
  """Убрать ANSI коды из текста | `re`"""
  cache_id = "remove_ANSI", 0
  if not cache_id in cache:
    import re
    cache[cache_id] = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
  return cache[cache_id].sub("", text)


OnlyOneInstanceError = ms.types.OnlyOneInstanceError


class OnlyOneInstance:
  """Запретить запуск одной программы несколько раз | `tempfile`, `fcntl`"""
  _win = sys.platform == "win32"

  def __init__(self, name: str = "main", lock_path: str = None):
    import tempfile
    self.name: str = name
    self.running = False
    if lock_path is None:
      lock_path = tempfile.gettempdir() + "/" + ms.MAIN_FILE.replace(":", "").replace("/", "_") + "." + name + ".lock"
    self.lock = ms.path.Path(lock_path, use_cache=False)
    if self._win:
      flags = os.O_CREAT | os.O_EXCL | os.O_RDWR

      def _enter():
        try:
          if os.path.exists(self.lock.path):
            os.unlink(self.lock.path)
          self.fd = os.open(self.lock.path, flags)
        except OSError as err:
          if err.errno == 13:
            raise OnlyOneInstanceError()
          raise

      def _exit():
        os.close(self.fd)
        os.unlink(self.lock.path)
    else:
      import fcntl
      flags = fcntl.LOCK_EX | fcntl.LOCK_NB

      def _enter():
        self.fp = open(self.lock.path, "w")
        self.fp.flush()
        try:
          fcntl.lockf(self.fp, flags)
        except IOError:
          raise OnlyOneInstanceError()

      def _exit():
        fcntl.lockf(self.fp, fcntl.LOCK_UN)
        self.fp.close()
        if os.path.exists(self.lock.path):
          os.unlink(self.lock.path)
    self._enter = _enter
    self._exit = _exit

  def __enter__(self):
    if self.running:
      raise OnlyOneInstanceError()
    self._enter()
    self.running = True
    try:
      self.on_enter()
    except Exception:
      pass
    return self

  def __exit__(self, a, b, c):
    if not self.running:
      return
    self._exit()
    self.running = False
    self.on_exit()

  def on_enter(self):
    pass

  def on_exit(self):
    pass


def multi_and(*values: bool) -> bool:
  for i in values:
    if not i:
      return False
  return True


def multi_or(*values: bool) -> bool:
  for i in values:
    if i:
      return True
  return False


def is_int(value: float) -> bool:
  return value == int(value)


def get_self_module(__name__: str):
  return sys.modules[__name__]


def check_programs(*progs: str, raise_error: bool = True) -> list[str]:
  """Проверить наличие программ в `$PATH` | `shutil`"""
  from shutil import which
  failed = []
  for i in progs:
    if which(i) is None:
      if not i in failed:
        failed.append(i)
  failed.sort()
  if raise_error:
    if len(failed) > 0:
      if len(failed) == 1:
        raise OSError("Failed to find program " + failed[0] + " in $PATH")
      raise OSError("Failed to find programs " + (", ".join(failed)) + " in $PATH")
  return failed


def handle_exception(on_exception=return_None, reraise: bool = True, exc_type: type[BaseException] = Exception):
  """Обернуть функцию в `try`/`except`"""
  def deco(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      try:
        return func(*args, **kwargs)
      except exc_type as exc:
        on_exception(exc)
        if reraise:
          raise
    return wrapper
  return deco


def disable_warnings():
  """Отключить модуль `warnings`"""
  import warnings
  warnings.warn = return_None


download_file = sync_download_file
request = sync_request
