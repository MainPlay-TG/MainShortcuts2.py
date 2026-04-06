import os
import sys
from . import _module_info
from .advanced import get_platform
from .cfg import cfg
from .utils import mini_log
from threading import Thread
from time import time
UPDATE_CHECK_INTERVAL = 86400  # 24 часа


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
      self.save()
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
      version = self._get_github_version()
      if version != _module_info.version:
        mini_log("New MainShortcuts2 version available: %s", version)
        mini_log("Please update by running:")
        mini_log("%s -m pip install -U MainShortcuts2", sys.executable)
        mini_log("or disable updates in config")
        mini_log("File: %s", self.path)
    except:
      return

  def _get_github_version(self) -> str:
    from MainShortcuts2.api.github import Client
    gh = Client.from_env(True)
    rel = gh.releases.get_latest("MainPlay-TG", "MainShortcuts2.py")
    for asset in rel.assets:
      if asset.name == "changelog.json":
        with gh.http.get(asset.browser_download_url) as resp:
          return resp.json()["version"]
    return _module_info.version
