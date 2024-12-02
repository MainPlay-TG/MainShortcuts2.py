import os
from .base import Base, requests
from datetime import timedelta
from time import time
CERT_PATH = os.path.dirname(__file__) + "/russian_trusted_root_ca_pem.crt"


class GigaChat(Base):
  def __init__(self, auth_data: str, client_id: str, *,
               cert_path: str = None,
               **kw):
    self._init(**kw)
    self._access_token = {"expire_at": 0, "kw": None, "token": None}
    self._auth_data: str = auth_data
    self._client_id: str = client_id
    self._url = "https://gigachat.devices.sberbank.ru/api/v1/{method}"
    self.http.verify = CERT_PATH if cert_path is None else cert_path

  @property
  def access_token(self) -> str:
    if True:  # TODO Сделать проверку истёк ли токен доступа. Пока что каждый раз новый токен
      if self._access_token["kw"] is None:  # Если изменились данные для авторизации
        kw = {}
        kw["data"] = {}
        kw["headers"] = {}
        kw["stream"] = False
        kw["url"] = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        kw["data"]["scope"] = "GIGACHAT_API_PERS"
        kw["headers"]["Authorization"] = "Basic: " + self.auth_data
        kw["headers"]["Content-Type"] = "application/x-www-form-urlencoded"
        kw["headers"]["RqUID"] = self.client_id
        self._access_token["kw"] = kw
      else:
        kw = self._access_token["kw"]
      with self.http.post(**kw) as resp:  # Получить новый токен
        resp.raise_for_status()
        json = resp.json()
        self._access_token["expire_at"] = json["expires_at"] / 1000
        self._access_token["token"] = json["access_token"]
    return self._access_token["token"]

  @property
  def auth_data(self) -> str:
    return self._auth_data

  @auth_data.setter
  def auth_data(self, v: str):
    self._access_token["kw"] = None
    self._auth_data = v

  @property
  def client_id(self) -> str:
    return self._client_id

  @client_id.setter
  def client_id(self, v: str):
    self._access_token["kw"] = None
    self._client_id = v

  def request(self, http_method: str, api_method: str, **kw):
    self._headers["Authorization"] = "Bearer " + self.access_token
    kw["api_method"] = api_method
    kw["http_method"] = http_method
    return self._request(**kw).json()
  # TODO Добавить методы
