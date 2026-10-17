import hashlib
import os
from functools import cached_property
from MainShortcuts2.ex.pathlib_ex import Path
from MainShortcuts2.utils import short_urlsafe_b64encode
_rand = os.urandom(8)


class _ClassInfo(dict):
  """Информация об определённом классе"""

  def __init__(self, root: "InfoFile", map):
    super().__init__(map)
    self._root = root
    self.java_args: list[str] = self.get("java_args") or []
    """Дополнительные аргументы Java"""
    self.name: str = self.get("name")
    """Полное название класса"""
    self.optional_names: set[str] = set(self.get("optional") or [])
    """Необязательные зависимости"""
    self.required_names: set[str] = set(self.get("required") or [])
    """Обязательные зависимости"""
  @property
  def optional_depends(self):
    return {self._root.dependencies[i] for i in self.optional_names}

  @property
  def required_depends(self):
    return {*self._root.required_dependencies, *[self._root.dependencies[i] for i in self.required_names]}

  def build_args(self, cache_root: Path, file: Path):
    """Собрать список аргументов. Без пути к Java и пользовательских аргументов"""
    cp = {str(file), }
    # Собрать обязательные зависимости
    for i in self.required_depends:
      file = cache_root / i.file_name
      if not file.exists():
        raise FileNotFoundError(file)
      cp.add(str(file))
    # Собрать необязательные зависимости
    for i in self.optional_depends:
      file = cache_root / i.file_name
      if file.exists():
        cp.add(str(file))
    return [*self.java_args, "-cp", os.path.pathsep.join(cp), self.name]


class _Dependency(dict):
  """Информация о зависимости"""

  def __init__(self, root: "InfoFile", map):
    super().__init__(map)
    self._root = root
    self.artifact: str = self["artifact"]
    self.classifier: str = ("-" + self["classifier"]) if self.get("classifier") else ""
    self.ext: str = self.get("ext") or "jar"
    self.group: str = self["group"]
    self.repository_name: str | None = self.get("repository")
    """Название репозитория. Если не указано - Maven Central"""
    self.required = bool(self.get("required"))
    """Требуется ли для всего JAR"""
    self.size: int | None = self.get("size")
    self.version: str = self["version"]

  def __hash__(self):
    return hash(f"{_rand}_{self.file_url}")

  @property
  def repository_url(self):
    """Ссылка на репозиторий"""
    if self.repository_name:
      return self._root.repositories[self.repository_name]
    return "https://repo1.maven.org/maven2"

  @cached_property
  def file_name(self):
    """Название файла для кэша"""
    repo_hash = short_urlsafe_b64encode(hashlib.md5(self.repository_url.encode()).digest()).decode()
    return f"{repo_hash}/{self.group}/{self.artifact}-{self.version}{self.classifier}.{self.ext}"

  @property
  def file_url(self):
    """URL для скачивания файла"""
    return f"{self.repository_url}/{self.group.replace(".", "/")}/{self.artifact}/{self.version}/{self.artifact}-{self.version}{self.classifier}.{self.ext}"


class InfoFile(dict):
  """Информация для запуска JAR"""

  def __init__(self, map):
    super().__init__(map)
    self.classes: dict[str, _ClassInfo] = {k: _ClassInfo(self, v) for k, v in self["classes"].items()}
    """Все доступные для запуска классы"""
    self.dependencies: dict[str, _Dependency] = {k: _Dependency(self, v) for k, v in (self.get("dependencies") or {}).items()}
    """Список зависимостей (`alias:info`)"""
    self.format: int = self["format"]
    """Формат файла"""
    self.java_version: tuple[list[int], list[int]] = self["java_version"]
    """Требуемая версия Java (`min,max`)"""
    self.main_class_name: str | None = self.get("main_class")
    """Название основного класса"""
    self.repositories: dict[str, str] = {k: v.rstrip("/") for k, v in (self.get("repositories") or {})}
    """Список дополнительных репозиториев (`name:url`)"""
  @property
  def main_class(self):
    """Основной класс"""
    if self.main_class_name:
      return self.classes[self.main_class_name]

  @property
  def required_dependencies(self):
    """Зависимости, обязательные для всех классов"""
    return {i for i in self.dependencies.values() if i.required}
