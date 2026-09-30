from itertools import chain
from typing import Iterable, Tuple, List, Dict, Union

from data_logger.local.config.data_logger_config import AlarmRange, \
    DataLoggerConfig, MeasurementTask, AlarmTask, Target
from .task import DataLoggerMeasurementTask, DataLoggerAlarmTask


def _extract_tasks(
    config: DataLoggerConfig
) -> Tuple[List[DataLoggerMeasurementTask], List[DataLoggerAlarmTask]]:
    measurements = _extract_measurement_tasks(config)
    alarms = _extract_alarm_tasks(config, len(measurements))
    return measurements, alarms


def _extract_measurement_tasks(config: DataLoggerConfig
                               ) -> List[DataLoggerMeasurementTask]:
    return [
        _create_measurement_task(i, task, config.groups)
        for i, task in enumerate(config.measurement_tasks) if task.enabled
    ]


def _create_measurement_task(task_id: int,
                             task: MeasurementTask,
                             groups: Dict[str, List[int]]
                             ) -> DataLoggerMeasurementTask:
    expanded_targets = _expand_targets(task.targets, groups)
    return DataLoggerMeasurementTask(task_id,
                                     task.period,
                                     list(expanded_targets))


def _extract_alarm_tasks(config: DataLoggerConfig,
                         first_id: int) -> List[DataLoggerAlarmTask]:
    return [
        _create_alarm_task(first_id + i, task, config.groups)
        for (i, task) in enumerate(config.alarm_tasks) if task.enabled
    ]


def _create_alarm_task(task_id: int,
                       task: AlarmTask,
                       groups: Dict[str, List[int]]) -> DataLoggerAlarmTask:
    expanded_targets = _expand_targets(task.targets, groups)

    return DataLoggerAlarmTask(
        id=task_id,
        period=task.period,
        targets=list(expanded_targets),
        alarm_class=task.alarm_class,
        priority=task.priority,
        range=AlarmRange() if task.range is None else task.range,
        message=task.message,
        type=task.type
    )


def _expand_targets(targets: List[Target],
                    groups: Dict[str, List[int]]) -> Iterable[Union[int, str]]:
    return chain(*(_expand_target(target, groups) for target in targets))


def _expand_target(target: Target, groups: Dict[str, List[int]]):
    if target.is_group:
        group_name = target.context
        try:
            for nad in groups[group_name]:
                (yield nad, target.variable)
        except KeyError:
            return
    else:
        (yield target.context, target.variable)
