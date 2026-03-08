import autopep8
from pathlib import Path
OPTIONS = {
    "ignore": {"E402", "E501"},
    "in_place": True,
    "indent_size": 2,
    "max_line_length": 12000,
}


def format_code(dir: Path, **kw):
  kw["options"] = autopep8._get_options(OPTIONS, False)
  kw["options"].ignore = [opt.upper() for opt in kw["options"].ignore]
  kw["options"].select = [opt.upper() for opt in kw["options"].select]
  ignore_opt = kw["options"].ignore
  if not {"W50", "W503", "W504"} & set(ignore_opt):
    kw["options"].ignore.append("W50")
  files: set[str] = set()
  for root, dirnames, filenames in (dir / "src").walk():
    for file in [root / i for i in filenames]:
      if file.suffix == ".py":
        files.add(str(file))
  autopep8.fix_multiple_files(list(files), **kw)
