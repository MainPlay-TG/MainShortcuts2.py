import psycopg2
from ._sql_base import check_type, DatabaseBase, ObjectBase
__all__ = ["check_type", "Database", "ObjectBase"]


def _gws(where: dict, sep: str = " AND "):
  return sep.join(i + "=%s" for i in where)


class Database(DatabaseBase):
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
      with db.conn.cursor() as cur:
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

  def __init__(self, *, host: str = "127.0.0.1", name: str = None, password: str, port: int = 5432, user: str, **kw):
    kw["database"] = user if name is None else name
    kw["host"] = host
    kw["password"] = password
    kw["port"] = port
    kw["user"] = user
    DatabaseBase.__init__(self, **kw)
    self.ConnectionError = psycopg2.OperationalError, ConnectionError

  def _update_schema(self, schema):
    with self.cursor() as cur:
      for table, columns in schema.items():
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ();")
        for name, type in columns.items():
          cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {type};")

  def _connect(self):
    self.conn: psycopg2.extensions.connection = psycopg2.connect(**self.conn_kw)

  def delete(self, table: str, where: dict):
    """Удалить строки из таблицы"""
    self.exec(f"DELETE FROM {table} WHERE {_gws(where)};", where.values(), fetch=False)

  def insert(self, table: str, values: dict):
    """Вставить новую строку в таблицу"""
    self.exec(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join(['%s'] * len(values))});", values.values(), fetch=False)

  def select(self, table: str, columns: list[str], where: dict) -> list[tuple]:
    """Выбрать строки из таблицы"""
    if isinstance(columns, str):
      columns = [columns]
    return self.exec(f"SELECT {','.join(columns)} FROM {table} WHERE {_gws(where)};", where.values(), fetch=True)

  def update(self, table: str, values: dict, where: dict):
    """Изменить строки в таблице"""
    self.exec(f"UPDATE {table} SET {_gws(values, ',')} WHERE {_gws(where)};", list(values.values()) + list(where.values()), fetch=False)
