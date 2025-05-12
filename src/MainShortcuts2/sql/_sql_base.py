import atexit
from MainShortcuts2 import ms
__all__ = ["check_type", "DatabaseBase", "ObjectBase"]


def check_type(obj, cls: type, allow_None: bool = True):
  if allow_None:
    if obj is None:
      return
  if isinstance(obj, cls):
    return obj
  err_text = "Object %r must be like %r"
  if allow_None:
    err_text += " or None"
  raise ValueError(err_text % (obj, cls))


def _conv_val(value):
  if isinstance(value, memoryview):
    return value.tobytes()
  return value


def _conv_row(row: list):
  result = []
  for i in row:
    result.append(_conv_val(i))
  return tuple(result)


class ObjectBase:
  _autoinsert: bool
  _table: str

  def __init__(self, db, **index):
    assert len(index) > 0
    self._db: DatabaseBase = db
    self._index: dict = index
    if self._autoinsert:
      self._insert()

  def __repr__(self) -> str:
    cls = type(self)
    kwargs = []
    for k, v in self._index.items():
      kwargs.append(k + "=" + repr(v))
    return "{}.{}(...,{})".format(cls.__module__, cls.__name__, ",".join(kwargs))

  def __delitem__(self, column: str):
    self[column] = None

  def __getitem__(self, column: str):
    if column in self._index:
      return self._index[column]
    result = self._db.select_one(self._table, [column], self._index)[0]
    return result

  def __setitem__(self, column: str, value):
    self._db.update(self._table, {column: value}, self._index)
    if column in self._index:
      self._index[column] = value

  def _insert(self):
    if len(self._db.select(self._table, [list(self._index)[0]], self._index)) > 0:
      return
    self._db.insert(self._table, self._index)

  def delete_from_db(self):
    self._db.delete(self._table, self._index)

    @ms.utils.decorators.setattr(self, "__getitem__")
    @ms.utils.decorators.setattr(self, "__setitem__")
    def _(*a, **b):
      raise RuntimeError("This object is removed from the database")


class DatabaseBase:
  def __init__(self, *, autosave: bool = True, connect_on_init: bool = True, schema: dict[str, dict[str, str]] = None, **kw):
    atexit.register(self.close)
    self._need_update_schema = True
    self._updating_schema = False
    self.autosave = autosave
    self.closed = False
    self.conn = None
    self.conn_kw = kw
    self.ConnectionError = ConnectionError
    self.schema = schema
    if connect_on_init:
      self.connect()

  @property
  def connected(self):
    return not self.conn is None

  def cursor(self):
    self.connect()
    return self.conn.cursor()

  def update_schema(self, schema: dict[str, dict[str, str]] = None):
    if self._updating_schema:
      return
    if schema is None:
      schema = self.schema
    if schema is None:
      return
    self._updating_schema = True
    try:
      self._update_schema(schema)
    except:
      self._updating_schema = False
      raise
    self._need_update_schema = False
    self._updating_schema = False

  def save(self):
    if self.connected:
      self.conn.commit()

  def close(self, save: bool = True):
    if self.closed:
      return
    if save:
      self.save()
    self.disconnect()
    self.closed = True

  def connect(self):
    if self.closed:
      raise RuntimeError("Database closed")
    if not self.connected:
      self._connect()
      if self._need_update_schema:
        self.update_schema()

  def disconnect(self):
    if self.connected:
      self.conn.close()
      self.conn = None

  def exec(self, code: str, values: tuple = [], fetch: bool = True, reconnect: bool = True) -> list[tuple]:
    if not code.endswith(";"):
      code += ";"
    if not isinstance(values, tuple):
      values = tuple(values)
    try:
      with self.cursor() as cur:
        cur.execute(code, values)
        if self.autosave:
          self.save()
        if fetch:
          return [_conv_row(i) for i in cur.fetchall()]
      return
    except self.ConnectionError:
      self.disconnect()
      if reconnect:
        return self.exec(code, values, fetch, reconnect=False)
      raise

  def exec2(self, code: str, *values, **kw):
    return self.exec(code, values, **kw)

  def _connect(self):
    raise NotImplementedError

  def _update_schema(self, schema):
    raise NotImplementedError

  def delete(self, table: str, where: dict):
    """Удалить строки из таблицы"""
    raise NotImplementedError

  def insert(self, table: str, values: dict):
    """Вставить новую строку в таблицу"""
    raise NotImplementedError

  def select(self, table: str, columns: list[str], where: dict) -> list[tuple]:
    """Выбрать строки из таблицы"""
    raise NotImplementedError

  def select_one(self, table: str, columns: list[str], where: dict, max_error: bool = True):
    results = self.select(table, columns, where)
    if len(results) == 0:
      raise IndexError("The list is empty")
    if max_error:
      if len(results) > 1:
        raise IndexError("There should be only one element in the list")
    return results[0]

  def update(self, table: str, values: dict, where: dict):
    """Изменить строки в таблице"""
    raise NotImplementedError

  def select_count(self, table: str, where: dict):
    """Получить кол-во объектов в таблице"""
    return len(self.select(table, list(where)[0], where))
