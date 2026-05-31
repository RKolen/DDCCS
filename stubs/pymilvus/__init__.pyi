from typing import Any, Dict, List, Optional

class DataType:
    NONE: int
    BOOL: int
    INT8: int
    INT16: int
    INT32: int
    INT64: int
    FLOAT: int
    DOUBLE: int
    STRING: int
    VARCHAR: int
    ARRAY: int
    JSON: int
    FLOAT_VECTOR: int
    BINARY_VECTOR: int
    FLOAT16_VECTOR: int
    BFLOAT16_VECTOR: int
    SPARSE_FLOAT_VECTOR: int

class FieldSchema:
    def __init__(
        self,
        name: str,
        dtype: Any,
        description: str = ...,
        is_primary: bool = ...,
        auto_id: bool = ...,
        max_length: int = ...,
        dim: int = ...,
        **kwargs: Any,
    ) -> None: ...

class CollectionSchema:
    def __init__(
        self,
        fields: List[FieldSchema],
        description: str = ...,
        **kwargs: Any,
    ) -> None: ...

class Collection:
    def __init__(
        self,
        name: str,
        schema: Optional[CollectionSchema] = ...,
        using: str = ...,
        **kwargs: Any,
    ) -> None: ...
    def insert(self, data: Any, **kwargs: Any) -> Any: ...
    def search(
        self,
        data: Any,
        anns_field: str,
        param: Dict[str, Any],
        limit: int,
        expr: Optional[str] = ...,
        output_fields: Optional[List[str]] = ...,
        **kwargs: Any,
    ) -> Any: ...
    def query(self, expr: str, output_fields: Optional[List[str]] = ..., **kwargs: Any) -> Any: ...
    def load(self, **kwargs: Any) -> None: ...
    def release(self) -> None: ...
    def drop_index(self, **kwargs: Any) -> None: ...
    def create_index(self, field_name: str, index_params: Dict[str, Any], **kwargs: Any) -> None: ...
    def flush(self, **kwargs: Any) -> None: ...
    def drop(self) -> None: ...
    def num_entities(self) -> int: ...

class _Connections:
    def connect(self, alias: str = ..., host: str = ..., port: Any = ..., **kwargs: Any) -> None: ...
    def disconnect(self, alias: str = ...) -> None: ...
    def has_connection(self, alias: str = ...) -> bool: ...

class _Utility:
    def has_collection(self, collection_name: str, using: str = ...) -> bool: ...
    def drop_collection(self, collection_name: str, using: str = ...) -> None: ...
    def list_collections(self, using: str = ...) -> List[str]: ...
    def get_server_version(self, using: str = ...) -> str: ...

connections: _Connections
utility: _Utility
