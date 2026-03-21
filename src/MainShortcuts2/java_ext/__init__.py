import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from functools import cached_property
from MainShortcuts2 import ms
from MainShortcuts2.api import github
from MainShortcuts2.ex.pathlib_ex import Path
JAVA_VERSION_PATTERN = re.compile(r'version\s+"([^"]+)"')
SEARCH_RELEASE_COUNT = 1000


class AssetNotFoundError(Exception):
  pass


class VersionNotFoundError(Exception):
  pass


def find_system_java():
  plat = ms.advanced.get_platform()
  suffix = ".exe" if plat.is_mustdie else ""
  if os.environ.get("JAVA_HOME"):
    file = (Path(os.environ["JAVA_HOME"]) / f"bin/java{suffix}").resolve()
  else:
    str_file = shutil.which("java")
    if not str_file:
      raise RuntimeError("System java not found")
    file = Path(str_file).resolve()
  if not file.is_file():
    raise RuntimeError("System java not found")
  return file


def _parse_java_version(text: str):
  return list(map(int, text.split("_", 1)[0].split(".")))


def detect_java_version(file: Path):
  release_file = file.parent.parent / "release"
  if release_file.exists():
    try:
      for line in release_file.read_lines_iter(True):
        if "=" in line:
          k, v = map(str.strip, line.split("=", 1))
          if k == "JAVA_VERSION":
            return _parse_java_version(v.strip('"').strip("'"))
    except Exception:
      pass
  try:
    p = subprocess.run([str(file), "-version"], capture_output=True, check=True, text=True)
    match = JAVA_VERSION_PATTERN.search(p.stderr + p.stdout)
    return _parse_java_version(match.group(1))
  except Exception:
    raise RuntimeError("Couldn't determine the Java version") from None


class IncompatibleJava(Exception):
  pass


class InfoDict(dict):
  @property
  def builded_at(self):
    """Дата сборки релиза (Unix timestamp)"""
    return self["builded_at"]

  @cached_property
  def builded_at_dt(self):
    """Дата сборки релиза (`datetime`)"""
    return datetime.fromtimestamp(self.builded_at)

  @property
  def classes(self) -> dict[str, str]:
    """Словарь классов"""
    return self.get("classes", {})

  @property
  def max_java_version(self) -> list[int] | None:
    """Максимальная версия Java"""
    return self.get("max_java_version")

  @property
  def min_java_version(self) -> list[int] | None:
    """Минимальная версия Java"""
    return self.get("max_java_version")

  @property
  def name(self):
    """Название"""
    return self["name"]

  @property
  def version(self):
    """Название версии"""
    return self["version"]

  @property
  def version_id(self):
    """ID версии"""
    return self["version_id"]

  def check_java_file(self, file: Path):
    if (self.max_java_version is None) and (self.min_java_version is None):
      return True  # Нет информации о версии
    return self.check_java_version(detect_java_version(file))

  def check_java_version(self, version: list[int]):
    if self.max_java_version is not None:
      if version > self.max_java_version:
        raise IncompatibleJava(f"Incompatible Java version (current: {version}, max: {self.max_java_version})")
    if self.min_java_version is not None:
      if self.min_java_version > version:
        raise IncompatibleJava(f"Incompatible Java version (current: {version}, min: {self.min_java_version})")
    return True

  def version_id_in_range(self, min_id=0, max_id=sys.maxsize):
    """Проверить находится ли ID версии в диапазоне"""
    return bool(min_id <= self.version_id < max_id)


class JavaExtManager(ms.ObjectBase):
  """Менеджер версий JAR файла с кешированием"""

  def __init__(self, repo_owner: str, repo_name: str, github_token=None):
    self.gh = github.Client.from_env(True, token=github_token)
    self.repo = repo_owner, repo_name
    self.version_cache: "dict[str,JavaExtVersion]" = {}

  @cached_property
  def dir(self):
    """Папка кеша"""
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
    result = base / "MainPlay_TG/MainShortcuts2/java_ext_cache_v1" / self.repo[0] / self.repo[1]
    return result.resolve().any_mkdir()

  def get_version(self, version_name: str):
    """Получить определённую версию (по названию)"""
    if not version_name in self.version_cache:
      version = JavaExtVersion(self, version_name)
      if version.info.version == version_name:
        self.version_cache[version_name] = version
    return self.version_cache[version_name]

  def iter_online_releases(self, count=github.MAX_PER_PAGE):
    """Итерация релизов с GitHub"""
    return self.gh.releases.list_iter(*self.repo, count)

  def iter_online_versions(self, count=github.MAX_PER_PAGE):
    """Итерация версий с GitHub"""
    for rel in self.iter_online_releases(count):
      if rel.tag_name.startswith("v"):
        ver = self.get_version(rel.tag_name[1:])
        ver.__dict__["release"] = rel  # cached_property
        yield ver

  def iter_offline_versions(self):
    """Итерация версий из кэша"""
    for file in self.dir.iterdir():
      if file.suffix == ".json" and file.is_file():
        info = InfoDict(file.read_json())
        ver = self.get_version(info.version)
        ver.__dict__["info"] = info  # cached_property
        yield ver

  def iter_all_versions(self, online_count=github.MAX_PER_PAGE):
    """Итерация версий из кэша и с GitHub"""
    yield from self.iter_offline_versions()  # Сначала локальные
    yield from self.iter_online_versions(online_count)

  def search_has_class(self, class_name: str, max_count=SEARCH_RELEASE_COUNT):
    """Найти версию с указанным классом"""
    return self.search_has_classes([class_name], max_count)

  def search_has_classes(self, class_names: set[str], max_count=SEARCH_RELEASE_COUNT):
    """Найти версию, в которой есть все указанные классы"""
    class_names = set(class_names)
    for ver in self.iter_all_versions(max_count):
      classes = ver.info.classes
      if all(i in classes for i in class_names):
        return ver
    if len(class_names) == 1:
      raise VersionNotFoundError("Has class: " + class_names.pop())
    raise VersionNotFoundError("Has classes: " + ", ".join(class_names))

  def search_version_id_range(self, min_id: int = 0, max_id=sys.maxsize, max_count=SEARCH_RELEASE_COUNT):
    """Найти версию с ID в указанном диапазоне"""
    for ver in self.iter_all_versions(max_count):
      if ver.info.version_id_in_range(min_id, max_id):
        return ver
    raise VersionNotFoundError(f"{min_id} <= version_id <= {max_id}")

  def search_version_id(self, version_id: int, max_count=SEARCH_RELEASE_COUNT):
    """Найти версию с указанным ID"""
    for ver in self.iter_all_versions(max_count):
      if ver.info.version_id == version_id:
        return ver
    raise VersionNotFoundError(f"version_id == {version_id}")

  def download_latest(self, count=1, download_jar=True):
    """Скачать последнюю версию (если не скачана)"""
    for ver in self.iter_online_versions(count):
      ver.info  # Скачать файл JSON
      if download_jar:
        ver.jar_path  # Скачать файл JAR


class JavaExtVersion(ms.ObjectBase):
  """Версия JAR файла"""

  def __init__(self, mgr: JavaExtManager, version_name: str):
    self._java_bin = None
    self._java_checked = True
    self.mgr = mgr
    self.version_name = version_name

  @cached_property
  def release(self):
    """Релиз этой версии на GitHub"""
    return self.mgr.gh.releases.get_by_tag_name(*self.mgr.repo, "v" + self.version_name)

  @cached_property
  def info_asset(self):
    """Ассет файла информации на GitHub"""
    return self._get_asset("info.json")

  @cached_property
  def info(self):
    """Информация о версии (кэшируется)"""
    if self.info_path.exists():
      return InfoDict(self.info_path.read_json())
    with ms.utils.request("GET", self.info_asset.browser_download_url, session=self.mgr.gh.http) as resp:
      data = InfoDict(resp.json())
    self.info_path.write_json(data)
    return data

  @cached_property
  def info_path(self):
    """Путь к файлу информации"""
    return self.mgr.dir / f"{self.version_name}.json"

  @cached_property
  def jar_asset(self):
    """Ассет JAR файла на GitHub"""
    return self._get_asset(f"{self.info.name}-{self.info.version}.jar")

  @cached_property
  def _jar_path(self):
    """Файл JAR (без скачивания)"""
    return self.mgr.dir / f"{self.version_name}.jar"

  @property
  def jar_path(self):
    """Файл JAR (кэшируется)"""
    if not self._jar_path.exists():
      ms.utils.mini_log("[MainShortcuts2/java_ext] Downloading %s from %s/%s (%s)", self._jar_path.name, *self.mgr.repo, self.jar_asset.browser_download_url)
      self.jar_asset.download(self._jar_path)
    return self._jar_path

  @property
  def java_bin(self) -> Path:
    """Путь к исполняемому файлу Java (можно изменить)"""
    if self._java_bin is None:
      self._java_bin = find_system_java()
      self._java_checked = False
    return self._java_bin

  @java_bin.setter
  def java_bin(self, v):
    if v is None:
      self._java_bin = None
      return
    file = Path(v).resolve()
    if not file.exists():
      raise FileNotFoundError(file)
    self._java_bin = file
    self._java_checked = False

  def _get_asset(self, name: str):
    for i in self.release.assets:
      if i.name == name:
        return i
    raise AssetNotFoundError(name)

  def delete_cache(self, keep_info=True):
    """Удалить версию из кэша (будет скачана автоматически при использовании"""
    self._jar_path.remove()
    if not keep_info:
      self.info_path.remove()

  def _popen(self, args, **kw):
    if not self._java_checked:
      self.info.check_java_file(self.java_bin)
      self._java_checked = True
    return subprocess.Popen([str(self.java_bin), *args], **kw)

  def _run(self, args, **kw) -> subprocess.CompletedProcess:
    kw.setdefault("check", True)
    if not self._java_checked:
      self.info.check_java_file(self.java_bin)
      self._java_checked = True
    return subprocess.run([str(self.java_bin), *args], **kw)

  def popen_class_raw(self, class_path: str, args: list[str] = [], **kw):
    return self._popen(["-cp", str(self.jar_path), class_path, *args], **kw)

  def popen_class(self, class_name: str, args: list[str] = [], **kw):
    return self.popen_class_raw(self.info.classes[class_name], args, **kw)

  def popen(self, args: list[str], **kw):
    return self._popen(["-jar", str(self.jar_path), *args], **kw)

  def run_class_raw(self, class_path: str, args: list[str] = [], **kw):
    return self._run(["-cp", str(self.jar_path), class_path, *args], **kw)

  def run_class(self, class_name: str, args: list[str] = [], **kw):
    return self.run_class_raw(self.info.classes[class_name], args, **kw)

  def run(self, args: list[str], **kw):
    return self._run(["-jar", str(self.jar_path), *args], **kw)
