import subprocess
import typing
from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
ROOT_DIR = Path(ms.MAIN_DIR)
JSON_DIR = (ROOT_DIR / "json").any_mkdir()


class Version(typing.TypedDict):
  added: list[str]
  changed: list[str]
  fixed: list[str]
  removed: list[str]
  version_id: int
  version: str


@ms.utils.main_func(__name__)
def main():
  versions: list[Version] = []
  for file in JSON_DIR.iterdir():
    if file.suffix == ".json" and file.is_file():
      versions.append(Version(file.read_json()))
  latest = max(versions, key=lambda i: i["version_id"])
  print("Предыдущая версия: {version} ({version_id})".format(**latest))
  new_data = {"added": [], "changed": [], "fixed": [], "removed": []}
  new_data["version_id"] = latest["version_id"] + 1
  new_data["version"] = input("Название новой версии: ").strip()
  new_file = ROOT_DIR / "{version}.json".format(**new_data)
  print("Запись версии {version} ({version_id})".format(**new_data))
  new_file.write_json(new_data, mode="p")
  subprocess.run(["code", str(new_file)])
