import sys
import shutil
from MainShortcuts2 import ms2app
PYTHON = ("python3" if shutil.which("python3") else "python") if getattr(sys, "frozen", False) else sys.executable
reg_interpreter(PYTHON, "py", "pyc", "pyw")
if sys.platform == "win32":
  reg_interpreter(PYTHON + "w", "pyw")
if os.environ.get("JAVA_HOME"):
  java_bin = os.environ["JAVA_HOME"] + "/bin/java"
  if sys.platform == "win32":
    java_bin += ".exe"
else:
  java_bin = "java"
reg_interpreter([java_bin, "-jar"], "jar")
reg_interpreter("bash", "sh", "bash")
