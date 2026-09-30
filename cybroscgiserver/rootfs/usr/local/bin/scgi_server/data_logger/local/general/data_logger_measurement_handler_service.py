import re
from datetime import datetime
from typing import List

from lib.general.conditional_logger import ConditionalLogger
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from data_logger.local.db.model import Measurement
from data_logger.local.db.repository import Repository
from data_logger.local.general.data_logger_measurement import \
    DataLoggerMeasurement


class DataLoggerMeasurementHandlerService:
    def __init__(self,
                 log: ConditionalLogger,
                 repository: Repository,
                 cpu_intensive_task_runner: CPUIntensiveTaskRunner):
        self._log: ConditionalLogger = log
        self._repository: Repository = repository
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )

    async def on_new_data(self,
                          measurements: List[DataLoggerMeasurement]) -> None:
        self._log.debug(lambda: f"Measurement - {len(measurements)} variables")

        data = await self._cpu_intensive_task_runner.run(
            self._map_measurements_to_domain_objects,
            measurements
        )

        await self._repository.create_measurements(data)

    @staticmethod
    def _map_measurements_to_domain_objects(
        measurements: List[DataLoggerMeasurement]
    ) -> List[Measurement]:
        return [
            Measurement(
                id=None,
                nad=m.nad,
                tag=m.variable,
                value=m.value,
                timestamp=datetime.now()
            )
            for m in measurements
        ]
