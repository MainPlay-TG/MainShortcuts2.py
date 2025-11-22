import os
import requests
from .base import BaseClient
from io import BytesIO, IOBase
from MainShortcuts2 import ms
from typing import IO
UPLOAD_HEADERS = {"Content-Type": "application/octet-stream"}


class _ReadBinaryIO(IOBase):
  def __init__(self, resp: requests.Response):
    IOBase.__init__(self)
    resp.raw.decode_content = True
    self.mode: str = "rb"
    self.resp = resp

  def __exit__(self, *a):
    self.close()

  def close(self):
    self.resp.close()

  def read(self, size: int = None) -> bytes:
    return self.resp.raw.read(size)

  def readable(self) -> bool:
    return True

  def seekable(self) -> bool:
    return False

  def writable(self) -> bool:
    return False


class WebDAVClient(BaseClient):
  """Простой WebDAV клиент"""

  def __init__(self, root: str, **kw):
    self._init(**kw)
    self._cwd: str = "/"
    self._url = root.rstrip("/") + "{method}"

  def _auth(self):
    pass  # Без авторизации

  def _fspath(self, path) -> str:
    if isinstance(path, bytes):
      path = path.decode("utf-8")
    return os.fspath(path)

  def resolve_path(self, path: str) -> str:
    if not isinstance(path, str):
      path = self._fspath(path)
    if not path.startswith("/"):
      path = self.cwd + "/" + path
    return os.path.normpath(path).replace("\\", "/")

  @property
  def cwd(self) -> str:
    """Рабочая папка на сервере"""
    return self._cwd

  @cwd.setter
  def cwd(self, value: str):
    self._cwd = self.resolve_path(value).rstrip("/")

  def request(self, method: str, path: str, **kw) -> requests.Response:
    self._auth()
    path = self.resolve_path(path)
    if not kw.get("stream"):
      with self._request(method, path, **kw) as resp:
        return resp
    return self._request(method, path, **kw)

  def open(self, path: str, mode: str = "rb") -> _ReadBinaryIO:
    """Открыть файл сервера (read-only)"""
    if not mode in ["rb", "br"]:
      raise ValueError("Only the 'rb' mode is supported")
    return _ReadBinaryIO(self.request("GET", path, stream=True))

  def download(self, path: str, filepath: str, **kw) -> int:
    """Скачать файл с сервера"""
    with self.request("GET", path, stream=True) as resp:
      return ms.utils.download_file(resp, filepath)

  def upload_io(self, io: IO[bytes], path: str, **kw) -> requests.Response:
    if isinstance(io, bytes):
      with BytesIO(io) as f:
        return self.upload_io(f, path, **kw)
    kw.setdefault("headers", {})
    for k, v in UPLOAD_HEADERS.items():
      kw["headers"].setdefault(k, v)
    if not kw["headers"].get("Content-Length"):
      if io.seekable():
        pos = io.tell()
        io.seek(0, 2)
        kw["headers"]["Content-Length"] = str(io.tell())
        io.seek(pos)
    return self.request("PUT", path, data=io, **kw)

  def upload(self, filepath: str, path: str, **kw):
    """Загрузить локальный файл на сервер"""
    with open(filepath, "rb") as f:
      return self.upload_io(f, path, **kw)

  def mkdir(self, path: str):
    """Создать пустую папку на сервере"""
    if not path.endswith("/"):
      path += "/"
    return self.request("MKCOL", path)

  def delete(self, path: str):
    """Удалить файл/папку на сервере"""
    return self.request("DELETE", path)

  def move(self, src: str, dst: str, overwrite=False, **kw):
    """Переместить файл/папку на сервере"""
    kw.setdefault("headers", {})
    kw["headers"]["Destination"] = self.resolve_path(dst)
    kw["headers"]["Overwrite"] = "T" if overwrite else "F"
    return self.request("MOVE", src, **kw)

  def copy(self, src: str, dst: str, overwrite=False, **kw):
    """Скопировать файл/папку на сервере"""
    kw.setdefault("headers", {})
    kw["headers"]["Destination"] = self.resolve_path(dst)
    kw["headers"]["Overwrite"] = "T" if overwrite else "F"
    return self.request("COPY", src, **kw)

  def rename(self, src: str, name: str, **kw):
    """Переименовать файл/папку на сервере"""
    parent = os.path.dirname(self.resolve_path(src))
    return self.move(src, parent + "/" + name, **kw)
