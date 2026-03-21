import importlib
import sys
from MainShortcuts2.ex.aiohttp_ex.web import *


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
