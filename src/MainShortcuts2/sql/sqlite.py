import sqlite3
from ._sql_base import check_type, DatabaseBase, ObjectBase
from MainShortcuts2 import ms
__all__ = ["check_type", "Database", "ObjectBase"]


def _gws(where: dict, sep: str = " AND "):
  return sep.join(i + "=?" for i in where)


class Database(DatabaseBase):
  MEMORY = ":memory:"

  class Cursor(sqlite3.Cursor):
    def __enter__(self):
      return self

    def __exit__(self, *a):
      self.close()

  def __init__(self, path: str, **kw):
    if path == self.MEMORY:
      kw.setdefault("connect_on_init", False)
      kw["autosave"] = False
    else:
      ms.dir.create(ms.path.Path(path).parent_dir)
    kw.setdefault("check_same_thread", False)
    kw["database"] = path
    DatabaseBase.__init__(self, **kw)

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
    self.conn = sqlite3.connect(**self.conn_kw)

  def cursor(self):
    self.connect()
    return self.conn.cursor(self.Cursor)

  def delete(self, table: str, where: dict):
    """Удалить строки из таблицы"""
    self.exec(f"DELETE FROM {table} WHERE {_gws(where)};", where.values(), fetch=False)

  def insert(self, table: str, values: dict):
    """Вставить новую строку в таблицу"""
    self.exec(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join(['?'] * len(values))});", values.values(), fetch=False)

  def select(self, table: str, columns: list[str], where: dict) -> list[tuple]:
    """Выбрать строки из таблицы"""
    if isinstance(columns, str):
      columns = [columns]
    return self.exec(f"SELECT {','.join(columns)} FROM {table} WHERE {_gws(where)};", where.values(), fetch=True)

  def update(self, table: str, values: dict, where: dict):
    """Изменить строки в таблице"""
    self.exec(f"UPDATE {table} SET {_gws(values, ',')} WHERE {_gws(where)};", list(values.values()) + list(where.values()), fetch=False)

  def save(self):
    if self.connected:
      if self.conn_kw["database"] != self.MEMORY:
        self.conn.commit()
