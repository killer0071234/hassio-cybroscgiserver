from dataclasses import dataclass


@dataclass
class DataLoggerMeasurement:
    nad: str
    variable: str
    value: str

    def __str__(self):
        return f"c{self.nad}.{self.variable}={self.value}"
