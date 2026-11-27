import re
from asyncio import AbstractEventLoop
from datetime import timedelta, datetime
from timeit import default_timer
from typing import List, Tuple

from data_logger.constants import DATA_LOGGER_SAMPLES_TABLE, \
    DATA_LOGGER_ALARMS_TABLE
from data_logger.local.config.config.config import Config
from data_logger.local.db.db import Db
from data_logger.local.db.model import Alarm, Measurement
from data_logger.local.db.query_builder import QueryBuilder
from lib.general.conditional_logger import ConditionalLogger
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner


class Repository:
    _NAD_SIZE = 12
    _TIME_ISO_FORMAT_MAX_SIZE = 26
    _TAG_MAX_SIZE = 40
    _VALUE_MAX_SIZE = 16
    _ALARM_MAX_TYPE_SIZE = 11
    _ALARM_MAX_MESSAGE_SIZE = 50
    _ALARM_MAX_CLASS_SIZE = 20

    def __init__(self,
                 log: ConditionalLogger,
                 db: Db,
                 config: Config,
                 cpu_intensive_task_runner: CPUIntensiveTaskRunner,
                 loop: AbstractEventLoop):
        self._log: ConditionalLogger = log
        self._db: Db = db
        self._db_config = config.dbase_config
        self._query_builder = QueryBuilder(self._db_config.max_query_size)
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )
        self._loop: AbstractEventLoop = loop

        self._measurements: str = DATA_LOGGER_SAMPLES_TABLE
        self._alarms: str = DATA_LOGGER_ALARMS_TABLE

    async def _table_exists(self, table_name: str) -> bool:
        """Checks if table with specified name exists.

        :param table_name: Name of the table which existence to check.
        :return: True if table exists, or false otherwise.
        """
        res = await self._db.execute_query(
            f"SELECT COUNT(*) FROM information_schema.tables "
            f"WHERE table_schema = '{self._db_config.name}'"
            f"AND table_name = '{table_name}';"
        )
        return True if res[0][0] == 1 else False

    async def _create_table_alarms(self) -> None:
        """Creates alarms table.

        Note: Make sure this matches query in db_create.sql
        """
        db_name = self._db_config.name
        await self._db.execute_query(
            f"CREATE TABLE IF NOT EXISTS `{db_name}`.`{self._alarms}` ("
            f"  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',"
            f"  `type` INT(11) NOT NULL COMMENT '1-alarm, 2-event',"
            f"  `nad` VARCHAR(12) NOT NULL COMMENT 'Cybro device NAD',"
            f"  `tag` VARCHAR(40) NOT NULL COMMENT 'Cybro variable name',"
            f"  `value` VARCHAR(16) NOT NULL COMMENT 'Cybro variable value',"
            f"  `priority` SMALLINT(6) NOT NULL COMMENT 'Task priority: 0-low, "
            f"1-medium, 2-high',"
            f"  `class` VARCHAR(20) NOT NULL COMMENT 'Maps to task class tag "
            f"in data_logger.xml, user-defineable.',"
            f"  `message` VARCHAR(50) NOT NULL COMMENT 'Alarm message "
            f"configured by user',"
            f"  `timestamp_raise` DATETIME NOT NULL COMMENT 'Date and time "
            f"alarm was triggered',"
            f"  `timestamp_gone` DATETIME NULL COMMENT 'Date and time state "
            f"of cybro variable returned to normal',"
            f"  `timestamp_ack` DATETIME NULL COMMENT 'Date and time operator "
            f"acknowledged alarm',"
            f"  PRIMARY KEY (`id`),"
            f"  INDEX `tag_index` (`tag` ASC)) "
            f"ENGINE = MyISAM "
            f"DEFAULT CHARACTER SET = utf8 "
            f"COMMENT = 'Table holds triggered alarms and events, defined in "
            f"data_logger.xml';"
        )

    async def _create_table_measurements(self) -> None:
        """Creates measurements table.

        Note: Make sure this matches query in db_create.sql
        """
        db_name = self._db_config.name
        await self._db.execute_query(
            f"CREATE TABLE IF NOT EXISTS `{db_name}`.`{self._measurements}` ("
            f"  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',"
            f"  `nad` VARCHAR(12) NOT NULL COMMENT 'Cybro device NAD',"
            f"  `tag` VARCHAR(40) NOT NULL COMMENT 'Cybro variable name',"
            f"  `value` VARCHAR(16) NOT NULL COMMENT 'Cybro variable value',"
            f"  `timestamp` DATETIME NOT NULL COMMENT 'Date and time when "
            f"record is created',"
            f"  PRIMARY KEY (`id`),"
            f"  INDEX `tag_index` (`tag` ASC)) "
            f"ENGINE = MyISAM "
            f"DEFAULT CHARACTER SET = utf8 "
            f"COMMENT = 'Table holds measurements data, defined by sample tag "
            f"in data_logger.xml';"
        )

    async def init(self):
        """Checks for tables and creates missing ones.
        """
        self._log.debug("Initializing repository")

        alarms_exist = await self._table_exists(self._alarms)
        if not alarms_exist:
            await self._create_table_alarms()

        measurements_exist = await self._table_exists(self._measurements)
        if not measurements_exist:
            await self._create_table_measurements()

    def _parse_plc_name(self, nad: str) -> int:
        match = re.search("^c(\\d+)$", nad)

        if match is None:
            raise Exception(f"Invalid plc name {nad}")

        return int(match[1])

    def _parse_value(self, value: str) -> str:
        """Limits float number string length to fit into database.

        :param value: Value to be parsed.
        """
        return value if value.isdecimal() else value[:self._VALUE_MAX_SIZE]

    async def create_alarms(self, alarms: List[Alarm]):
        t = default_timer()
        self._log.debug("Preparing queries...")

        queries = self._query_builder.create_insert_queries(
            table=self._alarms,
            columns=(
                "nad",
                "tag",
                "priority",
                "value",
                "type",
                "class",
                "message",
                "timestamp_raise",
                "timestamp_gone",
                "timestamp_ack"
            ),
            rows=[
                (
                    alarm.nad,
                    alarm.tag,
                    str(alarm.priority),
                    self._parse_value(alarm.value),
                    str(alarm.alarm_type.value),
                    alarm.alarm_class,
                    alarm.message,
                    alarm.timestamp_raise.isoformat(sep=' ',
                                                    timespec='seconds'),
                    None if alarm.timestamp_gone is None
                    else alarm.timestamp_gone.isoformat(sep=' ',
                                                        timespec='seconds'),
                    None if alarm.timestamp_ack is None
                    else alarm.timestamp_ack.isoformat(sep=' ',
                                                       timespec='seconds')

                ) for alarm in alarms
            ],
            value_max_sizes=[
                self._NAD_SIZE,
                self._TAG_MAX_SIZE,
                self._VALUE_MAX_SIZE,
                self._ALARM_MAX_TYPE_SIZE,
                self._ALARM_MAX_CLASS_SIZE,
                self._ALARM_MAX_MESSAGE_SIZE,
                self._TIME_ISO_FORMAT_MAX_SIZE
            ]
        )

        self._log.debug(lambda: f"Prepared {len(queries)} queries in "
                                f"{timedelta(seconds=default_timer() - t)}")

        for query, args in queries:
            await self._loop.create_task(
                self._db.execute_query(query, args)
            )

    async def clear_alarms(self, alarm_ids: List[int], timestamp: datetime):
        if len(alarm_ids) == 0:
            return

        query, args = self._query_builder.create_clear_alarms_query(
            self._alarms,
            alarm_ids,
            timestamp
        )

        await self._loop.create_task(
            self._db.execute_query(query, args)
        )

    async def get_not_acknowledged_alarms(self,
                                          conditions: List[Tuple[str, str]]
                                          ) -> List[Alarm]:
        query = (f'SELECT'
                 f' id,'
                 f' nad,'
                 f' tag,'
                 f' value,'
                 f' type,'
                 f' class,'
                 f' message,'
                 f' timestamp_raise,'
                 f' timestamp_gone,'
                 f' timestamp_ack '
                 f'FROM {self._alarms}')
        args = None

        if len(conditions) > 0:
            predicate_joined = " OR ".join(
                "(nad = %s AND tag = %s AND timestamp_ack = '0000-00-00')"
                for _ in conditions
            )
            args = tuple(
                arg for nad, tag in conditions
                for arg in (nad, tag)
            )

            query = (f'SELECT'
                     f' id,'
                     f' nad,'
                     f' tag,'
                     f' priority,'
                     f' value,'
                     f' type,'
                     f' class,'
                     f' message,'
                     f' timestamp_raise,'
                     f' timestamp_gone,'
                     f' timestamp_ack '
                     f'FROM {self._alarms} '
                     f'WHERE {predicate_joined}')

        result = await self._db.execute_query(query, args)

        return [Alarm.create_from_db_result(*values) for values in result]

    async def create_measurements(self, measurements: List[Measurement]):
        t = default_timer()
        self._log.debug("Preparing queries...")

        queries = self._query_builder.create_insert_queries(
            self._measurements,
            ("nad", "tag", "value", "timestamp"),
            [
                (
                    m.nad,
                    m.tag,
                    self._parse_value(m.value),
                    m.timestamp.isoformat(sep=' ', timespec='seconds')
                )
                for m in measurements
            ],
            [
                self._NAD_SIZE,
                self._TAG_MAX_SIZE,
                self._VALUE_MAX_SIZE,
                self._TIME_ISO_FORMAT_MAX_SIZE
            ]
        )

        self._log.debug(f"queries {queries}")

        self._log.debug(lambda: f"Prepared {len(queries)} queries "
                                f"in {timedelta(seconds=default_timer() - t)}")

        for query, args in queries:
            await self._loop.create_task(
                self._db.execute_query(query, args)
            )

    @classmethod
    def _reduce_to_disjunction(cls, accumulator, condition):
        return condition if accumulator is None else accumulator | condition
