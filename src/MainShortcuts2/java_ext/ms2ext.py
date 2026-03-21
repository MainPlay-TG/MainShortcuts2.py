"""Функции для работы с большими файлами с помощью расширения на Java. При недоступности расширения будут использоваться встроенные функции"""
import base64
import hashlib
import os
import requests
import subprocess
import typing
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from MainShortcuts2 import java_ext
from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
mgr = java_ext.JavaExtManager("MainPlay-TG", "MS2Ext.java")
class2version: dict[str, java_ext.JavaExtVersion] = {}


def get_ver(class_name):
  if not class_name in class2version:
    class2version[class_name] = mgr.search_has_class(class_name)
  return class2version[class_name]


def popen_class(class_name, **kw) -> subprocess.Popen[bytes]:
  kw["stderr"] = subprocess.PIPE
  kw["stdin"] = subprocess.PIPE
  return get_ver(class_name).popen_class(class_name, **kw)


class ExtCoreError(subprocess.CalledProcessError):
  """Ошибка при запуске расширения (повтор через fallback)"""
  pass


class ExtOperationError(subprocess.CalledProcessError):
  """Ошибка при работе расширения (конечная ошибка)"""
  pass


ErrorsForFallback = (
    ExtCoreError,  # Не удалось запустить расширение
    java_ext.IncompatibleJava,  # Несовместимая Java
    requests.exceptions.RequestException,  # Не удалось скачать расширение
)


def run_class(class_name, config, timeout=None, **kw):
  with popen_class(class_name) as p:
    p.stdin.write(ms.json.encode(config).encode("utf-8"))
    p.stdin.flush()
    p.stdin.close()
    if p.wait(timeout):
      try:
        stderr = p.stderr.read().decode("utf-8")
        err_data = ms.json.decode(stderr)
      except Exception:
        raise ExtCoreError(p.returncode, p.args, p.stdout, p.stderr)
      raise ExtOperationError(p.returncode, p.args, p.stdout, err_data)
    stderr = p.stderr.read()
  if not stderr:
    return {}
  return ms.json.decode(stderr.decode("utf-8"))


class configs:
  class _Base(dict):
    def __setitem__(self, k, v):
      if v is None:
        return
      dict.__setitem__(self, k, v)

    def get(self, k, d=None):
      if k in self:
        return self[k] or d
      return d

  class FileDownloaderV1(_Base):
    @property
    def bufSize(self) -> int:
      return self.get("bufSize") or 1024 * 32

    @property
    def checkStatus(self) -> bool:
      return self.get("checkStatus", True)

    @property
    def followRedirects(self) -> bool:
      return self.get("followRedirects", True)

    @property
    def headers(self) -> dict[str, str]:
      return self.get("headers") or {}

    @property
    def method(self) -> str:
      return self.get("method") or "GET"

    @property
    def path(self) -> str:
      return self["path"]

    @property
    def query(self) -> dict[str, str]:
      return self.get("query") or {}

    @property
    def sizeLimit(self) -> int | None:
      return self.get("sizeLimit")

    @property
    def url(self) -> str:
      return self["url"]

    @property
    def verify(self) -> bool:
      return self.get("verify", True)

  class _FileHasherBase(_Base):
    @property
    def algs(self) -> list[str]:
      return self["algs"]

    @property
    def bufSize(self) -> int:
      return self.get("bufSize") or 1024 * 1024 * 4

  class FileHasherV1(_FileHasherBase):
    @property
    def path(self) -> str:
      return self["path"]

  class FileHasherV2(_FileHasherBase):
    @property
    def maxThreads(self) -> int:
      return self.get("maxThreads") or 8

    @property
    def paths(self) -> list[str]:
      return self["paths"]


class results:
  class FileDownloaderV1(dict):
    @property
    def downloadedSize(self) -> int:
      return self["downloadedSize"]

    @property
    def headers(self) -> dict[str, list[str]]:
      return self["headers"]

    @property
    def statusCode(self) -> int:
      return self["statusCode"]

  class FileHasherV1(dict[str, bytes]):
    @classmethod
    def _from_b64(cls, data: dict[str, str]):
      return cls({k: base64.b64decode(v) for k, v in data.items()})
  FileHasherV2 = dict[str, FileHasherV1]


class real:
  @classmethod
  def file_downloader_v1(cls, config: configs.FileDownloaderV1, **kw):
    return results.FileDownloaderV1(run_class("file_downloader_v1", config, **kw))

  @classmethod
  def file_hasher_v1(cls, config: configs.FileHasherV1, **kw):
    if not config.get("algs"):
      return results.FileHasherV1()
    return results.FileHasherV1._from_b64(run_class("file_hasher_v1", config, **kw))

  @classmethod
  def file_hasher_v2(cls, config: configs.FileHasherV2, **kw):
    if not config.get("paths"):
      return results.FileHasherV2()
    if not config.get("algs"):
      return results.FileHasherV2({i: results.FileHasherV1() for i in config.paths})
    result = run_class("file_hasher_v2", config, **kw)
    return results.FileHasherV2({k: results.FileHasherV1._from_b64(v) for k, v in result.items()})


class fallback:
  @classmethod
  def file_downloader_v1(cls, config: configs.FileDownloaderV1):
    file = Path(config.path).resolve()
    with ExitStack() as stack:
      resp = stack.enter_context(requests.request(config.method, config.url,
                                                  allow_redirects=config.followRedirects,
                                                  headers=config.headers,
                                                  params=config.query,
                                                  stream=True,
                                                  verify=config.verify,
                                                  ))
      if config.checkStatus:
        resp.raise_for_status()
      tmp = stack.enter_context(ms.path.TempFiles(file))  # Авто удаление недокачанного файла
      f = stack.enter_context(file.open("wb"))  # Открытие файла
      cls._download_file(resp.iter_content(config.bufSize), f.write, config.sizeLimit)  # Скачивание файла
      tmp.files.clear()  # Отключить авто удаление
      result = results.FileDownloaderV1()
      result["statusCode"] = resp.status_code
      result["downloadedSize"] = f.tell()
      result["headers"] = {k: [v] for k, v in resp.headers.items()}
    return result

  @classmethod
  def _download_file(cls, stream: typing.Iterable[bytes], write_func: typing.Callable[[bytes], None], sizeLimit: int | None):
    if sizeLimit is None:
      for buf in stream:
        write_func(buf)
      return
    downloaded = 0
    for buf in stream:
      downloaded += len(buf)
      if sizeLimit > downloaded:
        raise OverflowError("The file is too big")
      write_func(buf)

  @classmethod
  def file_hasher_v1(cls, config: configs.FileHasherV1):
    if not config.get("algs"):
      return results.FileHasherV1()
    return cls._hash_file(Path(config.path), set(config.algs), config.bufSize)

  @classmethod
  def file_hasher_v2(cls, config: configs.FileHasherV2):
    if not config.get("paths"):
      return results.FileHasherV2()
    if not config.get("algs"):
      return results.FileHasherV2({i: results.FileHasherV1() for i in config.paths})
    algs, bufsize = set(config.algs), config.bufSize
    with ThreadPoolExecutor(config.maxThreads) as pool:
      futures = {i: pool.submit(cls._hash_file, Path(i), algs, bufsize) for i in config.paths}
      return results.FileHasherV2({k: v.result() for k, v in futures.items()})

  @classmethod
  def _hash_file(cls, file: Path, algs: set[str], bufSize: int):
    hashmap = {i: hashlib.new(i) for i in algs}
    update_func = [i.update for i in hashmap.values()]
    with file.open("rb") as f:
      read_func = f.read
      while True:
        buf = read_func(bufSize)
        if not buf:
          break
        for uf in update_func:
          uf(buf)
      return results.FileHasherV1({k: v.digest() for k, v in hashmap.items()})


def download_file(url: str, path: os.PathLike, *,
                  bufSize: int = None,
                  checkStatus=True,
                  followRedirects=True,
                  headers: dict[str, str] = None,
                  method="GET",
                  query: dict[str, str] = None,
                  sizeLimit: int = None,
                  verify=True,
                  **kw):
  """Скачать большой файл по HTTP"""
  config = configs.FileDownloaderV1()
  config["bufSize"] = bufSize
  config["checkStatus"] = checkStatus
  config["followRedirects"] = followRedirects
  config["headers"] = headers
  config["method"] = method
  config["path"] = os.fspath(path)
  config["query"] = query
  config["sizeLimit"] = sizeLimit
  config["url"] = url
  config["verify"] = verify
  if config.sizeLimit:
    if config.bufSize > config.sizeLimit:
      return fallback.file_downloader_v1(config)
  try:
    return real.file_downloader_v1(config, **kw)
  except ErrorsForFallback:
    return fallback.file_downloader_v1(config)


def hash_file(path: os.PathLike, algs: set[str], *, bufSize: int = None, **kw):
  """Хешировать большой файл"""
  config = configs.FileHasherV1()
  config["algs"] = list(algs)
  config["bufSize"] = bufSize
  config["path"] = os.fspath(path)
  try:
    return real.file_hasher_v1(config, **kw)
  except ErrorsForFallback:
    return fallback.file_hasher_v1(config)


def hash_many_files(paths: set[os.PathLike], algs: set[str], *, bufSize: int = None, **kw):
  """Хешировать несколько файлов"""
  config = configs.FileHasherV2()
  config["algs"] = list(algs)
  config["bufSize"] = bufSize
  config["paths"] = [os.fspath(i) for i in paths]
  try:
    return real.file_hasher_v2(config, **kw)
  except ErrorsForFallback:
    return fallback.file_hasher_v2(config)
