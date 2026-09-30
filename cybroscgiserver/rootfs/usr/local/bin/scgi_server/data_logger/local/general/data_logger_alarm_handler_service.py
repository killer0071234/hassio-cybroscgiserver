import asyncio
from datetime import datetime
from typing import List, Tuple, Dict

from lib.general.conditional_logger import ConditionalLogger
from data_logger.local.config.data_logger_config import AlarmPriority, \
    AlarmRange
from data_logger.local.db.model import Alarm
from data_logger.local.db.repository import Repository
from data_logger.local.general.data_logger_measurement import \
    DataLoggerMeasurement
from data_logger.local.general.errors import UnexpectedValue


class DataLoggerAlarmHandlerService:
    def __init__(self,
                 log: ConditionalLogger,
                 repository: Repository) -> None:
        self._log: ConditionalLogger = log
        self._repository: Repository = repository

    async def on_new_data(self,
                          measurements: List[DataLoggerMeasurement],
                          message: str,
                          alarm_class: str,
                          priority: AlarmPriority,
                          alarm_range: AlarmRange,
                          task_type: int):
        self._log.debug(lambda: f"Alarm - {len(measurements)} variables")

        not_acknowledged = await self._get_not_acknowledged_alarms(
            [(m.nad, m.variable) for m in measurements]
        )

        to_create_alarms = []
        to_clear_alarm_ids = []

        for measurement in measurements:
            try:
                not_acknowledged_alarms = \
                    not_acknowledged[measurement.nad][measurement.variable]
            except KeyError:
                not_acknowledged_alarms = []

            not_cleared_alarm_ids = [
                alarm.id for alarm in not_acknowledged_alarms
                if alarm.is_timestamp_gone_default
            ]

            (
                _is_in_range,
                _is_in_range_with_hysteresis
            ) = self._is_in_range(measurement.value, alarm_range)

            if _is_in_range_with_hysteresis:
                to_clear_alarm_ids = not_cleared_alarm_ids
            elif not _is_in_range and len(not_cleared_alarm_ids) == 0:
                to_create_alarms.append(
                    Alarm(
                        id=None,
                        nad=measurement.nad,
                        tag=measurement.variable,
                        priority=priority.value,
                        value=measurement.value,
                        alarm_type=task_type,
                        alarm_class=alarm_class,
                        message=message,
                        timestamp_raise=datetime.now()
                    )
                )

        if len(to_create_alarms) > 0:
            self._log.debug(lambda: f"Raise: " + ", ".join(
                (str(a) for a in to_create_alarms)
            ))

        if len(to_clear_alarm_ids) > 0:
            self._log.debug(lambda: f"Clear: " + ", ".join(
                (str(a_id) for a_id in to_clear_alarm_ids)
            ))

        await asyncio.gather(
            self._repository.create_alarms(to_create_alarms),
            self._repository.clear_alarms(to_clear_alarm_ids, datetime.now())
        )

    async def _get_not_acknowledged_alarms(
        self,
        conditions: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, List[Alarm]]]:
        alarms = await self._repository.get_not_acknowledged_alarms(conditions)

        result = {}
        for alarm in alarms:
            try:
                alarms_for_nad = result[alarm.nad]
            except KeyError:
                alarms_for_nad = {}
                result[alarm.nad] = alarms_for_nad

            try:
                alarms_for_tag = alarms_for_nad[alarm.tag]
            except KeyError:
                alarms_for_tag = []
                alarms_for_nad[alarm.tag] = alarms_for_tag

            alarms_for_tag.append(alarm)

        return result

    @classmethod
    def _is_in_range(cls,
                     value_str: str,
                     alarm_range: AlarmRange) -> Tuple[bool, bool]:
        try:
            value = float(value_str)
        except ValueError:
            raise UnexpectedValue(value_str, "Expected number")

        _is_in_range = alarm_range.low <= value <= alarm_range.high

        low_with_hysteresis = alarm_range.low + alarm_range.hysteresis
        high_with_hysteresis = alarm_range.high - alarm_range.hysteresis

        _is_in_range_with_hysteresis = \
            low_with_hysteresis <= value <= high_with_hysteresis

        return _is_in_range, _is_in_range_with_hysteresis
