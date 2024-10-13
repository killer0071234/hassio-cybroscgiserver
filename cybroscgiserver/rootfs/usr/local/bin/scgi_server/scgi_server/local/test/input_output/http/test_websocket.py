import unittest

from lib.input_output.websocket.frame import WebSocketFrame


class WebsocketTestCase(unittest.TestCase):
    def test_pong(self):
        payload = "test".encode()
        frame = WebSocketFrame.pong(payload)

        self.assertEqual(frame.serialize(),
                         bytearray.fromhex("8A0474657374"))

    def test_pong_deserialize_wo_mask(self):
        data = bytearray.fromhex("8a0474657374")
        frame = WebSocketFrame.deserialize(data)

        self.assertEqual(frame.payload, "test".encode())

    def test_ping_parse(self):
        data = bytearray.fromhex("898444B6B51A30D3C66E")

        frame = WebSocketFrame.deserialize(data)

        self.assertEqual(frame.payload, "test".encode())

    def test_ping_client(self):
        frame = WebSocketFrame.ping("test", client=True)
        data = frame.serialize()

        frame2 = WebSocketFrame.deserialize(data)

        self.assertEqual(frame.payload, frame2.payload)


if __name__ == '__main__':
    unittest.main()
