from argparse import ArgumentParser
from MainShortcuts2.ex.pathlib_ex import Path
from MPL.java_launch import manager
from MPL.java_launch.infofile import _Dependency
from MPL.java_launch.util import detect_java_version, find_system_java
from MainShortcuts2.utils import main_func
from subprocess import CompletedProcess
argp = ArgumentParser()
argp.epilog = "Часть библиотеки MainShortcuts2"


def format_dep(n: str, d: _Dependency, G: str, N: str, R: str):
  file = manager.cache_root / d.file_name
  star = "*" if d.required else ""
  return f"{G if file.exists() else R}{n}{star}: {d.file_url}{N}"


def format_ver(v: list[int]):
  return ".".join(map(str, v))


def print_info(args=None):
  if args is None:
    argp.add_argument("jar", type=Path, help="путь к файлу JAR")
    argp.description = "Просмотр информации из файла `.ms2/java_launch.json`"
    args = argp.parse_args()
  try:
    import colorama
    colorama.init()
    G = colorama.Fore.GREEN
    N = colorama.Fore.RESET
    R = colorama.Fore.RED
  except Exception:
    G, N, R = ""
  info = manager.read_info(args.jar)
  ver_prefix = R
  if G:
    try:
      cur_ver = detect_java_version(find_system_java())
      if info.java_version[0] <= cur_ver <= info.java_version[1]:
        ver_prefix = G
    except Exception:
      pass
  print(f"Версия Java: {ver_prefix}{format_ver(info.java_version[0])}-{format_ver(info.java_version[1])}{N}")
  if info.main_class_name:
    print(f"Основной класс: {info.main_class_name}")
  print("Все классы:")
  for k, v in info.classes.items():
    print(f"- {k}:")
    print(f"  Класс: {v.name}")
    if v.java_args:
      print(f"  Аргументы Java: {v.java_args}")
    if v.required_names:
      print(f"  Зависимости: {", ".join(v.required_names)}")
    if v.optional_names:
      print(f"  Необязательные зависимости: {", ".join(v.optional_names)}")
  if info.dependencies:
    print("Список зависимостей:")
    for k, v in info.dependencies.items():
      print(f"- {format_dep(k, v, G, N, R)}")
  return 0


@main_func(__name__)
def launch(args=None):
  if args is None:
    argp.add_argument("--download-optional", action="store_true", help="скачивать необязательные зависимости")
    argp.add_argument("--java", type=Path, help="путь к исполняемому файлу Java")
    argp.add_argument("-c", "--class-name", help="выбрать класс для запуска")
    argp.add_argument("jar", type=Path, help="путь к файлу JAR")
    argp.add_argument("args", nargs="*", help="аргументы для программы")
    argp.description = "Лаунчер программ Java с автоматической загрузкой зависимостей"
    args = argp.parse_args()
  p: CompletedProcess = manager.launch_file(
      args.jar, args.args,
      class_name=args.class_name,
      download_optional=args.download_optional,
      java_bin=args.java,
  )
  return p.returncode
