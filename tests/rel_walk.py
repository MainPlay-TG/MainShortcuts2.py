from MainShortcuts2 import ms
from MainShortcuts2.ex.pathlib_ex import Path
my_dir = Path(ms.MAIN_DIR)
txt_file = my_dir / "rel_walk.txt"
root = my_dir.parent
with txt_file.open("w", encoding="utf-8") as f:
  for wroot, wdirs, wfiles in root.walk_relative():
    if not wroot.startswith(".git"):
      f.write(f"{wroot} {wdirs} {wfiles}\n")
