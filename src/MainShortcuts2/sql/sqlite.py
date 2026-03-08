from ._sql_base import *
from MainShortcuts2 import ms
from MainShortcuts2.ex import sqlite_ex
from typing import TYPE_CHECKING
__all__ = ["check_type", "Database", "ObjectBase"]


def _gws(where: dict, sep: str = " AND "):
  return sep.join(i + "=?" for i in where)


class Database(DatabaseBase):
  """SQLite3"""
  MEMORY = ":memory:"

  def __init__(self, path: str, **kw):
    if path == self.MEMORY:
      kw.setdefault("connect_on_init", False)
      kw["autosave"] = False
    else:
      ms.dir.create(ms.path.Path(path).parent_dir)
    kw["database"] = path
    DatabaseBase.__init__(self, **kw)
  if TYPE_CHECKING:
    def cursor(self) -> sqlite_ex.Cursor:
      return super().cursor()

  @classmethod
  def create_in_memory(cls, **kw):
    """Создать базу данных в оперативной памяти"""
    kw["path"] = cls.MEMORY
    return cls(**kw)

  def _update_schema(self, schema):
    with self.cursor() as cur:
      for table in schema:
        columns_str = ",".join(k + " " + v for k, v in schema[table].items())
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns_str});")
        cur.execute(f"PRAGMA table_info({table});")
        exist_cols = [i[1] for i in cur.fetchall()]
        for col_name, col_type in schema[table].items():
          if not col_name in exist_cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type};")
    self.save()

  def _connect(self):
    self.conn = sqlite_ex.connect(**self.conn_kw)

  def delete(self, table: str, where: dict):
    """Удалить строки из таблицы"""
    if isinstance(table, ObjectBase):
      table = table._table
    self.exec(*sqlite_ex.make_delete_sql(table, where), fetch=False)

  def insert(self, table: str, values: dict):
    """Вставить новую строку в таблицу"""
    if isinstance(table, ObjectBase):
      table = table._table
    self.exec(*sqlite_ex.make_insert_sql(table, values), fetch=False)

  def select(self, table: str, columns: str | list[str], where: dict) -> list[tuple]:
    """Выбрать строки из таблицы"""
    if isinstance(table, ObjectBase):
      table = table._table
    if not isinstance(columns, str):
      columns = ",".join(columns)
    if where:
      return self.exec(*sqlite_ex.make_select_sql(table, columns, where), fetch=True)
    return self.exec(f"SELECT {columns} FROM {table};", fetch=True)

  def update(self, table: str, values: dict, where: dict):
    """Изменить строки в таблице"""
    if isinstance(table, ObjectBase):
      table = table._table
    self.exec(*sqlite_ex.make_update_sql(table, values, where), fetch=False)

  def save(self):
    if self.connected:
      if self.conn_kw["database"] != self.MEMORY:
        self.conn.commit()

  def select_adv(self, table: str, columns: str | list[str], where: dict = None, order_by: str = None, limit: int = None, offset: int = None, other: str = None):
    if isinstance(table, ObjectBase):
      table = table._table
    if not isinstance(columns, str):
      columns = ",".join(columns)
    code = f"SELECT {columns} FROM {table}"
    if where:
      if isinstance(where, str):
        code += f" WHERE {where}"
      else:
        code += f" WHERE {_gws(where)}"
    if order_by:
      code += f" ORDER BY {order_by}"
    if limit:
      code += f" LIMIT {limit}"
    if offset:
      code += f" OFFSET {offset}"
    if other:
      code += f" {other}"
    if where:
      return self.exec(code, where.values(), fetch=True)
    return self.exec(code, fetch=True)
