import argparse
import sys
from MainShortcuts2 import ms
HASH_SUFFIX = ".MS2_hash"
HASH_TYPES = ["blake2b", "blake2s", "md5", "sha1", "sha224", "sha256", "sha384", "sha3_224", "sha3_256", "sha3_384", "sha3_512", "sha512"]


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


def hash_gen(args: argparse.Namespace = None):
  import hashlib
  import os
  import shlex
  if args is None:
    argp = argparse.ArgumentParser("ms2-hash_gen", description="создание контрольной суммы для файла")
    argp.add_argument("files", nargs="+", help="пути к файлам")
    argp.add_argument("-b", "--bar", action="store_true", help="показывать прогрессбар (нужен модуль progressbar2)")
    argp.add_argument("-f", "--force", action="store_true", help="перезаписывать существующие хеши")
    argp.add_argument("-t", "--type", choices=HASH_TYPES, default="sha512", help="тип контрольной суммы")
    args = argp.parse_args()
  pbar, pbar_w, progressbar = None, None, None
  if args.bar:
    import progressbar
    pbar_w = [progressbar.Percentage(), progressbar.GranularBar(left="(", right=")"), progressbar.FileTransferSpeed(), " ", progressbar.ETA(format="%(eta)8s", format_finished="%(elapsed)8s", format_na="     N/A", format_not_started="--:--:--", format_zero="00:00:00")]
  completed = []
  data = {}
  data["file"] = {}
  data["format"] = "MainShortcuts2_hash_v1"
  data["hash"] = {}
  data["hash"]["type"] = args.type
  Hash = getattr(hashlib, args.type)
  for file in args.files:
    while file.lower().endswith(HASH_SUFFIX.lower()):
      file = file[:0 - len(HASH_SUFFIX)]
    if file in completed:
      continue
    if os.path.isfile(file + HASH_SUFFIX):
      if not args.force:
        print("Пропуск файла " + shlex.quote(file) + ": хеш существует", file=sys.stderr)
        continue
    data["file"]["size"] = os.path.getsize(file)
    with open(file, "rb") as f:
      if args.bar:
        pbar = progressbar.ProgressBar(max_error=False, max_value=data["file"]["size"], widgets=[ms.path.Path(file).full_name] + pbar_w)
        c = 0
        pbar.start()
      hash = Hash()
      for chunk in f:
        hash.update(chunk)
        if args.bar:
          c += len(chunk)
          pbar.update(c)
    if args.bar:
      pbar.finish()
    data["hash"]["hex"] = hash.hexdigest()
    ms.json.write(file + HASH_SUFFIX, data)
    completed.append(file)


def hash_check(args: argparse.Namespace = None):
  import hashlib
  import os
  import shlex
  if args is None:
    argp = argparse.ArgumentParser("ms2-hash_check", description="проверка размера и контрольной суммы файла")
    argp.add_argument("files", nargs="+", help="пути к файлам")
    argp.add_argument("-b", "--bar", action="store_true", help="показывать прогрессбар (нужен модуль progressbar2)")
    args = argp.parse_args()
  pbar, pbar_w, progressbar = None, None, None
  if args.bar:
    import progressbar
    pbar_w = [progressbar.Percentage(), progressbar.GranularBar(left="(", right=")"), progressbar.FileTransferSpeed(), " ", progressbar.ETA(format="%(eta)8s", format_finished="%(elapsed)8s", format_na="     N/A", format_not_started="--:--:--", format_zero="00:00:00")]
  completed = []
  for file in args.files:
    while file.lower().endswith(HASH_SUFFIX.lower()):
      file = file[:0 - len(HASH_SUFFIX)]
    if file in completed:
      continue
    if not os.path.exists(file + HASH_SUFFIX):
      print("Ошибка: не найден файл " + shlex.quote(file + HASH_SUFFIX), file=sys.stderr)
      continue
    data = ms.json.read(file + HASH_SUFFIX)
    if data["file"]["size"] != os.path.getsize(file):
      print("Ошибка: размер файла " + shlex.quote(file) + " не совпадает", file=sys.stderr)
      continue
    if args.bar:
      pbar = progressbar.ProgressBar(max_error=False, max_value=data["file"]["size"], widgets=[ms.path.Path(file).full_name] + pbar_w)
      c = 0
      pbar.start()
    hash = getattr(hashlib, data["hash"]["type"])()
    with open(file, "rb") as f:
      for chunk in f:
        hash.update(chunk)
        if args.bar:
          c += len(chunk)
          pbar.update(c)
    if args.bar:
      pbar.finish()
    if data["hash"]["hex"] == hash.hexdigest():
      print("Успех: файл " + shlex.quote(file) + " не изменён")
    else:
      print("Ошибка: файл " + shlex.quote(file) + " изменён")
    completed.append(file)
