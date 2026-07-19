import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from library.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Loan(_message.Message):
    __slots__ = ("id", "copy_id", "book_id", "book_title", "barcode", "member_id", "member_name", "staff_id", "borrowed_at", "due_at", "returned_at", "status", "renewed_count")
    ID_FIELD_NUMBER: _ClassVar[int]
    COPY_ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_TITLE_FIELD_NUMBER: _ClassVar[int]
    BARCODE_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    MEMBER_NAME_FIELD_NUMBER: _ClassVar[int]
    STAFF_ID_FIELD_NUMBER: _ClassVar[int]
    BORROWED_AT_FIELD_NUMBER: _ClassVar[int]
    DUE_AT_FIELD_NUMBER: _ClassVar[int]
    RETURNED_AT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RENEWED_COUNT_FIELD_NUMBER: _ClassVar[int]
    id: str
    copy_id: str
    book_id: str
    book_title: str
    barcode: str
    member_id: str
    member_name: str
    staff_id: str
    borrowed_at: _timestamp_pb2.Timestamp
    due_at: _timestamp_pb2.Timestamp
    returned_at: _timestamp_pb2.Timestamp
    status: str
    renewed_count: int
    def __init__(self, id: _Optional[str] = ..., copy_id: _Optional[str] = ..., book_id: _Optional[str] = ..., book_title: _Optional[str] = ..., barcode: _Optional[str] = ..., member_id: _Optional[str] = ..., member_name: _Optional[str] = ..., staff_id: _Optional[str] = ..., borrowed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., due_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., returned_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., status: _Optional[str] = ..., renewed_count: _Optional[int] = ...) -> None: ...

class BorrowBookRequest(_message.Message):
    __slots__ = ("member_id", "copy_id", "book_id")
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    COPY_ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    member_id: str
    copy_id: str
    book_id: str
    def __init__(self, member_id: _Optional[str] = ..., copy_id: _Optional[str] = ..., book_id: _Optional[str] = ...) -> None: ...

class ReturnBookRequest(_message.Message):
    __slots__ = ("loan_id",)
    LOAN_ID_FIELD_NUMBER: _ClassVar[int]
    loan_id: str
    def __init__(self, loan_id: _Optional[str] = ...) -> None: ...

class ListLoansRequest(_message.Message):
    __slots__ = ("member_id", "active_only", "overdue_only", "page")
    MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_ONLY_FIELD_NUMBER: _ClassVar[int]
    OVERDUE_ONLY_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    member_id: str
    active_only: bool
    overdue_only: bool
    page: _common_pb2.PageParams
    def __init__(self, member_id: _Optional[str] = ..., active_only: _Optional[bool] = ..., overdue_only: _Optional[bool] = ..., page: _Optional[_Union[_common_pb2.PageParams, _Mapping]] = ...) -> None: ...

class ListLoansResponse(_message.Message):
    __slots__ = ("loans", "page")
    LOANS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    loans: _containers.RepeatedCompositeFieldContainer[Loan]
    page: _common_pb2.PageInfo
    def __init__(self, loans: _Optional[_Iterable[_Union[Loan, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageInfo, _Mapping]] = ...) -> None: ...
