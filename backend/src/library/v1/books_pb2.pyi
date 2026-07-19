import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from library.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Book(_message.Message):
    __slots__ = ("id", "title", "author", "isbn", "publisher", "published_year", "category", "description", "total_copies", "available_copies", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COPIES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_COPIES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    author: str
    isbn: str
    publisher: str
    published_year: int
    category: str
    description: str
    total_copies: int
    available_copies: int
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., author: _Optional[str] = ..., isbn: _Optional[str] = ..., publisher: _Optional[str] = ..., published_year: _Optional[int] = ..., category: _Optional[str] = ..., description: _Optional[str] = ..., total_copies: _Optional[int] = ..., available_copies: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BookCopy(_message.Message):
    __slots__ = ("id", "book_id", "barcode", "condition", "status", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    BARCODE_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    book_id: str
    barcode: str
    condition: str
    status: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., book_id: _Optional[str] = ..., barcode: _Optional[str] = ..., condition: _Optional[str] = ..., status: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateBookRequest(_message.Message):
    __slots__ = ("title", "author", "isbn", "publisher", "published_year", "category", "description")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    title: str
    author: str
    isbn: str
    publisher: str
    published_year: int
    category: str
    description: str
    def __init__(self, title: _Optional[str] = ..., author: _Optional[str] = ..., isbn: _Optional[str] = ..., publisher: _Optional[str] = ..., published_year: _Optional[int] = ..., category: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class UpdateBookRequest(_message.Message):
    __slots__ = ("id", "title", "author", "isbn", "publisher", "published_year", "category", "description")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_YEAR_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    author: str
    isbn: str
    publisher: str
    published_year: int
    category: str
    description: str
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., author: _Optional[str] = ..., isbn: _Optional[str] = ..., publisher: _Optional[str] = ..., published_year: _Optional[int] = ..., category: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class GetBookRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListBooksRequest(_message.Message):
    __slots__ = ("search", "page")
    SEARCH_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    search: str
    page: _common_pb2.PageParams
    def __init__(self, search: _Optional[str] = ..., page: _Optional[_Union[_common_pb2.PageParams, _Mapping]] = ...) -> None: ...

class ListBooksResponse(_message.Message):
    __slots__ = ("books", "page")
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedCompositeFieldContainer[Book]
    page: _common_pb2.PageInfo
    def __init__(self, books: _Optional[_Iterable[_Union[Book, _Mapping]]] = ..., page: _Optional[_Union[_common_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class AddCopyRequest(_message.Message):
    __slots__ = ("book_id", "barcode", "condition")
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    BARCODE_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    book_id: str
    barcode: str
    condition: str
    def __init__(self, book_id: _Optional[str] = ..., barcode: _Optional[str] = ..., condition: _Optional[str] = ...) -> None: ...

class ListCopiesRequest(_message.Message):
    __slots__ = ("book_id",)
    BOOK_ID_FIELD_NUMBER: _ClassVar[int]
    book_id: str
    def __init__(self, book_id: _Optional[str] = ...) -> None: ...

class ListCopiesResponse(_message.Message):
    __slots__ = ("copies",)
    COPIES_FIELD_NUMBER: _ClassVar[int]
    copies: _containers.RepeatedCompositeFieldContainer[BookCopy]
    def __init__(self, copies: _Optional[_Iterable[_Union[BookCopy, _Mapping]]] = ...) -> None: ...
