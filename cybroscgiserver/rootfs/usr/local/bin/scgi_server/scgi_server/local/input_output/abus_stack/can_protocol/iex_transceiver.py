from typing import Optional, List

import can

from lib.general.conditional_logger import ConditionalLogger
from scgi_server.local.input_output.abus_stack.can_protocol.can_transceiver \
    import CanTransceiver
from scgi_server.local.input_output.abus_stack.can_protocol.iex_frame import \
    IexFrame


class IexTransceiver:
    def __init__(self, log: ConditionalLogger, receiver: 'AbusTransceiver'):
        self._log: ConditionalLogger = log
        self._buffer = []
        self._receiver: 'AbusTransceiver' = receiver
        self._receiver.set_can_sender(self)
        self._sender: Optional[CanTransceiver] = None

    def set_sender(self, sender: CanTransceiver):
        self._sender = sender

    def send(self, iex_frames: List[IexFrame]) -> None:
        for frame in iex_frames:
            can_msg = IexTransceiver.iex_frame_to_can_msg(frame)
            self._sender.send(can_msg)

    def receive(self, can_msg: can.Message) -> None:
        header = can_msg.arbitration_id.to_bytes(4, byteorder='big')
        data = can_msg.data
        iex_frame = IexFrame.bytes_to_iex(header, data)

        if not (iex_frame.is_stream or iex_frame.is_strend):
            return

        if not iex_frame.is_abus:
            return

        if len(self._buffer) == 0 and not iex_frame.is_data_abus_start:
            return

        if iex_frame.is_stream:
            self.add_to_buffer(iex_frame)
        if iex_frame.is_strend:
            self.add_to_buffer(iex_frame)
            buffer = self._buffer
            self.clear_buffer()

            self._log.debug(f'Flushing input buffer containing iex frames')
            for iex_frame in buffer:
                self._log.debug(f'{iex_frame}\n')

            self._receiver.receive(buffer)

    @classmethod
    def iex_frame_to_can_msg(cls, iex_frame: IexFrame) -> can.Message:
        header, data = IexFrame.iex_to_bytes(iex_frame)

        can_msg = can.Message(
            check=True,
            arbitration_id=int.from_bytes(header, 'big'),
            data=bytearray(data),
            is_extended_id=True,
            is_error_frame=False,
            is_remote_frame=False
        )
        return can_msg

    def add_to_buffer(self, iex_frame: IexFrame) -> None:
        self._buffer.append(iex_frame)

    def clear_buffer(self) -> None:
        self._buffer = []



