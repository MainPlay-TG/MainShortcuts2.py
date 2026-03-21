from functools import cached_property
from urllib import parse
from types import MappingProxyType


class ParseResult(parse.ParseResult):
  @cached_property
  def path_parts(self):
    """`path.split('/')`"""
    return tuple(self.path.split("/"))

  @cached_property
  def query_dict(self):
    return MappingProxyType(dict(self.parse_qsl(keep_blank_values=True)))

  @classmethod
  def from_url(cls, url: str, **kw):
    return cls(*parse.urlparse(url, **kw))

  def parse_qs(self, **kw):
    return parse.parse_qs(self.query, **kw)

  def parse_qsl(self, **kw):
    return parse.parse_qsl(self.query, **kw)
