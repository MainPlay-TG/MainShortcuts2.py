import hashlib
import shutil
from pathlib import Path


class HashAsIO:
  def __init__(self, hash: "hashlib._Hash"):
    self.hash = hash
    self.write = hash.update

  @classmethod
  def new(cls, alg, data=b""):
    return cls(hashlib.new(alg, data))

  @classmethod
  def from_file(cls, alg, file: bytes | Path):
    if isinstance(file, bytes):
      return cls.new(alg, file)
    with file.open("rb") as f:
      self = cls.new(alg)
      shutil.copyfileobj(f, self)
    return self


def create_hash(alg: str, files: dict[str, bytes | Path]):
  lines: list[str] = []
  for name in sorted(files):
    hash = HashAsIO.from_file(alg, files[name]).hash
    lines.append(f"{hash.hexdigest()}  {name}")
  lines.append("")
  return "\n".join(lines)
