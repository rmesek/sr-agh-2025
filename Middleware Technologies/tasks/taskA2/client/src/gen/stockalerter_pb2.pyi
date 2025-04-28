from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AlertType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ALERT_TYPE_UNSPECIFIED: _ClassVar[AlertType]
    PRICE_ABOVE_THRESHOLD: _ClassVar[AlertType]
    PRICE_BELOW_THRESHOLD: _ClassVar[AlertType]
    GENERAL_UPDATE: _ClassVar[AlertType]
ALERT_TYPE_UNSPECIFIED: AlertType
PRICE_ABOVE_THRESHOLD: AlertType
PRICE_BELOW_THRESHOLD: AlertType
GENERAL_UPDATE: AlertType

class Money(_message.Message):
    __slots__ = ("currency_code", "units", "nanos")
    CURRENCY_CODE_FIELD_NUMBER: _ClassVar[int]
    UNITS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    currency_code: str
    units: int
    nanos: int
    def __init__(self, currency_code: _Optional[str] = ..., units: _Optional[int] = ..., nanos: _Optional[int] = ...) -> None: ...

class SubscriptionRequest(_message.Message):
    __slots__ = ("subscription_id", "stock_symbol", "notify_above_price", "notify_below_price")
    SUBSCRIPTION_ID_FIELD_NUMBER: _ClassVar[int]
    STOCK_SYMBOL_FIELD_NUMBER: _ClassVar[int]
    NOTIFY_ABOVE_PRICE_FIELD_NUMBER: _ClassVar[int]
    NOTIFY_BELOW_PRICE_FIELD_NUMBER: _ClassVar[int]
    subscription_id: str
    stock_symbol: str
    notify_above_price: Money
    notify_below_price: Money
    def __init__(self, subscription_id: _Optional[str] = ..., stock_symbol: _Optional[str] = ..., notify_above_price: _Optional[_Union[Money, _Mapping]] = ..., notify_below_price: _Optional[_Union[Money, _Mapping]] = ...) -> None: ...

class NotificationMessage(_message.Message):
    __slots__ = ("stock_symbol", "current_price", "alert_type", "alert_message", "related_symbols", "timestamp")
    STOCK_SYMBOL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PRICE_FIELD_NUMBER: _ClassVar[int]
    ALERT_TYPE_FIELD_NUMBER: _ClassVar[int]
    ALERT_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RELATED_SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    stock_symbol: str
    current_price: Money
    alert_type: AlertType
    alert_message: str
    related_symbols: _containers.RepeatedScalarFieldContainer[str]
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, stock_symbol: _Optional[str] = ..., current_price: _Optional[_Union[Money, _Mapping]] = ..., alert_type: _Optional[_Union[AlertType, str]] = ..., alert_message: _Optional[str] = ..., related_symbols: _Optional[_Iterable[str]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UnsubscribeRequest(_message.Message):
    __slots__ = ("subscription_id",)
    SUBSCRIPTION_ID_FIELD_NUMBER: _ClassVar[int]
    subscription_id: str
    def __init__(self, subscription_id: _Optional[str] = ...) -> None: ...

class UnsubscribeResponse(_message.Message):
    __slots__ = ("confirmation_message",)
    CONFIRMATION_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    confirmation_message: str
    def __init__(self, confirmation_message: _Optional[str] = ...) -> None: ...
