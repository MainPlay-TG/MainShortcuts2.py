import psutil
import signal
import subprocess
from datetime import timedelta


class Process(psutil.Process):
  def iter_tree(self, include_root=True):
    """Итератор дерева процессов"""
    if include_root:
      yield self
    for p in self.children(True):
      yield p

  def send_signal_tree(self, signal, include_root=True):
    """Отправить сигнал дереву процессов"""
    for p in self.iter_tree(include_root):
      try:
        p.send_signal(signal)
      except psutil.NoSuchProcess:
        pass

  def interrupt_tree(self, include_root=True):
    """Отправить SIGINT дереву процессов"""
    self.send_signal_tree(signal.SIGINT, include_root)

  def kill_tree(self, include_root=True):
    """Убить дерево процессов"""
    for p in self.iter_tree(include_root):
      try:
        p.kill()
      except psutil.NoSuchProcess:
        pass

  def terminate_tree(self, include_root=True):
    """Завершить дерево процессов"""
    for p in self.iter_tree(include_root):
      try:
        p.terminate()
      except psutil.NoSuchProcess:
        pass

  def start_same(self, func=subprocess.Popen, **kw):
    """Запустить такой же процесс"""
    kw.setdefault("args", self.cmdline())
    kw.setdefault("cwd", self.cwd())
    kw.setdefault("env", self.environ())
    if psutil.POSIX:
      kw.setdefault("user", self.username())
    return func(**kw)

  def restart(self, stop_signal=signal.SIGTERM, wait_for_exit: bool | float = True, **kw):
    """Остановить процесс и запустить такой же"""
    self.send_signal(stop_signal)
    if wait_for_exit:
      if isinstance(wait_for_exit, timedelta):
        wait_for_exit = wait_for_exit.total_seconds()
      if isinstance(wait_for_exit, (float, int)):
        # Если число, указать время ожидания
        self.wait(wait_for_exit)
      else:
        # Если True, то ждать без ограничения
        self.wait()
    return self.start_same(**kw)
