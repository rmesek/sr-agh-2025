from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Item(_message.Message):
    __slots__ = ("id", "name", "value", "details")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    value: float
    details: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., value: _Optional[float] = ..., details: _Optional[str] = ...) -> None: ...

class GetItemListRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetItemListResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class GetItemRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class AddItemRequest(_message.Message):
    __slots__ = ("name", "value", "details")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: float
    details: str
    def __init__(self, name: _Optional[str] = ..., value: _Optional[float] = ..., details: _Optional[str] = ...) -> None: ...

class ClearItemListRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ClearItemListResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
