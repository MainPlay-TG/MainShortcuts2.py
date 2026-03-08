import builtins
from .core import ms
from ._any2json_regs import decoders, encoders, reg_decoder, reg_encoder


def _decode_obj(obj: dict):
  return decoders[obj["type"]](obj["data"])


def _encode_obj(obj) -> dict:
  result = {}
  obj_type = builtins.type(obj)
  if hasattr(obj_type, "__module__"):
    if hasattr(obj_type, "__name__"):
      type = obj_type.__module__ + "." + obj_type.__name__
      if type in encoders:
        result["data"] = encoders[type](obj)
        result["type"] = type
        return result
  for type, func in encoders.items():
    try:
      encoded = func(obj)
      if not encoded is None:
        result["data"] = encoded
        result["type"] = type
        return result
    except Exception:
      pass
  raise ValueError("failed to encode object " + repr(obj))


def decode(text, **kw):
  kw["text"] = text
  return _decode_obj(ms.json.decode(**kw))


def encode(data, **kw) -> str:
  kw["data"] = _encode_obj(data)
  return ms.json.encode(**kw)


def read(path: str, **kw):
  kw["path"] = path
  return _decode_obj(ms.json.read(**kw))


def write(path: str, data, **kw):
  kw["data"] = _encode_obj(data)
  kw["path"] = path
  return ms.json.write(**kw)
