import os
import subprocess
from .infofile import InfoFile, _ClassInfo
from .util import detect_java_version
from .util import find_system_java
from .util import IncompatibleJava
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property
from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
from zipfile import ZipFile


class JavaLaunchManager:
  @cached_property
  def cache_root(self):
    plat = ms.advanced.get_platform()
    if plat.is_mustdie:
      if os.environ.get("LOCALAPPDATA"):
        base = Path(os.environ["LOCALAPPDATA"])
      else:
        base = Path.home() / "AppData/Local"
    else:
      if os.environ.get("XDG_DATA_HOME"):
        base = Path(os.environ["XDG_DATA_HOME"])
      else:
        base = Path.home() / ".local/share"
    return base / "MainPlay_TG/MainShortcuts2/java_launch_cache_v1"

  @cached_property
  def downloader(self):
    return ms.advanced.FileDownloader()

  def read_info(self, file: Path):
    """Прочитать информацию о JAR"""
    with file.open("rb") as f:
      zip = ZipFile(f, "r")
      data = zip.read(".ms2/java_launch.json").decode()
    return InfoFile(ms.json.decode(data))

  def download_depends(self, clazz: _ClassInfo, download_optional=False):
    """Скачать зависимости класса"""
    queue: set[tuple[str, Path]] = set()
    for i in clazz.required_depends:
      file = self.cache_root / i.file_name
      if not file.exists():
        file.parent.any_mkdir()
        queue.add((i.file_url, file))
    if download_optional:
      for i in clazz.optional_depends:
        file = self.cache_root / i.file_name
        if not file.exists():
          file.parent.any_mkdir()
          queue.add((i.file_url, file))
    with ThreadPoolExecutor() as pool:
      futures = [pool.submit(self.downloader.download2file, *i) for i in queue]
      [i.result() for i in futures]

  def launch_file(self, file: Path, args: list[str] = [], *,
                  class_name: str = None,
                  download_optional=False,
                  download_required=True,
                  info: InfoFile = None,
                  java_bin: Path = None,
                  wait_process=True,
                  **run_kw):
    """
    Запустить файл JAR

    :param file: Путь к файлу JAR
    :type file: Path
    :param args: Дополнительные аргументы
    :type args: list[str]
    :param class_name: Название класса. Если не указано, будет запущен основной класс
    :type class_name: str
    :param download_optional: Нужно ли скачивать необязательные библиотеки
    :param download_required: Нужно ли скачивать обязательные библиотеки
    :param info: Информация о JAR. Если не указана, будет загружена из самого файла
    :type info: InfoFile
    :param java_bin: Путь к Java. Если не указан, будет использована системная Java
    :type java_bin: Path
    :param wait_process: Нужно ли ждать завершения процесса. Выбирает метод запуска: `subprocess.run`/`Popen`
    :param run_kw: Аргументы для `subprocess.run`/`Popen`
    """
    # Получение информации
    if not info:
      info = self.read_info(file)
    # Подготовка класса
    if not class_name:
      class_name = info.main_class_name
      if not class_name:
        raise ValueError("No main class")
    if class_name not in info.classes:
      raise ValueError(f"Class {class_name} not found")
    clazz = info.classes[class_name]
    # Подготовка Java
    if not java_bin:
      java_bin = find_system_java()
    java_version = detect_java_version(java_bin)
    if not info.java_version[0] <= java_version <= info.java_version[1]:
      raise IncompatibleJava(f"Current: {java_version}, required: {info.java_version[0]}-{info.java_version[1]}")
    # Подготовка библиотек
    if download_required:
      self.download_depends(clazz, download_optional)
    # Запуск
    run_kw["args"] = [str(java_bin), *clazz.build_args(self.cache_root, file)]
    if args:
      run_kw["args"].extend(args)
    if wait_process:
      return subprocess.run(**run_kw)
    return subprocess.Popen(**run_kw)


manager = JavaLaunchManager()
