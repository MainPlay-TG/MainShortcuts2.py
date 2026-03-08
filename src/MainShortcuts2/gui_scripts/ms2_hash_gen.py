from MainShortcuts2.ex.pathlib_ex import Path
from MainShortcuts2.gui_scripts.utils import *
from MainShortcuts2.ms2hash import *
argp = ArgumentParser()
argp.add_argument("files", nargs="*", help="пути к файлам")
argp.add_argument("-f", "--force", action="store_true", help="перезаписывать существующие хеши")
argp.add_argument("-t", "--type", choices=HASH_TYPES, default="sha512", help="тип контрольной суммы")


def prep_files(paths: list[str]) -> set[Path]:
  result = set()
  for str_path in paths:
    obj_path = Path(str_path)
    suffix = HASH_SUFFIX.lower()
    while obj_path.suffix.lower() == suffix:
      obj_path = obj_path.with_suffix("")
    if obj_path.is_file():
      result.add(obj_path)
  return result


class MainWindow(QMainWindow):
  def __init__(self, files: set[Path], force=False, hash_type="sha512"):
    super().__init__()
    self.files = files
    self.force = force
    self.hash_type = hash_type
    # Настройка окна


raise Exception("Модуль в разработке")


@main_func(__name__)
def main(args=None, *, qapp: QApplication):
  if args is None:
    args = argp.parse_args()
  files = prep_files(args.files)
  if not files:
    mw = QMessageBox()
    mw.setIcon(QMessageBox.Icon.Critical)
    mw.setText("Нет доступных файлов для обработки")
    mw.setWindowTitle("Ошибка")
    return mw.exec()
