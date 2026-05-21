import pymysql
from ._sql_base import *
from typing import TYPE_CHECKING
# bool -> TINYINT(1)
# bytes -> BLOB | https://dev.mysql.com/doc/refman/9.7/en/blob.html
# float -> FLOAT (4 байта), DOUBLE (8 байт) | https://dev.mysql.com/doc/refman/9.7/en/floating-point-types.html
# int -> TINYINT (±127), SMALLINT (±32767), MEDIUMINT (±8.3e6), INT (±2.1e9), BIGINT (±9.2e18) | https://dev.mysql.com/doc/refman/9.7/en/integer-types.html
# str -> TEXT | https://dev.mysql.com/doc/refman/9.7/en/blob.html


def _gws(where: dict, sep: str = " AND "):
  return sep.join(f"{k}=%s" for k in where)


Cursor = pymysql.cursors.Cursor


class Database(DatabaseBase):
  """MariaDB/MySQL"""

  def __init__(self, user: str, password: str, *,
               host: str = "127.0.0.1", port: int = 3306,
               name: str = None, **kw):
    kw.setdefault("autocommit", False)
    kw.setdefault("charset", "utf8mb4")
    kw["database"] = name or user
    kw["host"] = host
    kw["password"] = password
    kw["port"] = port
    kw["user"] = user
    DatabaseBase.__init__(self, **kw)
    self.ConnectionError = (pymysql.err.OperationalError, ConnectionError)

  @classmethod
  def db_local(cls, user: str, password: str, database: str = None, **kw):
    """Подключение к локальной БД по TCP"""
    kw.setdefault("ssl_disabled", True)
    return cls(user, password, database=database, **kw)
  if TYPE_CHECKING:
    def cursor(self) -> Cursor:
      return super().cursor()
  # Обязательные методы

  def _connect(self):
    self.conn = pymysql.connect(**self.conn_kw)

  def _create_table(self, cur: Cursor, table: str, columns: dict):
    cstr = ",".join(f"{k} {v}" for k, v in columns.items())
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cstr});")
    cur.execute(f"DESCRIBE {table};")
    exist_cols = {row[0] for row in cur.fetchall()}
    for cname, ctype in columns.items():
      if cname not in exist_cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {cname} {ctype};")

  def _delete(self, table: str, where: dict):
    self.exec(f"DELETE FROM {table} WHERE {_gws(where)}", list(where.values()), fetch=False)

  def _insert(self, table: str, values: dict):
    cols = ",".join(values)
    placeholders = ",".join(["%s"] * len(values))
    self.exec(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(values.values()), fetch=False)

  def _select_adv(self, table: str, columns: str | list[str], where: dict,
                  order_by: str, limit: int, offset: int, other: str):
    if isinstance(columns, list):
      columns = ", ".join(columns)
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
    if limit is not None:
      parts.append(f"LIMIT {int(limit)}")
      if offset is not None:
        parts.append(f"OFFSET {int(offset)}")
    if other:
      parts.append(other)
    return self.exec(" ".join(parts), params, fetch=True)

  def _select(self, table: str, columns: str | list[str], where: dict):
    if not isinstance(columns, str):
      columns = ",".join(columns)
    if where:
      return self.exec(f"SELECT {columns} FROM {table} WHERE {_gws(where)};", where.values(), fetch=True)
    return self.exec(f"SELECT {columns} FROM {table};", fetch=True)

  def _update(self, table: str, values: dict, where: dict):
    params = list(values.values()) + list(where.values())
    set_clause = _gws(values, ", ")
    where_clause = _gws(where, " AND ")
    self.exec(f"UPDATE {table} SET {set_clause} WHERE {where_clause}", params, fetch=False)
  # Оптимизированные методы

  def select_count(self, table: str, where: dict = None) -> int:
    return self.select(table, "COUNT(*)", where)[0][0]

  def select_random(self, table: str, columns: list[str], where: dict = None, **kw):
    kw.setdefault("limit", 1)
    kw["order_by"] = "RAND()"
    return self.select_adv(table, columns, where, **kw)
