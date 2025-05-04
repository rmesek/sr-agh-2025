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

class ItemInput(_message.Message):
    __slots__ = ("name", "value", "details")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: float
    details: str
    def __init__(self, name: _Optional[str] = ..., value: _Optional[float] = ..., details: _Optional[str] = ...) -> None: ...

class GetItemsRequest(_message.Message):
    __slots__ = ("item_ids",)
    ITEM_IDS_FIELD_NUMBER: _ClassVar[int]
    item_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, item_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class GetItemsResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class AddItemsRequest(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ItemInput]
    def __init__(self, items: _Optional[_Iterable[_Union[ItemInput, _Mapping]]] = ...) -> None: ...

class AddItemsResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class ClearItemsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ClearItemsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
