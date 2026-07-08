import os
import pathlib
import shutil
import typing
import enum
from functools import cached_property
from MainShortcuts2 import ms
from os import fspath
from stat import S_ISDIR, S_ISREG


class ms2hash_version(enum.IntEnum):
  LEGACY = enum.auto()
  V0 = enum.auto()
  VA = enum.auto()
  VB = enum.auto()
  VH = enum.auto()


class Path(pathlib.Path):
  @cached_property
  def ms_path(self):
    """Объект `ms.path.Path`"""
    return ms.path.Path(self)

  def size(self, recursive=False, **walk_kw) -> int:
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
    tmp = real.with_name(self.name + ".tmp" + ms.utils.randstr(4))
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
    try:
      with tmp.open("w", **kw) as f:
        result = f.write(data)
      tmp.replace(real)
    except:
      tmp.unlink(True)
      raise
    return result

  def write_bytes(self, data: bytes, **kw) -> int:
    tmp, real = self._get_write_path()
    try:
      with tmp.open("wb", **kw) as f:
        result = f.write(data)
      tmp.replace(real)
    except:
      tmp.unlink(True)
      raise
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
  if not typing.TYPE_CHECKING:
    def samefile(self, other_path):
      """Добавление проверки пути к файлу, чтобы не выполнять stat лишний раз"""
      if os.fspath(self) == os.fspath(other_path):
        return True
      return super().samefile(other_path)

  def samestat(self, st2: os.stat_result):
    """Аналогично `.samefile`, но принимает `stat_result` вместо пути"""
    st1 = self.stat()
    return st1.st_dev == st2.st_dev and st1.st_ino == st2.st_ino

  def write_ms2dat(self, data, **kw):
    """Сохранить данные в последней версии формата MS2Dat"""
    ms.ms2dat.write_file(data, self, **kw)

  def write_ms2dat_v1(self, data, ms2dat_inst=None, **kw):
    """Сохранить данные в формате MS2Dat v1"""
    if ms2dat_inst is None:
      ms2dat_inst = ms.ms2dat_v1.inst
    ms2dat_inst.write_file(data, self, **kw)

  def read_ms2dat(self, **kw):
    """Прочитать данные в формате MS2Dat"""
    return ms.ms2dat.read_file(self, **kw)

  def copy_to_io(self, fdest: typing.BinaryIO):
    """Скопировать содержимое в открытый файл"""
    with self.open("rb") as fsrc:
      shutil.copyfileobj(fsrc, fdest)

  def _compress(self, opn: typing.Callable[[typing.Self], typing.BinaryIO], suffix: str, dest: os.PathLike = None, keep=False, **kw):
    if dest is None:
      dest = self.with_name(self.name + suffix)
    else:
      dest = type(self)(dest)
    with opn(dest, **kw) as f:
      self.copy_to_io(f)
    if not keep:
      self.unlink()
    return dest

  def compress_bz2(self, dest=None, keep=False, **kw):
    """Сжать через bzip2"""
    import bz2
    return self._compress(bz2.open, ".bz2", dest, keep, mode="wb", **kw)

  def compress_gzip(self, dest=None, keep=False, **kw):
    """Сжать через gzip"""
    import gzip
    return self._compress(gzip.open, ".gz", dest, keep, mode="wb", **kw)

  def compress_lzma(self, / dest=None, keep=False, **kw):
    """Сжать через lzma"""
    import lzma
    return self._compress(lzma.open, ".lzma", dest, keep, mode="wb", **kw)

  def compress_zstd(self, dest=None, keep=False, **kw):
    """Сжать через zstandard"""
    import zstandard
    return self._compress(zstandard.open, ".zst", dest, keep, mode="wb", **kw)

  def hash(self, alg: str, bufsize=2**18):
    """Хешировать файл одним алгоритмом"""
    import hashlib
    with self.open("rb") as f:
      return hashlib.file_digest(f, alg, _bufsize=bufsize).digest()

  def hash_multi(self, algs: set[str], bufsize=2**18) -> dict[str, bytes]:
    """Хешировать файл несколькими алгоритмами"""
    if not algs:
      return {}
    import hashlib
    hashes = {i: hashlib.new(i) for i in algs}
    updaters = [i.update for i in hashes.values()]
    with self.open("rb") as f:
      read = f.read
      while True:
        buf = read(bufsize)
        if not buf:
          break
        for upd in updaters:
          upd(buf)
    return {k: v.digest() for k, v in hashes.items()}

  def generate_ms2hash(self, alg="sha3-256", overwrite=False, version=ms2hash_version.LEGACY, **kw):
    """Сгенерировать файл хеша рядом с этим файлом. **Внимание**: версия по умолчанию изменится в будущем обновлении"""
    if version == ms2hash_version.LEGACY:
      dest = self.with_name(self.name + ms.ms2hash.HASH_SUFFIX)
      if dest.exists() and not overwrite:
        raise FileExistsError(dest)
      hash = ms.ms2hash.Format1.generate(self, **kw)
      return dest.write_json(hash.to_dict())
    from MPL import ms2hash  # WIP, скоро будет в MS2
    if version == ms2hash_version.V0:
      v = ms2hash.VERSION_0
    elif version == ms2hash_version.VA:
      v = ms2hash.VERSION_A
    elif version == ms2hash_version.VB:
      v = ms2hash.VERSION_B
    elif version == ms2hash_version.VH:
      v = ms2hash.VERSION_H
    else:
      raise ValueError("Invalid hash version: %s" % version)
    dest = self.with_name(self.name + ms2hash.FILE_SUFFIX)
    if dest.exists() and not overwrite:
      raise FileExistsError(dest)
    hash = ms2hash.HashInfo.from_file(alg, self, **kw)
    return dest.write_bytes(hash.to_auto(v))
