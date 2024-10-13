from dataclasses import dataclass
from typing import Optional, Iterable

from lib.services.alias_service import AliasService, AliasError


@dataclass(frozen=True)
class Operation:
    key: str
    value: Optional[str] = None

    def __str__(self) -> str:
        if self.is_read:
            return self.key
        else:
            return f"{self.key}={self.value}"

    @property
    def is_read(self) -> bool:
        return self.value is None

    @property
    def is_write(self) -> bool:
        return not self.is_read


class OperationUtil:
    """Extracts operation objects from binary data (HTTP or simple binary
    format).
    """

    @classmethod
    def bytes_to_operations(
        cls,
        query_string: str,
        alias_service: AliasService
    ) -> tuple[Iterable[Operation], list[Operation], list[Operation]]:
        return cls._extract_operations_from_query_string(
            query_string,
            alias_service
        )

    @classmethod
    def _extract_operations_from_query_string(
        cls,
        query_string: str,
        alias_service: AliasService
    ) -> tuple[Iterable[Operation], list[Operation], list[Operation]]:
        read_operations_by_key: dict[str, Operation] = {}
        write_operations: list[Operation] = []
        error_operations: list[Operation] = []

        for entry_str in query_string.split("&"):
            entry_members = entry_str.split("=")

            try:
                key = alias_service.to_nad_name_strict(entry_members[0])
            except AliasError as e:
                val = entry_members[1] if len(entry_members) > 1 else None
                error_operations.append(Operation(entry_members[0], val))
                continue

            try:
                write_operations.append(Operation(key, entry_members[1]))
                read_operations_by_key[key] = Operation(key)
            except IndexError:
                read_operations_by_key[key] = Operation(key)

        return (
            read_operations_by_key.values(),
            write_operations,
            error_operations
        )
