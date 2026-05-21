from ._sql_base import *
from MainShortcuts2.ex import sqlite_ex
from MainShortcuts2.ex.pathlib_ex import Path
from sqlite3 import sqlite_version_info
from typing import TYPE_CHECKING
STRICT_SUPPORT = sqlite_version_info >= (3, 37, 0)
# bool -> INTEGER (0/1)
# bytes -> BLOB
# float -> REAL (8 байт)
# int -> INTEGER (±9.2e18)
# str -> TEXT


def _gws(where: dict, sep: str = " AND "):
  return sep.join(i + "=?" for i in where)


Cursor = sqlite_ex.Cursor


class Database(SyncDatabaseBase):
  """SQLite3"""
  MEMORY = ":memory:"

  def __init__(self, path: str, strict_schema=False, **kw):
    if path == self.MEMORY:
      kw.setdefault("connect_on_init", False)
      kw["autosave"] = False
      self.db_path = None
    else:
      self.db_path.parent.any_mkdir()
      self.db_path = Path(path)
    DatabaseBase.__init__(self, **kw)
    self.strict_schema = strict_schema
  if TYPE_CHECKING:
    def cursor(self) -> Cursor:
      return super().cursor()

  @classmethod
  def create_in_memory(cls, **kw):
    """Создать базу данных в оперативной памяти"""
    kw["path"] = cls.MEMORY
    return cls(**kw)

  def export_db(self):
    """Экспортировать БД в байты"""
    self.connect()
    return self.conn.serialize()

  def import_db(self, data: bytes):
    """Импортировать БД из байтов"""
    self.connect()
    self.conn.deserialize(data)

  def save(self, vacuum=False):
    if self.connected and self.db_path:
      if vacuum:
        self.conn.vacuum()  # Сам делает коммит
      else:
        self.conn.commit()
  # Обязательные методы

  def _connect(self):
    db = self.MEMORY if self.db_path is None else str(self.db_path)
    self.conn = sqlite_ex.connect(db, **self.conn_kw)

  def _create_table(self, cur: Cursor, table: str, columns: dict):
    suffix = " STRICT" if (STRICT_SUPPORT and self.strict_schema) else ""
    cstr = ",".join(f"{k} {v}" for k, v in columns.items())
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cstr}){suffix};")
    cur.execute(f"PRAGMA table_info({table});")
    exist_cols = {i[1] for i in cur.fetchall()}
    for cname, ctype in columns.items():
      if cname not in exist_cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {cname} {ctype};")

  def _delete(self, table: str, where: dict):
    self.exec(*sqlite_ex.make_delete_sql(table, where), fetch=False)

  def _insert(self, table: str, values: dict):
    self.exec(*sqlite_ex.make_insert_sql(table, values), fetch=False)

  def _select_adv(self, table: str, columns: str | list[str], where: dict,
                  order_by: str, limit: int, offset: int, other: str):
    if not isinstance(columns, str):
      columns = ",".join(columns)
    params = []
    parts = [f"SELECT {columns} FROM {table}"]
    if where:
      if isinstance(where, str):
        parts.append(f"WHERE {where}")
      else:
        params.extend(where.values())
        parts.append(f"WHERE {_gws(where)}")
    if order_by:
      parts.append(f"ORDER BY {order_by}")
    if limit:
      parts.append(f"LIMIT {limit}")
    if offset:
      parts.append(f"OFFSET {offset}")
    if other:
      parts.append(other)
    return self.exec(" ".join(parts), params, fetch=True)

  def _select(self, table: str, columns: str | list[str], where: dict):
    if not isinstance(columns, str):
      columns = ",".join(columns)
    if where:
      return self.exec(*sqlite_ex.make_select_sql(table, columns, where), fetch=True)
    return self.exec(f"SELECT {columns} FROM {table};", fetch=True)

  def _update(self, table: str, values: dict, where: dict):
    self.exec(*sqlite_ex.make_update_sql(table, values, where), fetch=False)
