import asyncio
from asyncio import AbstractEventLoop
from datetime import datetime, timedelta
from pathlib import Path
from timeit import default_timer
from typing import List, Tuple, Optional, Union

from lib.config.errors import DataLoggerXmlParserError
from lib.general.conditional_logger import ConditionalLogger
from lib.general.misc import create_task_callback
from lib.input_output.scgi.rw_responses_xml_serializer import \
    RRResponsesXmlSerializer
from lib.input_output.scgi.scgi_client import ScgiClient
from lib.services.alias_service import AliasService
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from data_logger.local.config.data_logger_config import DataLoggerConfig
from data_logger.local.config.data_logger_config_xml_parser import \
    parse_data_logger_xml
from data_logger.local.db.repository import Repository
from data_logger.local.general.calculate_wait_time import calculate_wait_time
from data_logger.local.general.data_logger_activity_service import \
    DataLoggerActivityService
from data_logger.local.general.data_logger_alarm_handler_service import \
    DataLoggerAlarmHandlerService
from data_logger.local.general.data_logger_config_util import _extract_tasks
from data_logger.local.general.data_logger_measurement import \
    DataLoggerMeasurement
from data_logger.local.general.data_logger_measurement_handler_service import \
    DataLoggerMeasurementHandlerService
from data_logger.local.general.task import DataLoggerMeasurementTask, \
    DataLoggerAlarmTask


class DataLoggerService:
    def __init__(self,
                 log: ConditionalLogger,
                 loop: AbstractEventLoop,
                 repository: Repository,
                 data_logger_activity_service: DataLoggerActivityService,
                 cpu_intensive_task_runner: CPUIntensiveTaskRunner,
                 scgi_client: ScgiClient,
                 alias_service: AliasService,
                 data_logger_config_file: Path):
        self._log: ConditionalLogger = log
        self._loop: AbstractEventLoop = loop
        self._measurement_handler_service = (
            DataLoggerMeasurementHandlerService(self._log,
                                                repository,
                                                cpu_intensive_task_runner)
        )
        self._alarm_handler_service = DataLoggerAlarmHandlerService(self._log,
                                                                    repository)
        self._data_logger_activity_service: DataLoggerActivityService = (
            data_logger_activity_service
        )
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )
        self._scgi_client: ScgiClient = scgi_client
        self._alias_service: AliasService = alias_service
        self._data_logger_config_file: Path = data_logger_config_file

        self._running_tasks_by_id: dict = {}

    def start(self):
        self.on_file_changed()

    def on_file_changed(self):
        text = None
        try:
            with self._data_logger_config_file.open(
                "r", encoding="utf-8"
            ) as f:
                text = f.read()
        except OSError as e:
            self._log.debug(f"Can't load file "
                            f"'{self._data_logger_config_file.as_posix()}'",
                            exc_info=e)
            self._log.error(f"Can't load file "
                            f"'{self._data_logger_config_file.as_posix()}'",
                            f" {e}")

        if text is None:
            self._log.warning("No data logger config xml.")
            return

        try:
            config = parse_data_logger_xml(
                text, self._alias_service.reversed_aliases
            )
            self.on_data_logger_config(config)
        except DataLoggerXmlParserError as e:
            self._log.debug("Can't parse data logger config xml.",
                            exc_info=e)
            self._log.debug(f"Can't parse data logger config xml: {e}")

        self._log.info(f"Loaded data from {self._data_logger_config_file}")

    def on_data_logger_config(self, data_logger_config: DataLoggerConfig):
        measurement_tasks, alarm_tasks = _extract_tasks(data_logger_config)

        self._data_logger_activity_service.report_tasks_loaded(
            measurement_tasks, alarm_tasks
        )

        self._clear_existing_tasks()
        for task in measurement_tasks:
            self._run_measurement_task(task)
        for task in alarm_tasks:
            self._run_alarm_task(task)

    def _clear_existing_tasks(self):
        for task in self._running_tasks_by_id.values():
            task.cancel()
        self._running_tasks_by_id.clear()

    async def _handle_measurement(self,
                                  task: DataLoggerMeasurementTask) -> None:
        wait_time = calculate_wait_time(task.period, datetime.now())
        self._log.debug(lambda: f"Measurement {task.id} scheduled - execution "
                                f"in {wait_time}")
        await asyncio.sleep(wait_time.seconds)

        self._data_logger_activity_service.report_task_triggered(task.id)

        task_start = default_timer()
        self._log.debug(lambda: f"Executing measurement {task.id}")

        valid_measurements, invalid_results_count = await self._read(
            task.targets
        )

        if invalid_results_count > 0:
            self._log.error(lambda: f"Can't execute measurement {task.id}")
        else:
            await self._measurement_handler_service.on_new_data(
                valid_measurements
            )

        task_timedelta = timedelta(seconds=default_timer() - task_start)
        self._log.debug(lambda: f"Measurement {task.id} done in "
                                f"{task_timedelta}")

        self._data_logger_activity_service.report_task_results(
            task.id,
            len(valid_measurements),
            invalid_results_count,
            task_timedelta
        )

        if task.id in self._running_tasks_by_id:
            self._run_measurement_task(task)

    async def _handle_alarm(self, task: DataLoggerAlarmTask) -> None:
        wait_time = calculate_wait_time(task.period, datetime.now())
        self._log.debug(
            lambda: f"Alarm {task.id} scheduled - execution in {wait_time}"
        )
        await asyncio.sleep(wait_time.seconds)

        self._data_logger_activity_service.report_task_triggered(task.id)

        task_start = default_timer()
        self._log.debug(lambda: f"Executing alarm {task.id}")

        valid_measurements, invalid_results_count = await self._read(
            task.targets
        )

        if invalid_results_count > 0:
            self._log.error(lambda: f"Can't execute alarm {task.id}")
        else:
            await self._alarm_handler_service.on_new_data(
                valid_measurements,
                task.message,
                task.alarm_class,
                task.priority,
                task.range,
                task.type
            )

        task_timedelta = timedelta(seconds=default_timer() - task_start)
        self._log.debug(lambda: f"Alarm {task.id} done in {task_timedelta}")

        self._data_logger_activity_service.report_task_results(
            task.id,
            len(valid_measurements),
            invalid_results_count,
            task_timedelta
        )

        if task.id in self._running_tasks_by_id:
            self._run_alarm_task(task)

    async def _read(self,
                    targets: List[Tuple[int, str, Optional[int]]]
                    ) -> Tuple[List[DataLoggerMeasurement], int]:
        preparing_read_start_s = default_timer()
        self._log.debug(
            lambda: f"Preparing requests for {len(targets)} targets"
        )

        requests: List[str] = await self._cpu_intensive_task_runner.run(
            self._prepare_request_variables,
            targets,
            self._alias_service
        )

        preparing_read_timedelta = timedelta(
            seconds=default_timer() - preparing_read_start_s
        )
        self._log.debug(
            lambda: f"Requests prepared in {preparing_read_timedelta}"
        )
        self._log.debug("Reading...")

        xml = await self._scgi_client.get("&".join(requests))

        valid_measurements = []
        invalid_measurements_count = 0

        responses = RRResponsesXmlSerializer.from_xml(xml)

        for response in responses:
            if response.valid:
                valid_measurements.append(
                    DataLoggerMeasurement(
                        response.name,
                        response.tag_name,
                        response.value
                    )
                )
            else:
                invalid_measurements_count += 1
                self._log.error(
                    lambda: f"Received invalid response: {response}"
                )

        return valid_measurements, invalid_measurements_count

    def _run_measurement_task(self, task: DataLoggerMeasurementTask) -> None:
        self._run_task(task, self._handle_measurement)

    def _run_alarm_task(self, task: DataLoggerAlarmTask) -> None:
        self._run_task(task, self._handle_alarm)

    def _run_task(self,
                  task: Union[DataLoggerMeasurementTask, DataLoggerAlarmTask],
                  handler) -> None:
        t = self._loop.create_task(handler(task))
        t.add_done_callback(create_task_callback(self._log))
        self._running_tasks_by_id[task.id] = t

    @staticmethod
    def _prepare_request_variables(
        targets: List[Tuple[int, str, Optional[int]]],
        alias_service: AliasService
    ) -> List[str]:
        return [
            alias_service.to_alias_name(f"c{nad}.{variable}")
            for nad, variable in targets
        ]
