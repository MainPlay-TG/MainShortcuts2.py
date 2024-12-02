import requests


class Base:
  def __init__(self, **kw):
    self._init(**kw)

  def _init(self, session: requests.Session = None):
    self._headers = {}
    self._http = session
    self._params = {}
    self._url = "https://example.com/api/{method}"
    self._url_data = {}

  def __enter__(self):
    return self

  def __exit__(self, *a):
    self.http.close()

  def __repr__(self) -> str:
    cls = type(self)
    return "%s.%s(...)" % (cls.__module__, cls.__name__)

  @property
  def http(self) -> requests.Session:
    if self._http is None:
      self._http = requests.Session()
    return self._http

  def _request(self, http_method: str, api_method: str, *, headers: dict[str, str] = None, params: dict[str, str] = None, raise_for_status: bool = True, url_data: dict[str, str] = None, **kw):
    _headers = self._headers.copy()
    _params = self._params.copy()
    _url_data = self._url_data.copy()
    _url_data["method"] = api_method
    _headers.update({} if headers is None else headers)
    _params.update({} if params is None else params)
    _url_data.update({} if url_data is None else url_data)
    kw["headers"] = _headers
    kw["method"] = http_method
    kw["params"] = _params
    kw["url"] = self._url.format(**_url_data)
    result = self.http.request(**kw)
    if raise_for_status:
      result.raise_for_status()
    return result

  def request(self, *args, **kwargs) -> requests.Response:
    """Отправить запрос к API"""
    return self._request(*args, **kwargs)
