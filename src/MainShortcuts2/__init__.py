"""Упрощение и сокращение вашего кода благодаря этой библиотеке
Разработчик: MainPlay TG
https://t.me/MainPlayCh"""
__all__ = ["ms", "NoLogger"]
__scripts__ = []
from ._module_info import version as __version__
# 2.0.0
from .core import ms, NoLogger
try:
  from .core_config import CoreConfig
  ms.config = CoreConfig()
except Exception:
  ms.config = None
