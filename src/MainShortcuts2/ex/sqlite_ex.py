import sqlite3
# Внимание: возможны SQL-инъекции через названия таблиц и столбцов
# при использовании упрощённых методов (make_*_sql)
# Не указывайте названия из непроверенных источников (например, пользовательский ввод)
TYPE_BY_NAME = {
    "BLOB": bytes,
    "INTEGER": int,
    "NULL": type(None),
    "REAL": float,
    "TEXT": str,
}
NAME_BY_TYPE = {v: k for k, v in TYPE_BY_NAME.items()}


def make_where_string(where: dict, sep=" AND ", prep_null=True):
  params = []
  parts = []
  for k, v in where.items():
    if prep_null and v is None:
      parts.append(k + " IS NULL")
    else:
      params.append(v)
      parts.append(k + "=?")
  return sep.join(parts), params


def make_delete_sql(table: str, where: dict):
  text, params = make_where_string(where)
  return f"DELETE FROM {table} WHERE {text};", params


def make_insert_sql(table: str, values: dict, modifier=""):
  if not values:
    raise ValueError("Cannot insert empty dictionary")
  keys = ",".join(values)
  inserts = ",".join("?" * len(values))
  return f"INSERT {modifier}INTO {table} ({keys}) VALUES ({inserts});", list(values.values())


def make_select_sql(table: str, columns: list[str], where: dict):
  text, params = make_where_string(where)
  return f"SELECT {','.join(columns)} FROM {table} WHERE {text};", params


def make_update_sql(table: str, values: dict, where: dict):
  if not values:
    raise ValueError("No values to update")
  text1, params1 = make_where_string(values, ",", False)
  text2, params2 = make_where_string(where)
  return f"UPDATE {table} SET {text1} WHERE {text2};", params1 + params2


class Cursor(sqlite3.Cursor):
  def __enter__(self):
    return self

  def __exit__(self, *a):
    self.close()

  def execute2(self, sql: str, *params):
    """Удобно если кол-во параметров не меняется"""
    return self.execute(sql, params)
  # Быстрые операции

  def delete(self, table: str, where: dict):
    """Удалить строки из таблицы"""
    return self.execute(*make_delete_sql(table, where))

  def insert_or_ignore(self, table: str, values: dict):
    """Вставить или игнорировать"""
    return self.execute(*make_insert_sql(table, values, "OR IGNORE "))

  def insert_or_replace(self, table: str, values: dict):
    """Вставить или заменить"""
    return self.execute(*make_insert_sql(table, values, "OR REPLACE "))

  def insert(self, table: str, values: dict):
    """Вставить строку в таблицу"""
    return self.execute(*make_insert_sql(table, values))

  def select_fetchall(self, table: str, columns: list[str], where: dict):
    return self.select(table, columns, where).fetchall()

  def select_fetchone(self, table: str, columns: list[str], where: dict):
    return self.select(table, columns, where).fetchone()

  def select(self, table: str, columns: list[str], where: dict):
    """Выбрать строки из таблицы. Не выполняет `fetch`!"""
    return self.execute(*make_select_sql(table, columns, where))

  def update(self, table: str, values: dict, where: dict):
    """Изменить строки в таблице"""
    if not values:
      return self
    return self.execute(*make_update_sql(table, values, where))


class Connection(sqlite3.Connection):
  @classmethod
  def connect(cls, database, **kw):
    """Создать/открыть файл БД"""
    kw.setdefault("check_same_thread", False)
    return cls(database, **kw)

  @classmethod
  def create_in_memory(cls, **kw):
    """Создать БД без файла"""
    return cls.connect(":memory:", **kw)

  def cursor(self):
    return Cursor(self)

  def vacuum(self):
    """Уменьшить размер БД если возможно. Также делает коммит"""
    self.commit()
    with self.cursor() as cur:
      cur.execute("VACUUM;")
  # Методы от курсора

  def delete(self, table: str, where: dict):
    with self.cursor() as cur:
      cur.delete(table, where)

  def execute2(self, sql: str, *params):
    return self.execute(sql, params)

  def insert_or_ignore(self, table: str, values: dict):
    with self.cursor() as cur:
      cur.insert_or_ignore(table, values)

  def insert_or_replace(self, table: str, values: dict):
    with self.cursor() as cur:
      cur.insert_or_replace(table, values)

  def insert(self, table: str, values: dict):
    with self.cursor() as cur:
      cur.insert(table, values)

  def select_fetchall(self, table: str, columns: list[str], where: dict):
    with self.cursor() as cur:
      return cur.select_fetchall(table, columns, where)

  def select_fetchone(self, table: str, columns: list[str], where: dict):
    with self.cursor() as cur:
      return cur.select_fetchone(table, columns, where)

  def update(self, table: str, values: dict, where: dict):
    with self.cursor() as cur:
      cur.update(table, values, where)


connect = Connection.connect
create_in_memory = Connection.create_in_memory
