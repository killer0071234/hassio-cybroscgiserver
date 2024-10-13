from asyncio import AbstractEventLoop

import can

from lib.general.conditional_logger import ConditionalLogger


class CanTransceiver(can.Listener):
    def __init__(self,
                 communication_loop: AbstractEventLoop,
                 log: ConditionalLogger,
                 receiver: 'IexTransceiver',
                 interface: str,
                 channel: str,
                 bitrate: int
                 ):
        super().__init__()
        self._communication_loop: AbstractEventLoop = communication_loop
        self._log: ConditionalLogger = log
        self._interface: str = interface
        self._channel: str = channel
        self._bitrate: int = bitrate

        self._receiver: 'IexTransceiver' = receiver
        self._receiver.set_sender(self)
        self._notifier: can.Notifier | None = None
        self._bus: can.interface.Bus | None = None

    def start(self) -> None:
        can.rc['interface'] = self._interface
        can.rc['channel'] = self._channel
        can.rc['bitrate'] = self._bitrate
        self._bus = can.interface.Bus()
        self._notifier = can.Notifier(self._bus, [self],
                                      loop=self._communication_loop)

    def send(self, can_msg: can.Message) -> None:
        try:
            s = CanTransceiver._create_can_msg_string_representation(can_msg)
            self._log.info(f'Sending: {s}')
            self._bus.send(can_msg)
        except can.CanError:
            es = CanTransceiver._create_can_msg_string_representation(can_msg)
            self._log.error(f'Sending failed: {es}')

    def on_message_received(self, can_msg: can.Message) -> None:
        s = CanTransceiver._create_can_msg_string_representation(can_msg)
        self._log.info(f'Received: {s}')
        self._receiver.receive(can_msg)

    def on_error(self, exc: Exception) -> None:
        self._log.error(f"Can error: {exc}")

    @staticmethod
    def _create_can_msg_string_representation(can_msg: can.Message) -> str:
        return f'{can_msg.arbitration_id} {can_msg.data.hex()}'
