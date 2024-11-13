import argparse
import sys
from MainShortcuts2 import ms


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
  if nano_args.rcfile:
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
