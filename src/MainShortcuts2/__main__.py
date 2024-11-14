import argparse
import sys
from MainShortcuts2 import ms
HASH_SUFFIX = ".MS2_hash"
HASH_TYPES = ["sha1", "sha256", "sha512"]


def import_example():
  argp = argparse.ArgumentParser("ms2-import_example", description="код для импорта MainShortcuts2")
  argp.parse_args()
  print("from MainShortcuts2 import ms")


def nano_json():
  ms.utils.check_programs("nano")
  import subprocess
  argp = argparse.ArgumentParser("nano-json", description="форматирование JSON файлов и редактирование в GNU NANO")
  argp.add_argument("files", nargs="+", help="пути к файлам JSON")
  argp.add_argument("--nano-help", action="store_true", help="показать помощь nano")
  argp.add_argument("-f", "--rcfile", help="использовать только этот файл для настройки nano")
  argp.add_argument("-m", "--mode", choices=ms.json.MODES, default="p", help="режим сохранения редактирования")
  args = argp.parse_args()
  if args.nano_help:
    return subprocess.call(["nano", "--help"])
  nano_args = ["nano"]
  if args.rcfile:
    nano_args += ["--rcfile", args.rcfile]
  nano_args += args.files
  for i in args.files:
    try:
      data = ms.json.read(i)
      ms.json.write(i + ms.file.TMP_SUFFIX, data, ensure_ascii=False, mode="p")
      ms.file.delete(i)
      ms.file.move(i + ms.file.TMP_SUFFIX, i)
    except Exception as err:
      print(err, file=sys.stderr)
  subprocess.call(nano_args)
  for i in args.files:
    try:
      data = ms.json.read(i)
      ms.json.write(i + ms.file.TMP_SUFFIX, data, mode=args.mode)
      ms.file.delete(i)
      ms.file.move(i + ms.file.TMP_SUFFIX, i)
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


def hash_gen():
  import os
  import hashlib
  argp = argparse.ArgumentParser("ms2-hash-gen", description="создание контрольной суммы для файла")
  argp.add_argument("files", nargs="+", help="пути к файлам")
  argp.add_argument("-t", "--type", choices=HASH_TYPES, default="sha512", help="тип контрольной суммы")
  args = argp.parse_args()
  data = {}
  data["format"] = "MainShortcuts2_hash_v1"
  data["file"] = {}
  data["hash"] = {}
  data["hash"]["type"] = args.type
  Hash = getattr(hashlib, args.type)
  for file in args.files:
    hash = Hash()
    data["file"]["size"] = os.path.getsize(file)
    with open(file, "rb") as f:
      for chunk in f:
        hash.update(chunk)
    data["hash"]["hex"] = hash.hexdigest()
    ms.json.write(file + HASH_SUFFIX, data)


def hash_check()


import hashlib
import os
import shlex
argp = argparse.ArgumentParser("ms2-hash-check", description="проверка размера и контрольной суммы файла")
argp.add_argument("files", nargs="+", help="пути к файлам")
args = argp.parse_args()
for file in args.files:
    if file.lower().endswith(HASH_SUFFIX.lower()):
      file = file[:0 - len(HASH_SUFFIX)]
    if not os.path.exists(file + HASH_SUFFIX):
      print("Ошибка: не найден файл " + shlex.quote(file + HASH_SUFFIX), file=sys.stderr)
      continue
    data = ms.json.read(file + HASH_SUFFIX)
    if data["file"]["size"] != os.path.getsize(file):
      print("Ошибка: размер файла " + shlex.quote(file) + " не совпадает")
      continue
    hash = getattr(hashlib, data["hash"]["type"])()
    with open(file, "rb") as f:
      for chunk in f:
        hash.update(chunk)
    if data["hash"]["hex"] == hash.hexdigest():
      print("Успех: файл " + shlex.quote(file) + " не изменён")
    else:
      print("Ошибка: файл " + shlex.quote(file) + " изменён")
