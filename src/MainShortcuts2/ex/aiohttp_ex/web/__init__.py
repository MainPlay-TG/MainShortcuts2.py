import base64
import json
import os
import typing
import uuid
import warnings
from aiohttp import BasicAuth, hdrs, web
from aiohttp.typedefs import Handler
from aiohttp.web import FileResponse, Request, Response, StreamResponse
from datetime import datetime, timedelta
from logging import DEBUG
from MainShortcuts2 import ms
from pathlib import Path, PurePath
warnings.filterwarnings("ignore", "Inheritance class .* from web.Application is discouraged", DeprecationWarning)
PATH_TYPES = os.PathLike, PurePath


def wrap_handler(app: "Application", handler: Handler):
  """Обернуть обработчик запросов"""
  async def wrapper(req: Request) -> StreamResponse | typing.Any:
    """Обёртка с поддержкой ответов `int`, `ApiResult` и `os.PathLike`"""
    try:
      resp = await handler(req)
      if isinstance(resp, int):  # Код статуса
        resp = Response(status=resp)
      elif isinstance(resp, ApiResult):  # Результат API обработчика
        resp = resp.make_resp(req.content_type)
      elif isinstance(resp, PATH_TYPES):  # Локальный файл
        resp = FileResponse(resp)
    except ApiResult as exc:  # Результат API исключения
      resp = exc.make_resp(req.content_type)
    except Exception as exc:
      app.logger.exception("Failed to process request", exc_info=exc)
      resp = Response(status=500, reason="Internal server error")
    if app.logger.isEnabledFor(DEBUG):
      remote = req.remote or "unknown"
      if "X-Real-IP" in req.headers:
        remote += " (X-Real-IP: %s)" % req.headers["X-Real-IP"]
      status = resp.status if isinstance(resp, StreamResponse) else repr(resp)
      app.logger.debug("Request %s %s from %s, return %s", req.method, req.raw_path, remote, status)
    return resp
  return wrapper


class Application(web.Application):
  def run(self, **kw):
    """Запустить приложение"""
    kw.setdefault("print", self.logger.info)
    web.run_app(self, **kw)

  def run_local(self, port: int, **kw):
    """Запустить локально на указанном порту"""
    self.run(host="127.0.0.1", port=port, **kw)

  def on_request(self, methods: str | list[str], paths: str | list[str], add_slash=True, **kw):
    """Зарегистрировать обработчик запросов"""
    if isinstance(methods, str):
      methods = [methods]
    if isinstance(paths, str):
      paths = [paths]

    def deco(func: Handler):
      wrapper = wrap_handler(self, func)
      for m in methods:
        for p in paths:
          self._on_request(wrapper, m, p, add_slash, **kw)
      return func
    return deco

  def _on_request(self, func: Handler, method: str, path: str, add_slash=True, **kw):
    if path == "/":
      add_slash = False
    if add_slash:
      path = path.rstrip("/")
    self.router.add_route(method, path, func, **kw)
    if add_slash:
      self.router.add_route(method, path + "/", func, **kw)

  def on_any_path_request(self, methods: str | list[str], **kw):
    """Зарегистрировать обработчик запросов на любой путь"""
    return self.on_request(methods, "/{tail:.*}", False, **kw)


def auth_header(header=hdrs.AUTHORIZATION, value=None):
  """Простая авторизация заголовком. Если не указать требуемое значение, будет проверять только наличие заголовка"""
  def deco(func: Handler):
    async def wrapper(req: Request):
      if header in req.headers:
        if value is not None:
          if req.headers[header] != value:
            return Response(status=403)  # Заголовок не совпадает
        return await func(req)  # Заголовок совпадает или значение не указано
      return Response(status=401)  # Заголовок отсутствует
    return wrapper
  return deco


basic_unauthorized_headers = {"WWW-Authenticate": 'Basic realm="Basic Auth"'}


def auth_basic(header=hdrs.AUTHORIZATION, filter: typing.Callable[[BasicAuth], bool] = ms.utils.return_True):
  """Авторизация `Basic`. Если не указать фильтр, только проверяет наличие заголовка"""
  def deco(func: typing.Callable[[Request, BasicAuth], typing.Awaitable[StreamResponse]]):
    async def wrapper(req: Request):
      if header in req.headers:
        try:
          auth = BasicAuth.decode(req.headers[header])
        except Exception:
          return Response(status=400, headers=basic_unauthorized_headers)  # Неправильный заголовок
        if filter(auth):
          return await func(req, auth)  # Одобрено
        return Response(status=403, headers=basic_unauthorized_headers)  # Запрещено
      return Response(status=401, headers=basic_unauthorized_headers)  # Заголовок отсутствует
    return wrapper
  return deco


class ApiResult(BaseException):
  """Результат для вызова API. Может быть вызван как исключение"""

  def __init__(self, result=None, status=200, **base_dict):
    super().__init__("This exception should be handled as a response to the request")
    self.base_dict = base_dict
    self.result = result
    self.status = status

  def to_dict(self):
    r = self.base_dict.copy()
    r["ok"] = self.status < 400
    if self.result is not None:
      r["result"] = self.result
    return r

  def _serialize_ms2dat(self, obj, other_serializer=None):
    """Для форматов, не поддерживающих `bytes`, `datetime`, `timedelta` и `UUID`"""
    if isinstance(obj, bytes):  # Base64
      return base64.b64encode(obj).decode("utf-8")
    if isinstance(obj, datetime):  # ISO
      return obj.isoformat()
    if isinstance(obj, timedelta):  # секунды
      return obj.total_seconds()
    if isinstance(obj, uuid.UUID):  # HEX
      return str(obj)
    if other_serializer is None:  # Другого сериализатора нет
      raise TypeError(f"Object of type {obj.__class__.__name__} is not serializable")
    return other_serializer(obj)

  def _to_json(self):
    # Минимальный размер за счёт
    # коротких разделителей
    # и отсутвия \uXXXX кодов
    return "application/json", json.dumps(
        self.to_dict(),
        default=self._serialize_ms2dat,
        ensure_ascii=False,
        separators=(",", ":"),
    )

  def _to_yaml(self):
    import yaml
    return "application/yaml", yaml.safe_dump(self.to_dict())

  def _to_xml(self):
    raise NotImplementedError()

  def _to_ms2dat1(self) -> tuple[str, bytes]:
    from MainShortcuts2 import ms2dat1
    return "application/x-ms2dat1", ms2dat1.dumps(self.to_dict())

  def make_resp(self, content_type=None):
    """Создать ответ в указаном формате, по умолчанию JSON"""
    try:
      if content_type == "application/x-ms2dat1":
        ctype, body = self._to_ms2dat1()
      elif content_type == "application/yaml":
        ctype, body = self._to_yaml()
      else:  # Если запрошенный формат не поддерживается
        ctype, body = self._to_json()
    except ImportError:  # Если формат не поддерживается
      ctype, body = self._to_json()  # JSON должен сработать
    # Клиент должен проверять формат ответа, на случай если он не соответствует запрошенному
    if isinstance(body, str):
      return web.Response(status=self.status, text=body, content_type=ctype)
    return web.Response(status=self.status, body=body, content_type=ctype)


class ApiError(ApiResult):
  """Ошибка API. Можно вызывать как исключение"""

  def __init__(self, message: str, status=400, **base_dict):
    base_dict["message"] = message
    super().__init__(status=status, **base_dict)
