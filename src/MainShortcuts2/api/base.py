import requests
import requests.auth
from MainShortcuts2 import ms
USER_AGENTS: dict[str, str] = {}
USER_AGENTS["Android"] = "Mozilla/5.0 (Linux; Android 13; K) Chrome/128.0.6613.146"
USER_AGENTS["Android13"] = "Mozilla/5.0 (Linux; Android 13; K) Chrome/128.0.6613.146"


def auth_basic(username: str, password: str, *, client: "BaseClient" = None) -> str:
  """Настроить базовую авторизацию для клиента"""
  if username is None:
    username = client.username
  if password is None:
    password = client.password
  header = requests.auth._basic_auth_str(username, password)
  if client is not None:
    client._headers["Authorization"] = header
  return header


def setdefattr(obj, attr, value):
  if getattr(obj, attr, None) is None:
    setattr(obj, attr, value)


class BaseClient(ms.ObjectBase):
  """Базовый клиент для HTTP API"""
  _enable_cookies: bool
  _http: requests.Session
  _url_data: dict[str, str]
  _url: str
  cache: "CacheStorage"

  def __init__(self, **kw):
    self._init(**kw)

  def _init(self, session: requests.Session = None):
    setdefattr(self, "_http", session)
    setdefattr(self, "_enable_cookies", False)
    setdefattr(self, "_url_data", {})
    setdefattr(self, "_url", "https://example.com/api/{method}")
    setdefattr(self, "cache", CacheStorage())

  def __enter__(self):
    return self

  def __exit__(self, *a):
    if self._http is not None:
      self._http.close()

  def __repr__(self) -> str:
    cls = type(self)
    return "%s.%s(...)" % (cls.__module__, cls.__name__)

  @property
  def _cookies(self):
    return self.http.cookies

  @property
  def _headers(self):
    return self.http.headers

  @property
  def _params(self):
    return self.http.params

  @property
  def http(self) -> requests.Session:
    """HTTP сессия"""
    if self._http is None:
      self._http = requests.Session()
    return self._http

  def _request(self, http_method: str, api_method: str, *, raise_for_status: bool = True, url_data: dict[str, str] = None, **kw):
    _url_data = self._url_data.copy()
    _url_data["method"] = api_method
    if url_data is not None:
      _url_data.update(url_data)
    result = self.http.request(http_method, self._url.format(**_url_data), **kw)
    if self._enable_cookies:
      self._cookies.update(result.cookies)
    if raise_for_status:
      result.raise_for_status()
    return result

  def request(self, httpm, apim, **kw) -> requests.Response:
    """Отправить запрос к API"""
    return self._request(httpm, apim, **kw)


class Base(BaseClient):
  """Устаревший класс, используйте BaseClient!"""
  def __init_subclass__(cls, **kw):
    from warnings import warn
    warn("Class 'Base' renamed 'BaseClient' starting with version 2.4.6", DeprecationWarning)
    return BaseClient.__init_subclass__(**kw)


class BasicAuthClient(BaseClient):
  """API клиент для авторизации `HTTP Basic`"""

  def _request(self, http_method: str, api_method: str, **kw) -> requests.Response:
    if self._headers.get("Authorization") is None:
      auth_basic(None, None, client=self)
    return BaseClient._request(self, http_method, api_method, **kw)

  @property
  def username(self) -> str:
    """Имя пользователя"""
    return self._username

  @username.setter
  def username(self, value):
    self._headers["Authorization"] = None
    self._username = value

  @property
  def password(self) -> str:
    """Пароль"""
    return self._password

  @password.setter
  def password(self, value):
    self._headers["Authorization"] = None
    self._password = value


class OfflineObjectBase(ms.ObjectBase):
  """API объект из словаря"""

  def __init__(self, raw: dict, *args, **kwargs):
    self.raw = raw
    self._init(*args, **kwargs)

  def __getitem__(self, k):
    return self.raw.get(k)

  def _init(self):
    pass


class ObjectBase(OfflineObjectBase):
  """API объект с привязкой клиента"""

  def __init__(self, client: BaseClient, raw: dict, *args, **kwargs):
    self.client = client.client if isinstance(client, ObjectBase) else client
    self.raw = raw
    self._init(*args, **kwargs)


class CacheStorage(dict):
  def __getitem__(self, k) -> dict:
    self.setdefault(k, {})
    return dict.__getitem__(self, k)
