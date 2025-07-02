import os
import sys
from . import _module_info
from .advanced import get_platform
from .cfg import cfg
from .utils import mini_log
from threading import Thread
from time import time
UPDATE_CHECK_INTERVAL = 21600  # 6 часов


class CoreConfig(cfg):
  def __init__(self):
    if getattr(sys, "frozen", False):
      return
    if os.environ.get("MS2_NO_CONFIG"):
      return
    plat = get_platform()
    cfg.__init__(self, plat.user_config_dir + "/MainPlay_TG/MainShortcuts2/cfg.json", type="json")
    self.default["check_updates"] = True
    self.default["check_updates#"] = "Set to 'false' to disable checking for updates"
    self.default["last_update_check"] = 0
    self.default["last_update_check#"] = "Don't change this"
    self.default["version"] = _module_info.version
    self.default["version#"] = "Don't change this"
    self.dload()
    if self["version"] != _module_info.version:
      self["version"] = _module_info.version
    self.check_updates()
    self.save_if_need(sort_keys=True)

  def check_updates(self):
    if not self["check_updates"]:
      return
    if os.environ.get("MS2_NO_UPDATE"):
      return
    now = time()
    if self["last_update_check"] + UPDATE_CHECK_INTERVAL > now:
      return
    self["last_update_check"] = now
    Thread(target=self._cu_thread).start()

  def _cu_thread(self):
    try:
      import requests
      url = "https://github.com/MainPlay-TG/MainShortcuts2.py/raw/refs/heads/master/src/MainShortcuts2/_module_info.py"
      with requests.get(url) as resp:
        resp.raise_for_status()
        version = self._parse_version(resp.text)
      if version != _module_info.version:
        mini_log("New MainShortcuts2 version available: %s", version)
        mini_log("Please update by running:")
        mini_log("%s -m pip install -U MainShortcuts2", sys.executable)
        mini_log("or disable updates in config")
        mini_log("File: %s", self.path)
    except:
      return

  def _parse_version(self, code) -> str:
    import ast
    tree = ast.parse(code)
    for node in ast.walk(tree):
      if isinstance(node, ast.Assign):
        for target in node.targets:
          if isinstance(target, ast.Name):
            if target.id == "version":
              return ast.literal_eval(node.value)
    return _module_info.version
