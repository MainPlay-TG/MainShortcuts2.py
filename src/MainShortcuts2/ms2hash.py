import argparse
import hashlib
import os
import shlex
import sys
from MainShortcuts2 import ms
HASH_SUFFIX = ".MS2_hash"
HASH_TYPES = ["blake2b", "blake2s", "md5", "sha1", "sha224", "sha256", "sha384", "sha3_224", "sha3_256", "sha3_384", "sha3_512", "sha512"]


class _NoPbar(ms.ObjectBase):
  finish = ms.utils.return_None
  start = ms.utils.return_None
  update = ms.utils.return_None
  value = 0


def get_pbar(filename: str, enabled: bool, **kw):
  if not enabled:
    return _NoPbar()
  try:
    import progressbar
  except Exception:
    return _NoPbar()
  kw.setdefault("max_error", False)
  kw.setdefault(
      "widgets",
      [
          filename,
          " ",
          progressbar.Percentage(),
          progressbar.GranularBar(
              left="(",
              right=")",
          ),
          progressbar.FileTransferSpeed(),
          " ",
          progressbar.ETA(
              format_finished="%(elapsed)8s",
              format_na="     N/A",
              format_not_started="--:--:--",
              format_zero="00:00:00",
              format="%(eta)8s",
          )
      ]
  )
  return progressbar.ProgressBar(**kw)


class Format1:
  def __init__(self, *, file_size: int, hash_hex: str, hash_type: str):
    assert hash_type in HASH_TYPES
    self.file_size = file_size
    self.hash_hex = hash_hex
    self.hash_type = hash_type

  @classmethod
  def from_dict(cls, data: dict, **kw):
    kw.setdefault("file_size", data["file"]["size"])
    kw.setdefault("hash_hex", data["hash"]["hex"])
    kw.setdefault("hash_type", data["hash"]["type"])
    return cls(**kw)

  @classmethod
  def generate(cls, path: str, enable_pbar: bool, **kw):
    file = ms.path.Path(path)
    kw.setdefault("hash_type", "sha512")
    hash: hashlib._Hash = getattr(hashlib, kw["hash_type"])()
    kw["file_size"] = file.size
    with open(path, "rb") as f:
      with get_pbar(file.full_name, enable_pbar, max_value=file.size) as pbar:
        pbar.start()
        for i in f:
          hash.update(i)
          pbar.update(pbar.value + len(i))
    kw["hash_hex"] = hash.hexdigest()
    return cls(**kw)

  def to_dict(self):
    data = {}
    data["file"] = {"size": self.file_size}
    data["format"] = "MainShortcuts2_hash_v1"
    data["hash"] = {"hex": self.hash_hex, "type": self.hash_type}
    return data


def hash_gen(args: argparse.Namespace = None):
  if args is None:
    argp = argparse.ArgumentParser("ms2-hash_gen", description="создание контрольной суммы для файла")
    argp.add_argument("files", nargs="+", help="пути к файлам")
    argp.add_argument("-b", "--bar", action="store_true", help="показывать прогрессбар (нужен модуль progressbar2)")
    argp.add_argument("-f", "--force", action="store_true", help="перезаписывать существующие хеши")
    argp.add_argument("-t", "--type", choices=HASH_TYPES, default="sha512", help="тип контрольной суммы")
    args = argp.parse_args()
  completed = []
  for file in args.files:
    while file.lower().endswith(HASH_SUFFIX.lower()):
      file = file[:0 - len(HASH_SUFFIX)]
    if file in completed:
      continue
    if os.path.isdir(file):
      print("Пропуск файла " + shlex.quote(file) + ": это папка", file=sys.stderr)
      completed.append(file)
      continue
    if os.path.isfile(file + HASH_SUFFIX):
      if not args.force:
        print("Пропуск файла " + shlex.quote(file) + ": хеш существует", file=sys.stderr)
        continue
    hash = Format1.generate(file, args.bar, hash_type=args.type)
    ms.json.write(file + HASH_SUFFIX, hash.to_dict())
    completed.append(file)


def hash_check(args: argparse.Namespace = None):
  if args is None:
    argp = argparse.ArgumentParser("ms2-hash_check", description="проверка размера и контрольной суммы файла")
    argp.add_argument("files", nargs="+", help="пути к файлам")
    argp.add_argument("-b", "--bar", action="store_true", help="показывать прогрессбар (нужен модуль progressbar2)")
    args = argp.parse_args()
  completed = []
  for file in args.files:
    while file.lower().endswith(HASH_SUFFIX.lower()):
      file = file[:0 - len(HASH_SUFFIX)]
    if file in completed:
      continue
    if os.path.isdir(file):
      print("Пропуск файла " + shlex.quote(file) + ": это папка", file=sys.stderr)
      completed.append(file)
      continue
    if not os.path.exists(file + HASH_SUFFIX):
      print("Ошибка: не найден файл " + shlex.quote(file + HASH_SUFFIX), file=sys.stderr)
      continue
    saved_hash = Format1.from_dict(ms.json.read(file + HASH_SUFFIX))
    if saved_hash.file_size != os.path.getsize(file):
      print("Ошибка: размер файла " + shlex.quote(file) + " не совпадает", file=sys.stderr)
      continue
    real_hash = Format1.generate(file, args.bar, hash_type=saved_hash.hash_type)
    if saved_hash.hash_hex == real_hash.hash_hex:
      print("Успех: файл " + shlex.quote(file) + " не изменён")
    else:
      print("Ошибка: файл " + shlex.quote(file) + " изменён")
    completed.append(file)
