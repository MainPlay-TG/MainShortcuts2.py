import os
import re
import shutil
import subprocess
from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
JAVA_VERSION_PATTERN = re.compile(r'version\s+"([^"]+)"')


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


_java_version_cache: dict[str, list[int]] = {}


def _detect_java_version(file: Path):
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


def detect_java_version(file: Path):
  file = file.resolve()
  version = _java_version_cache.get(os.fspath(file))
  if not version:
    version = _java_version_cache[os.fspath(file)] = _detect_java_version(file)
  return version


class IncompatibleJava(Exception):
  pass
