import os
import pathlib
import shutil
from MainShortcuts2 import ms
from os import fspath
from stat import S_ISDIR, S_ISREG


class Path(pathlib.Path):
  @property
  def ms_path(self):
    """Объект `ms.path.Path`"""
    return ms.path.Path(self)

  def size(self, recursive=False, **walk_kw):
    """Вычислить размер файла/папки"""
    st = self.stat()
    if S_ISREG(st.st_mode):
      return st.st_size
    if recursive:
      if S_ISDIR(st.st_mode):
        result = 0
        for _, _, files in self.walk2(**walk_kw):
          result += sum(i.size() for i in files)
        return result
    raise IsADirectoryError(self)

  def walk2(self, **kw):
    """Итерация `(root: Path, dirs: list[Path], files: list[Path])`"""
    for root, dirnames, filenames in self.walk(**kw):
      dirs = [root / i for i in dirnames]
      files = [root / i for i in filenames]
      yield root, dirs, files

  def move_to(self, target):
    """Переместить файл/папку в указанное место"""
    shutil.move(fspath(self), fspath(target))
    return Path(target)

  def copy_to(self, target, follow_symlinks=True, recursive=False, **copytree_kw):
    """Копировать файл/папку в указанное место"""
    if recursive:
      if self.is_dir():
        shutil.copytree(fspath(self), fspath(target), **copytree_kw)
        return Path(target)
    shutil.copy2(fspath(self), fspath(target), follow_symlinks=follow_symlinks)
    return Path(target)

  def remove(self, missing_ok=True, recursive=False, **rmtree_kw):
    """Удалить файл/папку"""
    if recursive:
      if self.is_dir() and not self.is_symlink():
        return shutil.rmtree(fspath(self), **rmtree_kw)
    self.unlink(missing_ok=missing_ok)

  def _get_write_path(self):
    """tmp,real"""
    real = self.resolve()
    tmp = real
    while tmp.exists():
      tmp = real.with_name(self.name + ".tmp" + ms.utils.randstr(4))
    return tmp, real

  def read_text(self, **kw):
    """Прочитать весь текст из файла"""
    kw.setdefault("encoding", "utf-8")
    with self.open("r", **kw) as f:
      return f.read()

  def write_text(self, data: str, **kw) -> int:
    kw.setdefault("encoding", "utf-8")
    """Записать текст в файл"""
    tmp, real = self._get_write_path()
    with tmp.open("w", **kw) as f:
      result = f.write(data)
    if not tmp.samefile(real):
      tmp.replace(real)
    return result

  def write_bytes(self, data, **kw) -> int:
    tmp, real = self._get_write_path()
    with tmp.open("wb", **kw) as f:
      result = f.write(data)
    if not tmp.samefile(real):
      tmp.replace(real)
    return result

  def read_json(self, **kw):
    """Прочитать файл как JSON"""
    return ms.json.read(self, **kw)

  def write_json(self, data, **kw) -> int:
    """Записать JSON в файл"""
    return ms.json.write(self, data, **kw)

  def any_mkdir(self, **kw):
    """Создать папку игнорируя ошибки"""
    self.mkdir(parents=True, exist_ok=True, **kw)
    return self

  def clear_dir(self, mkdir=False, **kw):
    """Очистить папку"""
    if mkdir:
      self.any_mkdir()
    kw.setdefault("recursive", True)
    for i in self.iterdir():
      i.remove(**kw)
    return self

  def read_lines_iter(self, remove_ends=False, **kw):
    """Прочитать строки из файла (итератор)"""
    with self.open("r", **kw) as f:
      while True:
        line = f.readline()
        if line:
          if remove_ends and line.endswith("\n"):
            line = line[:-1]
          yield line
        else:
          break

  def read_lines(self, remove_ends=False, **kw):
    """Прочитать строки из файла"""
    return list(self.read_lines_iter(remove_ends, **kw))

  def walk_relative(self, **kw):
    """Рекурсивный обход папок с относительными путями"""
    self = self.resolve()
    for root, dirnames, filenames in os.walk(fspath(self), **kw):
      rel_root = str(Path(root).relative_to(self))
      if rel_root == ".":
        rel_root = ""
      yield rel_root, dirnames, filenames

  def list_relative(self, recursive=False, **kw):
    """Сканирование папки с относительными путями"""
    if recursive:
      for root, dirnames, filenames in self.walk_relative(**kw):
        yield from [os.path.join(root, i) for i in dirnames]
        yield from [os.path.join(root, i) for i in filenames]
    else:
      yield from os.listdir(self)
