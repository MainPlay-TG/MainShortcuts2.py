import json
import json5
from pathlib import Path
locale = {"added": "Добавлено", "changed": "Изменено", "fixed": "Исправлено", "removed": "Удалено"}


class Changelog(dict):
  def __init__(self, data):
    super().__init__(data)
    self.file: Path | None = None
    self.setdefault("added", [])
    self.setdefault("changed", [])
    self.setdefault("fixed", [])
    self.setdefault("removed", [])
    self.added.sort()
    self.changed.sort()
    self.fixed.sort()
    self.removed.sort()
    for i in ("version_id", "version"):
      if not i in self:
        raise KeyError(i)

  @property
  def added(self) -> list[str]:
    return self["added"]

  @property
  def changed(self) -> list[str]:
    return self["changed"]

  @property
  def fixed(self) -> list[str]:
    return self["fixed"]

  @property
  def removed(self) -> list[str]:
    return self["removed"]

  @property
  def version(self) -> str:
    return self["version"]

  @property
  def version_id(self) -> int:
    return self["version_id"]

  def to_md(self, name: str):
    lines = [f"# {name}"]
    lines.append(f"Версия: {self.version} ({self.version_id})")
    for key, name in locale.items():
      if self[key]:
        lines.append(f"## {name}:")
        for item in self[key]:
          lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)

  def to_summary_md(self):
    lines = [f"## {self.version} ({self.version_id})"]
    for key, name in locale.items():
      if self[key]:
        lines.append(f"### {name}:")
        for item in self[key]:
          lines.append(f"- {item}")
    return lines


def read_json(path: Path):
  with path.open("r", encoding="utf-8") as f:
    return json5.load(f)


def dump_json(data, **kw):
  kw.setdefault("separators", (",", ":"))
  return json.dumps(data, **kw)


def write_json(path: Path, data, **kw):
  temp_path = path.with_suffix(path.suffix + ".tmp")
  new_text = dump_json(data, **kw)
  if path.is_file():
    old_text = path.read_text("utf-8")
    if new_text == old_text:
      return
  try:
    temp_path.write_text(new_text, "utf-8", newline="\n")
    temp_path.replace(path)
  except Exception:
    temp_path.unlink(missing_ok=True)


def read_changelog(path: Path):
  chlog = Changelog(read_json(path))
  chlog.file = path
  return chlog


def write_changelog(path: Path, chlog: Changelog, **kw):
  write_json(path, dict(chlog), **kw)


def prepare_changelog(dir: Path, name: str):
  result: dict[str, Changelog] = {}
  for file in dir.iterdir():
    if (file.suffix.lower() == ".json") and file.is_file():
      chlog = read_changelog(file)
      result[chlog.version] = chlog
      write_changelog(file, chlog)
      md_file = file.with_suffix(".md")
      if not md_file.exists():
        md_file.write_text(chlog.to_md(name), "utf-8", newline="\n")
  summary = [f"# {name}"]
  for chlog in sorted(result.values(), key=lambda i: i.version_id, reverse=True):
    summary.extend(chlog.to_summary_md())
  summary.append("")
  (dir / "README.md").write_text("\n".join(summary), "utf-8", newline="\n")
  return result
