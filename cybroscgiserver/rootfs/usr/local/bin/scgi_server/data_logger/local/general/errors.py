class DataLoggerError(Exception):
    pass


class UnexpectedValue(DataLoggerError):
    def __init__(self, value_str: str, *args):
        super().__init__(f"Unexpected value \"{value_str}\"", *args)
        self.value_str = value_str
