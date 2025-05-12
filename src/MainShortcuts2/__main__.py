import argparse
import os
import sys
from MainShortcuts2 import ms


def import_example():
  argp = argparse.ArgumentParser("ms2-import_example", description="код для импорта MainShortcuts2")
  argp.parse_args()
  print("from MainShortcuts2 import ms")


def nano_json(args: argparse.Namespace = None):
  ms.utils.check_programs("nano")
  import subprocess
  if args is None:
    argp = argparse.ArgumentParser("nano-json", description="форматирование JSON файлов и редактирование в GNU NANO")
    argp.add_argument("files", nargs="+", help="пути к файлам JSON")
    argp.add_argument("--nano-help", action="store_true", help="показать помощь nano")
    argp.add_argument("-e", "--encoding", default="utf-8", help="кодировка файлов")
    argp.add_argument("-f", "--rcfile", help="использовать только этот файл для настройки nano")
    argp.add_argument("-i", "--indent", default=2, type=int, help="кол-во пробелов для отступа")
    argp.add_argument("-m", "--mode", choices=ms.json.MODES_ALL, default="p", help="режим сохранения редактирования")
    argp.add_argument("-s", "--sort", action="store_true", help="сортировать ключи словаря")
    argp.add_argument("-u", "--no-escape", action="store_false", help="не использовать Unicode Escape")
    args = argp.parse_args()
  if args.nano_help:
    return subprocess.call(["nano", "--help"])
  write_kw = {}
  write_kw["encoding"] = args.encoding
  write_kw["ensure_ascii"] = False
  write_kw["indent"] = args.indent
  write_kw["mode"] = "print"
  write_kw["sort_keys"] = args.sort
  nano_args = ["nano"]
  if args.rcfile:
    nano_args += ["--rcfile", args.rcfile]
  nano_args += args.files
  for i in args.files:
    try:
      data = ms.json.read(i, encoding=args.encoding)
      ms.json.write(i, data, **write_kw)
    except Exception as err:
      print(err, file=sys.stderr)
  subprocess.call(nano_args)
  write_kw["ensure_ascii"] = args.no_escape
  write_kw["indent"] = None if args.mode in ms.json.MODES_COMPRESS else args.indent
  write_kw["mode"] = args.mode
  for i in args.files:
    try:
      data = ms.json.read(i, encoding=args.encoding)
      ms.json.write(i, data, **write_kw)
    except Exception as err:
      print(err, file=sys.stderr)


def _check_nginx() -> int:
  import subprocess
  with subprocess.Popen(["nginx", "-t"], stderr=subprocess.PIPE) as p:
    code = p.wait()
    if code != 0:
      sys.stderr.buffer.write(p.stderr.read())
  return code


def nginx_reload():
  ms.utils.check_programs("nginx")
  import subprocess
  argp = argparse.ArgumentParser("nginx-reload", description="проверка конфига и перезагрузка Nginx")
  argp.parse_args()
  code = _check_nginx()
  if code != 0:
    sys.exit(code)
  sys.exit(subprocess.call(["nginx", "-s", "reload"]))


def nginx_restart():
  ms.utils.check_programs("nginx", "systemctl")
  import subprocess
  argp = argparse.ArgumentParser("nginx-reload", description="проверка конфига и перезапуск Nginx через systemctl")
  argp.parse_args()
  code = _check_nginx()
  if code != 0:
    sys.exit(code)
  sys.exit(subprocess.call(["systemctl", "restart", "nginx"]))


def ln(args=None):
  if args is None:
    argp = argparse.ArgumentParser("ms2-ln", description="создание символьной ссылки с абсолютным путём к файлу")
    argp.add_argument("-f", "--force", action="store_true", help="принудительное создание ссылки")
    argp.add_argument("file", help="путь к файлу, на который будет указывать ссылка")
    argp.add_argument("link", help="путь к ссылке для создания")
    args = argp.parse_args()
  if args.force:
    ms.path.delete(args.link)
  file = os.path.realpath(args.file)
  os.symlink(file, args.link, os.path.isdir(file))
