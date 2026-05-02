from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
my_dir = Path(ms.MAIN_DIR)
txt_file = my_dir / "rel_list.txt"
root = my_dir.parent
with txt_file.open("w", encoding="utf-8") as f:
  for i in root.list_relative(True):
    if not i.startswith(".git"):
      f.write(f"{i}\n")
