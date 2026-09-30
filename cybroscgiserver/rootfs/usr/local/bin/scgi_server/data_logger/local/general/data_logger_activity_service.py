from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .task import DataLoggerMeasurementTask, DataLoggerAlarmTask


@dataclass
class TaskActivity:
    trigger_count: int = 0
    last_trigger_datetime: Optional[datetime] = None
    valid_results: int = 0
    invalid_results: int = 0
    duration: Optional[timedelta] = None

    def report_task_triggered(self) -> None:
        self.trigger_count += 1
        self.last_trigger_datetime = datetime.now()

    def report_task_results(self,
                            valid_count: int,
                            invalid_count: int,
                            duration: timedelta) -> None:
        self.valid_results = valid_count
        self.invalid_results = invalid_count
        self.duration = duration


class DataLoggerActivityService:
    def __init__(self):
        self._measurement_tasks: List[DataLoggerMeasurementTask] = []
        self._alarm_tasks: List[DataLoggerAlarmTask] = []
        self._task_activities: Dict[int, TaskActivity] = {}

    def __getitem__(self, task_id: int) -> TaskActivity:
        try:
            return self._task_activities[task_id]
        except KeyError:
            task_activity = TaskActivity()
            self._task_activities[task_id] = task_activity
            return task_activity

    def report_tasks_loaded(self,
                            measurement_tasks: List[DataLoggerMeasurementTask],
                            alarm_tasks: List[DataLoggerAlarmTask]) -> None:
        self._measurement_tasks = measurement_tasks
        self._alarm_tasks = alarm_tasks
        self._task_activities: Dict[int, TaskActivity] = {}

    def report_task_triggered(self, task_id: int) -> None:
        self[task_id].report_task_triggered()

    def report_task_results(self,
                            task_id: int,
                            valid_count: int,
                            invalid_count: int,
                            duration: timedelta) -> None:
        self[task_id].report_task_results(valid_count, invalid_count, duration)

    @property
    def measurement_tasks(self) -> List[DataLoggerMeasurementTask]:
        return self._measurement_tasks

    @property
    def alarm_tasks(self) -> List[DataLoggerAlarmTask]:
        return self._alarm_tasks
