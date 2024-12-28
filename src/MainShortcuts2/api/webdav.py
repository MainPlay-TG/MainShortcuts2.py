import os
import requests
from .base import BaseClient
from io import IOBase
from MainShortcuts2 import ms
UPLOAD_HEADERS = {"Content-Type": "application/octet-stream"}


class _ReadBinaryIO(IOBase):
  def __init__(self, resp: requests.Response):
    IOBase.__init__(self)
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
    self._url = (root[:-1] if root.endswith("/") else root) + "{method}"

  def _auth(self):
    pass  # Без авторизации

  def _fspath(self, path) -> str:
    if isinstance(path, bytes):
      path = path.decode("utf-8")
    return os.fspath(path)

  @property
  def cwd(self) -> str:
    """Рабочая папка на сервере"""
    return self._cwd

  @cwd.setter
  def cwd(self, value: str):
    path = self._fspath(value)
    if not path.startswith("/"):
      path = self.cwd + "/" + path
    self._cwd = os.path.normpath(path[:-1] if path.endswith("/") else path)

  def request(self, method: str, path: str, **kw) -> requests.Response:
    self._auth()
    path = self._fspath(path)
    if not path.startswith("/"):
      path = self.cwd + path
    return self._request(method, path, **kw)

  def open(self, path: str, mode: str = "rb") -> _ReadBinaryIO:
    """Открыть файл сервера (read-only)"""
    if not mode in ["rb", "br"]:
      raise ValueError("Only the 'rb' mode is supported")
    return _ReadBinaryIO(self.request("GET", path, stream=True))

  def download(self, path: str, filepath: str, **kw) -> int:
    """Скачать файл с сервера"""
    return ms.utils.download_file(self.request("GET", path, stream=True), filepath)

  def upload(self, filepath: str, path: str):
    """Загрузить локальный файл на сервер"""
    with open(filepath, "rb") as f:
      self.request("PUT", path, data=f, headers=UPLOAD_HEADERS)

  def mkdir(self, path: str):
    """Создать пустую папку на сервере"""
    if not path.endswith("/"):
      path += "/"
    self.request("MKCOL", path)

  def delete(self, path: str):
    """Удалить файл/папку на сервере"""
    self.request("DELETE", path)
