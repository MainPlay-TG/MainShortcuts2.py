import hashlib
import os
import shutil
import subprocess
import sys
from MainShortcuts2 import ms
from zipfile import ZipFile, ZipInfo
interpreters: dict[str, list[str]] = {}


def reg_interpreter(command: str | list[str], *extensions: str):
  if isinstance(command, str):
    command = [command]
  for ext in extensions:
    if not ext.startswith("."):
      ext = "." + ext
    interpreters[ext] = command


def get_command(file: str) -> list[str]:
  _, ext = os.path.splitext(file)
  return interpreters.get(ext, []) + [file]


def _get_cache_dir():
  if sys.platform == "win32":
    import winreg
    dir, type = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders"), "Local AppData")
    return ms.path.Path(dir + "/MainPlay TG/MainShortcuts2/ms2app_cache")
  if sys.platform == 'darwin':
    return ms.path.Path(os.path.expanduser("~/Library/Caches") + "/ms2app_cache")
  return ms.path.Path(os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache")) + "/ms2app_cache")


CACHE_DIR = _get_cache_dir()


class LaunchError(Exception):
  pass


class Metadata(ms.ObjectBase):
  FILENAME = "ms2app.json"
  FORMAT = 1
  KEYS = (
      "author",
      "custom",
      "description",
      "download_url",
      "executable",
      "license",
      "name",
      "update_url",
      "version_id",
      "version",
  )

  def __init__(self, author: str, name: str, *,
               custom: dict = None,
               description: str = None,
               download_url: str = None,
               executable: str = "__main__.py",
               license: str = None,
               update_url: str = None,
               version_id: int = -1,
               version: str = None,
               ):
    self.author: str = author
    """Автор приложения"""
    self.download_url: None | str = download_url
    """Ссылка для скачивания `.ms2app`. Обязательна при проверке обновлений"""
    self.custom: dict = {} if custom is None else custom
    """Пользовательские метаданные"""
    self.description: None | str = description
    """Описание приложения"""
    self.executable: str = executable
    """Название главного файла приложения"""
    self.license: None | str = license
    """Лицензия"""
    self.name: str = name
    """Название приложения"""
    self.update_url: None | str = update_url
    """Ссылка на JSON файл с информацией для скачивания/обновления"""
    self.version_id: int = version_id
    """ID версии, используется для проверки обновлений"""
    self.version: str = str(version_id) if version is None else version
    """Название версии"""
  @classmethod
  def from_dict(cls, data):
    return cls(**data)

  @classmethod
  def from_json(cls, text, **json_kw):
    return cls.from_dict(ms.json.decode(text, **json_kw))

  def to_dict(self) -> dict:
    data = {"format": self.FORMAT}
    for k in self.KEYS:
      data[k] = getattr(self, k, None)
    return data

  def to_json(self, **kw) -> str:
    return ms.json.encode(self.to_dict(), **kw)

  def to_jsonb(self, **kw) -> bytes:
    return self.to_json(**kw).encode(ms.encoding)

  def check_updates(self) -> None | str:
    """Проверить наличие обновлений. Возвращает `None` или ссылку на скачивание `.ms2app`"""
    if not self.update_url:
      return
    try:
      with ms.utils.request("GET", self.update_url) as resp:
        data: dict = resp.json()
        if self.name != data["name"]:
          print("Warning: The name of the new version of the program is different (%s -> %s)" % (self.name, data["name"]), file=sys.stderr)
        if self.version_id > data["version_id"]:
          return data.get("download_url")
    except Exception as exc:
      print("Check for updates error: %r" % exc, file=sys.stderr)


class App(ms.ObjectBase):
  def __init__(self, file: str, password: bytes = None):
    self._platform = None
    self._sha256 = None
    self.file = ms.path.Path(file)
    self.password = password.encode("utf-8") if isinstance(password, str) else password
    with self.open_zip("r") as zip:
      self.meta = Metadata.from_json(zip.read(Metadata.FILENAME))

  def _get_platform(self) -> str:
    if self._platform is None:
      with self.open_zip() as zip:
        namelist = zip.namelist()
      if "app-%s/%s" % (sys.platform, self.meta.executable) in namelist:
        self._platform = sys.platform
      elif "app-any/%s" % self.meta.executable in namelist:
        self._platform = "any"
      else:
        raise LaunchError("This app is not supported on your system (%s)" % sys.platform)
    return self._platform

  @property
  def sha256(self) -> str:
    if self._sha256 is None:
      with open(self.file, "rb") as f:
        hash = hashlib.sha256()
        for i in f:
          hash.update(i)
      self._sha256 = hash.hexdigest()
    return self._sha256

  def open_zip(self, mode: str = "r", **kw) -> ZipFile:
    kw["mode"] = mode
    zip = ZipFile(self.file.path, **kw)
    if self.password:
      zip.setpassword(self.password)
    else:
      if zip.comment.lower().startswith(b"password: "):
        zip.setpassword(zip.comment[10:zip.comment.index(b"\n")])
    return zip

  def _extract_file(self, zip: ZipFile, src: ZipInfo, dest, created_dirs):
    if not isinstance(src, ZipInfo):
      src = zip.getinfo(src)
    if not isinstance(dest, ms.path.Path):
      dest = ms.path.Path(dest)
    if src.is_dir():
      return
    if dest.exists:
      return
    if not dest.parent_dir in created_dirs:
      if not os.path.exists(dest.parent_dir):
        os.makedirs(dest.parent_dir)
      created_dirs.add(dest.parent_dir)
    with zip.open(src, "r") as source:
      with open(dest, "wb") as target:
        shutil.copyfileobj(source, target)

  def _check_prefix(self, filename: str):
    for prefix in ("app-%s/" % self._get_platform(), "assets/", "icon.", "libs/"):
      if filename.startswith(prefix):
        return True
    return False

  def unpack(self, extract_dir: str = None):
    """Распаковать архив в папку кеша"""
    created_dirs = set()
    if extract_dir is None:
      extract_dir = CACHE_DIR + "/app-" + self.sha256 + "/"
    elif not extract_dir.endswith("/"):
      extract_dir += "/"
    with self.open_zip() as zip:
      for file in zip.filelist:
        if self._check_prefix(file.filename):
          dest = ms.path.Path(extract_dir + file.filename)
          self._extract_file(zip, file, dest, created_dirs)
      self._extract_file(zip, Metadata.FILENAME, extract_dir + Metadata.FILENAME, created_dirs)

  def start(self, args: list[str] = None, **kw):
    """запустить приложение"""
    from . import _ms2app_regs
    app_dir = CACHE_DIR + "/app-" + self.sha256 + "/app-" + self._get_platform()
    app_exe = app_dir + "/" + self.meta.executable
    kw.setdefault("env", os.environ.copy())
    kw["args"] = get_command(app_exe)
    kw["env"]["MS2APP_APP_DIR"] = app_dir
    kw["env"]["MS2APP_APP_EXE"] = app_exe
    kw["env"]["MS2APP_ZIP_FILE"] = self.file.path
    if args:
      kw["args"] += args
    return subprocess.Popen(**kw)

  def start_call(self, args: list[str] = None, timeout: float = None, **kw):
    """Запустить приложение и ожидать завершения"""
    with self.start(args, **kw) as p:
      try:
        return p.wait(timeout=timeout)
      except:
        p.kill()
        raise


@ms.utils.main_func(__name__)
def main(args=None, **kw):
  if args is None:
    from argparse import ArgumentParser
    argp = ArgumentParser("ms2-app", description="Управление приложениями ms2app")
    subp = argp.add_subparsers(dest="command", required=True)
    # download
    subp_download = subp.add_parser("download", help="скачать приложение")
    subp_download.add_argument("-O", "--output", help="путь сохранения")
    subp_download.add_argument("url", help="ссылка для скачивания")
    # run
    subp_run = subp.add_parser("run", help="запустить приложение")
    subp_run.add_argument("--password", help="пароль от файла")
    subp_run.add_argument("-b", "--no-wait", action="store_true", help="запустить приложение в фоне")
    subp_run.add_argument("args", nargs="+", help="путь к файлу ms2app или zip и аргументы запуска")
    # show
    subp_show = subp.add_parser("show", help="показать информацию о приложении")
    subp_show.add_argument("--no-check-updates", action="store_true", help="не проверять наличие обновлений")
    subp_show.add_argument("--password", help="пароль от файла")
    subp_show.add_argument("file", help="путь к файлу ms2app или zip")
    # upgrade
    subp_upgrade = subp.add_parser("upgrade", help="обновить приложение")
    subp_upgrade.add_argument("--password", help="пароль от файла")
    subp_upgrade.add_argument("-O", "--output", help="путь сохранения")
    subp_upgrade.add_argument("file", help="путь к файлу ms2app или zip")
    args = argp.parse_args()
  if args.command == "download":
    kw.setdefault("url", args.url)
    if args.output:
      kw.setdefault("path", args.output)
    else:
      from urllib.parse import ParseResult, urlparse
      parsed_url: ParseResult = urlparse(args.url)
      kw.setdefault("path", parsed_url.path.split("/")[-1])
    ms.utils.download_file(**kw)
    return
  if args.command == "run":
    app = App(args.args.pop(0), args.password)
    if args.no_wait:
      return app.start(args.args)
    return app.start_call(args.args)
  if args.command == "show":
    app = App(args.file, args.password)
    data = app.meta.to_dict()
    data["file"] = app.file.path
    for k in list(data):
      v = data[k]
      if isinstance(v, bool):
        data[k] = "да" if v else "нет"
      elif not v:
        data[k] = "(отсутствует)"
    print("Приложение %(name)s от %(author)s" % data)
    print("Версия: %(version)s (%(version_id)s)" % data)
    print("Описание: %(description)s" % data)
    print("Файл: %(file)s" % data)
    print("Лицензия: %(license)s" % data)
    if not args.no_check_updates:
      data["update"] = app.meta.check_updates()
      if data["update"]:
        print("Доступно обновление! Можете скачать его командой\nms2-app upgrade %(file)s\nИли по ссылке %(update)s" % data)
    return
  if args.command == "upgrade":
    app = App(args.file, args.password)
    kw.setdefault("url", app.meta.check_updates())
    if not kw["url"]:
      return print("Нет доступных обновлений")
    if args.output:
      kw.setdefault("path", args.output)
    else:
      kw.setdefault("path", app.file)
    print("Скачивание обновления...")
    ms.utils.download_file(**kw)
    print("Обновление завершено")
    return
