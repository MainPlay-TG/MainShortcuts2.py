import os
import sys
from .core import MS2
from functools import wraps
from typing import *
ms: MS2 = None
# 2.0.0


class MiddlewareBase:
  def __init__(self, func):
    self._init(func)

  def _init(self, func):
    self._args = None
    self._exception = None
    self._kwargs = None
    self._result = None
    self._traceback = None
    self.completed_with_exc = None
    self.completed = False
    self.func = func
    self.launched = False
    if not hasattr(self, "ignore_exceptions"):
      self.ignore_exceptions = False

  def _check_completed(self):
    if not self.completed:
      raise RuntimeError("The function has not yet been completed")

  def _check_launched(self):
    if not self.completed:
      raise RuntimeError("The function has not yet been launched")

  def _run(self, args, kwargs):
    self._args = args
    self._kwargs = kwargs
    self.launched = True
    try:
      self.before()
    except Exception:
      if not self.ignore_exceptions:
        raise
    try:
      self._result = self.func(*args, **kwargs)
      self.completed_with_exc = False
    except Exception as e:
      from traceback import format_exc
      self._exception = e
      self._traceback = format_exc()
      self.completed_with_exc = True
    self.completed = True
    try:
      self.after()
    except Exception:
      if not self.ignore_exceptions:
        raise
    return self.result

  @property
  def args(self) -> tuple:
    self._check_launched()
    return self._args

  @property
  def kwargs(self) -> dict[str, Any]:
    self._check_launched()
    return self._kwargs

  @property
  def result(self) -> Any:
    self._check_completed()
    if self.completed_with_exc:
      raise self.exception
    return self._result

  @property
  def exception(self) -> Union[None, Exception]:
    self._check_completed()
    return self._exception

  @property
  def traceback(self) -> Union[None, str]:
    self._check_completed()
    return self._traceback

  def before(self):
    pass

  def after(self):
    pass


def args2kwargs(func: Callable, args: Iterable = (), kwargs: dict[str, Any] = {}) -> tuple[tuple, dict[str, Any]]:
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


async def async_download_file(url: str, path: str, *, delete_on_error: bool = True, chunk_size: int = 1024, **kw) -> int:
  kw["url"] = url
  if not "method" in kw:
    kw["method"] = "GET"
  async with async_request(**kw) as resp:
    with open(path, "wb") as fd:
      size = 0
      try:
        async for chunk in resp.content.iter_chunked(chunk_size):
          fd.write(chunk)
          size += len(chunk)
      except:
        if delete_on_error:
          if os.path.isfile(path):
            os.remove(path)
        raise
  return size


async def async_request(method: str, url: str, *, ignore_status: bool = False, **kw):
  """aiohttp request"""
  import aiohttp
  kw["method"] = method
  kw["url"] = url
  resp = aiohttp.request(**kw)
  if not ignore_status:
    resp.raise_for_status()
  return resp


def async2sync(func: Callable) -> Callable:
  """Превратить асинхронную функцию в синхронную"""
  import asyncio
  import concurrent.futures
  pool = concurrent.futures.ThreadPoolExecutor()

  def wrapper(*args, **kwargs):
    return pool.submit(asyncio.run, func(*args, **kwargs)).result()
  return wrapper


def get_my_ip() -> str:
  import requests
  with requests.get("https://api.ipify.org?format=json") as resp:
    ip = resp.json()["ip"]
  return ip


def is_async(func: Callable) -> bool:
  import inspect
  return inspect.iscoroutinefunction(func)


def is_sync(func: Callable) -> bool:
  return not is_async(func)


def middleware(cls: MiddlewareBase):
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      return cls(func)._run(args, kwargs)
    return wrapper
  return decorator


def randfloat(min: float, max: float = None) -> float:
  from random import random
  if max == None:
    max = min
    min = 0
  return min + (random() * (max - min))


def randstr(length: int, symbols: str = "0123456789abcdefghijklmnopqrstuvwxyz") -> str:
  from random import choice
  t = ""
  while len(t) < length:
    t += choice(symbols)
  return t


def return_False(*a, **b):
  return False


def return_None(*a, **b):
  return None


def return_True(*a, **b):
  return True


def riop(**p_kw):
  """Run In Another Process (multiprocessing)"""
  import multiprocessing
  if not "daemon" in p_kw:
    p_kw["daemon"] = False

  def decorator(func):
    p_kw["target"] = func

    def wrapper(*args, **kwargs) -> multiprocessing.Process:
      p_kw["args"] = args
      p_kw["kwargs"] = kwargs
      p = multiprocessing.Process(**p_kw)
      p.start()
      return p
    return wrapper
  return decorator


def riot(**t_kw):
  """Run In Another Thread (threading)"""
  import threading
  if not "daemon" in t_kw:
    t_kw["daemon"] = False

  def decorator(func):
    t_kw["target"] = func

    def wrapper(*args, **kwargs) -> threading.Thread:
      t_kw["args"] = args
      t_kw["kwargs"] = kwargs
      t = threading.Thread(**t_kw)
      t.start()
      return t
    return wrapper
  return decorator


def sync_download_file(url: str, path: str, *, delete_on_error: bool = True, chunk_size: int = 1024, **kw) -> int:
  kw["stream"] = True
  kw["url"] = url
  if not "method" in kw:
    kw["method"] = "GET"
  with sync_request(**kw) as resp:
    with open(path, "wb") as fd:
      size = 0
      try:
        for chunk in resp.iter_content(chunk_size):
          fd.write(chunk)
          size += len(chunk)
      except:
        if delete_on_error:
          if os.path.isfile(path):
            os.remove(path)
        raise
  return size


def sync_request(method: str, url: str, *, ignore_status: bool = False, **kw):
  """requests request"""
  import requests
  kw["method"] = method
  kw["url"] = url
  resp = requests.request(**kw)
  if not ignore_status:
    resp.raise_for_status()
  return resp


def sync2async(func: Callable) -> Callable:
  """Превратить синхронную функцию в асинхронную"""
  async def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
  return wrapper


def uuid() -> str:
  from uuid import uuid4
  return str(uuid4())


def timedelta(time: Union[int, float, dict]):
  import datetime
  if type(time) == datetime.timedelta:
    return time
  if type(time) == dict:
    return datetime.timedelta(**time)
  return datetime.timedelta(seconds=time)


download_file = sync_download_file
request = sync_request
