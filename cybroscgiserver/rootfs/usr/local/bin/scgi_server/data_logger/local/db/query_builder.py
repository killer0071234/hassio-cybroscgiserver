from datetime import datetime
from typing import Any, List, Tuple, Union


class QueryBuilder:
    def __init__(self, max_query_size: int = 1000000):
        self._max_query_size: int = max_query_size

    def create_insert_queries(self,
                              table: str,
                              columns: Union[List[str], Tuple[str, ...]],
                              rows: List[Tuple[Any, ...]],
                              value_max_sizes: List[int]
                              ) -> List[Tuple[str, Tuple[str, ...]]]:
        available_chars = self._max_query_size
        result = []

        query_prefix = self._create_insert_prefix(table, columns)
        available_chars = available_chars - len(query_prefix)

        # 4 - two parentheses, comma and space, 4 - two quote-marks, comma
        # and space
        query_suffix_row_len = (
            4 + sum(value_max_sizes) + len(value_max_sizes) * 4
        )

        max_rows = available_chars // query_suffix_row_len

        while len(rows) > 0:
            rows_ = rows[:max_rows]

            rows_joined = ",".join(
                self._create_format(len(r)) for r in rows
            )
            args = tuple(arg for row in rows_ for arg in row)

            result.append((
                query_prefix + rows_joined,
                args
            ))

            rows = rows[max_rows:]

        return result

    @staticmethod
    def _create_format(var_count: int) -> str:
        return "(" + ",".join(["%s"] * var_count) + ")"

    def _create_insert_prefix(self, table: str, columns: List[str]) -> str:
        columns_str = self._create_columns_string(columns)
        return f"INSERT INTO {table} {columns_str} VALUES "

    @classmethod
    def _create_columns_string(cls, columns: List[str]) -> str:
        return "(" + ", ".join(columns) + ")"

    @staticmethod
    def create_clear_alarms_query(
        table: str,
        alarm_ids: List[int],
        timestamp: datetime
    ) -> Tuple[str, Tuple[int, ...]]:
        predicate = " OR ".join("id=%s" for _ in alarm_ids)
        timestamp_gone = timestamp.isoformat(sep=' ', timespec='seconds')

        query = (f"UPDATE {table} "
                 f"SET timestamp_gone = '{timestamp_gone}' "
                 f"WHERE {predicate}")
        args = tuple(alarm_id for alarm_id in alarm_ids)

        return query, args
