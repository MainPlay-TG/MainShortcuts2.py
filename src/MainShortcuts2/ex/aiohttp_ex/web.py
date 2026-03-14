import sys
import typing
import warnings
from aiohttp import BasicAuth, hdrs, web
from aiohttp.typedefs import Handler
from aiohttp.web import FileResponse, Request, Response, StreamResponse
from logging import DEBUG
from MainShortcuts2 import ms
from pathlib import Path
warnings.filterwarnings("ignore", "Inheritance class .* from web.Application is discouraged", DeprecationWarning)


def wrap_handler(app: "Application", handler: Handler):
  async def wrapper(req: Request) -> StreamResponse | typing.Any:
    try:
      resp = await handler(req)
      if isinstance(resp, int):
        resp = Response(status=resp)
      elif isinstance(resp, Path):
        resp = FileResponse(resp)
    except Exception as exc:
      app.logger.exception("Failed to process request", exc_info=exc)
      resp = Response(status=500, reason="Internal server error")
    if app.logger.isEnabledFor(DEBUG):
      remote = req.remote or "unknown"
      if "X-Real-IP" in req.headers:
        remote += " (real IP: %s)" % req.headers["X-Real-IP"]
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
        return Response(status=403)  # Запрещено
      return Response(status=401, headers=basic_unauthorized_headers)  # Заголовок отсутствует
    return wrapper
  return deco


@ms.utils.main_func(__name__)
def main(args=None, **kw):
  if args is None:
    from argparse import ArgumentParser
    argp = ArgumentParser()
    argp.add_argument("--backlog", default=128, type=int)
    argp.add_argument("--handler-cancellation", action="store_true")
    argp.add_argument("--handler", help="функция для обработки всех запросов (module:variable)")
    argp.add_argument("--keepalive-timeout", default=75, type=int)
    argp.add_argument("--no-handle-signals", action="store_true")
    argp.add_argument("--no-print", action="store_true", help="отключить вывод запросов")
    argp.add_argument("--shutdown-timeout", default=60, type=int)
    argp.add_argument("-H", "--host", default="127.0.0.1", help="IP для прослушивания")
    argp.add_argument("-p", "--port", default=8080, type=int, help="порт для прослушивания")
    argp.description = "Простой HTTP сервер, выводящий содержимое всех запросов"
    args = argp.parse_args()
  app = Application()
  log = ms.utils.mini_log
  if args.handler:
    import importlib
    m_name, f_name = args.handler.split(":", 1)
    custom_handler = getattr(importlib.import_module(m_name), f_name)
  else:
    async def custom_handler(req: Request):
      return 200
  do_print = not args.no_print

  @app.on_any_path_request(["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"])
  async def _(req: Request):
    if do_print:
      log("Request %s %s from %s", req.method, req.raw_path, req.remote)
      log("Headers:")
      for k, v in req.headers.items():
        log("- %s: %s", k, v)
      has_content = False
      async for chunk, _ in req.content.iter_chunks():
        if chunk:
          if not has_content:
            has_content = True
            log("Content: ")
          sys.stderr.buffer.write(chunk)
      log("")
    return await custom_handler(req)
  kw["backlog"] = args.backlog
  kw["handle_signals"] = not args.no_handle_signals
  kw["handler_cancellation"] = args.handler_cancellation
  kw["host"] = args.host
  kw["keepalive_timeout"] = args.keepalive_timeout
  kw["port"] = args.port
  kw["print"] = log
  kw["shutdown_timeout"] = args.shutdown_timeout
  app.run(**kw)
