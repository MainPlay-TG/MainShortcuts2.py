import psycopg2
from ._sql_base import *
from typing import TYPE_CHECKING
# bool -> BOOL
# bytes -> BYTEA
# float -> FLOAT (4 байта), FLOAT8 (8 байт)
# int -> SMALLINT (±32767), INT (±2.1e9), BIGINT (±9.2e18)
# str -> TEXT


def _gws(where: dict, sep: str = " AND "):
  return sep.join(i + "=%s" for i in where)


Cursor = psycopg2.extensions.cursor


class Database(DatabaseBase):
  """PostgreSQL"""
  class TRIGGERS:
    @staticmethod
    def generate_uuid(db: "Database", table: str, column: str = "uuid"):
      FUNC_NAME = "mpl_2b10ae7c6b3f"
      with db.conn.cursor() as cur:
        cur.execute("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} TEXT;".format(table, column))
        cur.execute((
            "CREATE OR REPLACE FUNCTION {}() RETURNS trigger\n" +
            "  LANGUAGE plpgsql\n" +
            "  AS $$\n" +
            "BEGIN\n" +
            "  IF (NEW.{} IS NULL) THEN\n" +
            "    NEW.uuid = (SELECT uuid_generate_v4());\n" +
            "  END IF;\n" +
            "  RETURN NEW;\n" +
            "END;\n" +
            "$$;"
        ).format(FUNC_NAME, column, column))
        cur.execute("CREATE OR REPLACE TRIGGER {}_{} BEFORE INSERT ON {} FOR EACH ROW EXECUTE FUNCTION {}();".format(FUNC_NAME, table, table, FUNC_NAME))

    @staticmethod
    def created_at_and_edited_at(db: "Database", table: str, columns: tuple[str, str] = ("created_at", "edited_at")):
      assert len(columns) == 2 and isinstance(columns[0], str) and isinstance(columns[1], str)
      FUNC1_NAME = "mpl_25abf49da36b"
      FUNC2_NAME = "mpl_d6271c88b3a2"
      with db.cursor() as cur:
        cur.execute("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} TIMESTAMP;".format(table, columns[0]))
        cur.execute("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} TIMESTAMP;".format(table, columns[1]))
        cur.execute((
            "CREATE OR REPLACE FUNCTION {}() RETURNS trigger\n" +
            "  LANGUAGE plpgsql\n" +
            "  AS $$\n" +
            "BEGIN\n" +
            "  NEW.{} := NOW();\n" +
            "  NEW.{} := NOW();\n" +
            "  RETURN NEW;\n" +
            "END;\n" +
            "$$;"
        ).format(FUNC1_NAME, *columns))
        cur.execute((
            "CREATE OR REPLACE FUNCTION {}() RETURNS trigger\n" +
            "  LANGUAGE plpgsql\n" +
            "  AS $$\n" +
            "BEGIN\n" +
            "  NEW.{} := NOW();\n" +
            "  RETURN NEW;\n" +
            "END;\n" +
            "$$;"
        ).format(FUNC2_NAME, columns[1]))
        cur.execute("CREATE OR REPLACE TRIGGER {}_{} BEFORE INSERT ON {} FOR EACH ROW EXECUTE FUNCTION {}();".format(FUNC1_NAME, table, table, FUNC1_NAME))
        cur.execute("CREATE OR REPLACE TRIGGER {}_{} BEFORE UPDATE ON {} FOR EACH ROW EXECUTE FUNCTION {}();".format(FUNC2_NAME, table, table, FUNC2_NAME))

  def __init__(self, user: str, password: str, *,
               host: str = "127.0.0.1", port: int = 5432,
               name: str = None, **kw):
    kw["database"] = name or user
    kw["host"] = host
    kw["password"] = password
    kw["port"] = port
    kw["user"] = user
    DatabaseBase.__init__(self, **kw)
    self.ConnectionError = psycopg2.OperationalError, ConnectionError

  @classmethod
  def db_local(cls, user: str, password: str, name: str = None, **kw):
    """Подключение к локальной БД по порту"""
    return cls(user, password, name=name, **kw)

  @classmethod
  def db_unix(cls, name: str = None, **kw):
    """Подключение к БД по Unix-сокету"""
    return cls(None, None, host=None, port=None, name=name, **kw)
  if TYPE_CHECKING:
    def cursor(self) -> Cursor:
      return super().cursor()
  # Обязательные методы

  def _connect(self):
    self.conn: psycopg2.extensions.connection = psycopg2.connect(**self.conn_kw)

  def _create_table(self, cur: Cursor, table: str, columns: dict[str, str]):
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ();")
    for cname, ctype in columns.items():
      cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {cname} {ctype};")

  def _delete(self, table: str, where: dict):
    self.exec(f"DELETE FROM {table} WHERE {_gws(where)};", where.values(), fetch=False)

  def _insert(self, table: str, values: dict):
    cols = ",".join(values)
    placeholders = ",".join(["%s"] * len(values))
    self.exec(f"INSERT INTO {table} ({cols}) VALUES ({placeholders});", values.values(), fetch=False)

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
      return self.exec(f"SELECT {columns} FROM {table} WHERE {_gws(where)};", where.values(), fetch=True)
    return self.exec(f"SELECT {columns} FROM {table};", fetch=True)

  def _update(self, table: str, values: dict, where: dict):
    self.exec(f"UPDATE {table} SET {_gws(values, ',')} WHERE {_gws(where)};", list(values.values()) + list(where.values()), fetch=False)
  # Оптимизированные методы

  def select_count(self, table: TABLE_NAME, where: dict = None) -> int:
    return self.select(table, "COUNT(*)", where)[0][0]

  def select_random(self, table: TABLE_NAME, columns: list[str], where: dict = None, **kw):
    kw.setdefault("limit", 1)
    kw["order_by"] = "RANDOM()"
    return self.select_adv(table, columns, where, **kw)
